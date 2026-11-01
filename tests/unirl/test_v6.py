"""Arnés v6 sin Lean ni API: plan determinista, contrabalanceo, igualación de largo, K_ig, ITT, recorte, prompts por
rama, guardia del registro, anexo obligatorio, fase 1 en seco, filtro de compilación, rechazados y vigilancia del modelo.

El Lean simulado (LakeV6) reporta un error en la LÍNEA exacta de cualquier línea que contenga «FALLA», «= 5» o
«absurd», agota el tiempo si alguna dice «LENTO», imprime las marcas de IO.println, responde `#check @n` con la
cabecera del teorema n que encuentre y `#print axioms n` con [propext].
"""

import hashlib
import json
import re

import pytest

from unirl import corpus_confirmatorio as K
from unirl import fase1 as F1
from unirl import fase2 as F2
from unirl import frontera as F
from unirl import plan_v6 as P
from unirl import prompts_v6 as PR
from unirl.tokens_api import ContadorFalso, Conteos, verificar_conteos

CTX = "namespace Juguete\n\ndef doble (n : Nat) : Nat := 2 * n"
FAMILIAS = [("pibase", "F1"), ("pibase", "F2"), ("etp", "V1"), ("etp", "V2")]
N_POR_FAMILIA = 24


def _sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


def _ids(fuente, fam):
    return [f"{fuente}:{fam}:{'imp:P000001-P000002:v' if k in (3, 7) else 't'}{k:02d}" for k in range(N_POR_FAMILIA)]


def _reg(i, k, fuente, fam):
    st = f"theorem {re.sub(r'[^A-Za-z0-9_]', '_', i)} (n : Nat) : doble (n + {k}) = 2 * n + {2 * k} := by sorry"
    return {"id": i, "fuente": fuente, "familia": fam, "verdad": "verdadero", "imports": ["Mathlib"], "dependencias": ["Mathlib"],
            "contexto_lean": CTX, "enunciado_lean": st, "sha256_tarea": _sha(CTX + "\n\n" + st)}


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch):
    monkeypatch.setattr(PR, "DORMIR", lambda s: None)


@pytest.fixture
def mundo(tmp_path):
    """Corpus sintético (4 familias × 24 tareas; dos ids por familia son «la misma implicación») + censo con un
    duplicado α-equivalente por familia (t22 y t23 comparten tipo)."""
    regs, filas = [], []
    for fuente, fam in FAMILIAS:
        for k, i in enumerate(_ids(fuente, fam)):
            regs.append(_reg(i, k, fuente, fam))
            tipo_k = 22 if k == 23 else k  # t23 duplica a t22
            filas.append({"id": i, "familia": f"{fuente} | {fam}", "ok": True, "tipo": f"x (n : Nat) : doble (n + {tipo_k}) = 2 * n + {2 * tipo_k}",
                          "error": "", "ctx_sha": "abc"})
    filas.append({"id": "pibase:F1:rota", "familia": "pibase | F1", "ok": False, "tipo": "", "error": "no elabora", "ctx_sha": "abc"})
    d = tmp_path / "aprobados" / "Corpus"
    d.mkdir(parents=True)
    txt = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in regs)
    (d / "corpus_v1.jsonl").write_text(txt, encoding="utf-8")
    (tmp_path / "aprobados" / "SHA256SUMS_corpus1").write_text(f"{_sha(txt)}  aprobados/Corpus/corpus_v1.jsonl\n", encoding="utf-8")
    censo = tmp_path / "censo"
    censo.mkdir()
    (censo / "elegibles.json").write_text(json.dumps({"sin_fundir": {f"{a} | {b}": N_POR_FAMILIA - 1 for a, b in FAMILIAS}, "fundidas": {}, "miembros": {}}))
    (censo / "referencias.jsonl").write_text("".join(json.dumps(f) + "\n" for f in filas))
    tareas = K.cargar_corpus(1, tmp_path)
    return {"raiz": tmp_path, "censo": censo, "tareas": tareas}


class LakeV6:
    timeout_s = 300.0

    def __init__(self):
        self.archivos = []

    def compilar(self, texto):
        self.archivos.append(texto)
        lineas = texto.splitlines()
        if any("LENTO" in l for l in lineas):
            return {"rc": -9, "salida": "", "s": 0.1}
        errs = [k for k, l in enumerate(lineas, 1) if "FALLA" in l or re.search(r"=\s*5\b", l) or "absurd" in l]
        if "CAMBIA_ENUNCIADO" in texto:  # un bloque que cambia el enunciado: el kernel rechaza unirl_chk (Type mismatch)
            errs += [k for k, l in enumerate(lineas, 1) if l.startswith("theorem unirl_chk_")]
        nombres = re.findall(r"^\s*theorem\s+(cu_\w+)", texto, re.M)
        dup = [n for n in set(nombres) if nombres.count(n) > 1]
        sal = [f"I.lean:{k}:2: error: unsolved goals FALLA" for k in errs]
        if dup:
            k = next(i for i, l in enumerate(lineas, 1) if re.match(rf"\s*theorem\s+{dup[0]}\b", l) and i > nombres.index(dup[0]))
            sal.append(f"I.lean:{k}:1: error: '{dup[0]}' has already been declared")
        for linea in lineas:
            if m := re.match(r'#eval IO\.println "(UNIRL_\w+)"', linea):
                sal.append(m.group(1))
            elif m := re.match(r"#check @(\S+)", linea):
                corto = m.group(1).split(".")[-1]
                cab = re.search(rf"^(?:private )?theorem {re.escape(corto)}\b([^\n]*?):=", texto, re.M)
                if cab and (texto[: cab.start()].count("\n") + 1) in errs:
                    cab = None  # el theorem no elaboró: #check no lo conoce
                if cab:
                    sal.append(f"I.lean:50:0: info: {corto} {_como_lean(cab.group(1).strip())}")
                else:
                    sal.append(f"I.lean:50:0: error: unknown identifier '{corto}'")
            elif m := re.match(r"#print axioms (\S+)", linea):
                sal.append(f"'Juguete.{m.group(1).split('.')[-1]}' depends on axioms: [propext]")
        return {"rc": 1 if (errs or dup) else 0, "salida": "\n".join(sal) + "\n", "s": 0.1}

    def version(self):
        return "Lean (version 4.34.1)"


def _como_lean(cabecera):
    """`(n : Nat) : cuerpo` → `: ∀ (n : Nat), cuerpo`, como imprime `#check @x` en Lean real (los binders van tras el `:`)."""
    prof, corte = 0, None
    for k, ch in enumerate(cabecera):
        prof += ch in "([{" ; prof -= ch in ")]}"
        if prof == 0 and cabecera.startswith(" : ", k) and corte is None:
            corte = k
    if corte is None:
        return cabecera
    binders, cuerpo = cabecera[:corte].strip(), cabecera[corte + 3:].strip()
    return f": ∀ {binders}, {cuerpo}" if binders else f": {cuerpo}"


class LakeExcl(LakeV6):
    """Como LakeV6, pero `first | exact L | simpa using L` solo cierra si el nombre de L lleva «mismo»."""

    def compilar(self, texto):
        return super().compilar("\n".join(l + (" FALLA" if "simpa using" in l and "mismo" not in l else "") for l in texto.splitlines()))


def _ent(nombre, enunciado, bloque=None, extra_teoremas=()):
    bloque = bloque or f"theorem {nombre} {enunciado} := by omega"
    teoremas = [nombre, *extra_teoremas]
    return {"nombre": nombre, "declara": teoremas, "teoremas": teoremas, "enunciados": {t: enunciado for t in teoremas}, "bloque": bloque,
            "origen": "tarea secreta, episodio secreto", "sha": _sha(bloque)}


# ============================================================================== plan y semillas


def test_plan_determinista_dedupe_tope_y_pliegues(mundo):
    censo = P.leer_censo(mundo["censo"])
    p1 = P.construir_plan(censo, mundo["tareas"])
    p2 = P.construir_plan(censo, mundo["tareas"])
    assert P.texto_plan(p1) == P.texto_plan(p2)
    assert p1["F"] == 4 and p1["semillas"] == P.SEMILLAS
    for fam, d in p1["familias"].items():
        assert d["n_distintas"] == 23 and d["n_tope"] == 23  # 24 censadas, t23 duplica a t22
        assert list(d["duplicados"].values()) == [[f"{fam.split(' | ')[0]}:{fam.split(' | ')[1]}:t23"]]
        assert set(d["pliegues"]["1"]) | set(d["pliegues"]["2"]) == set(d["tareas"]) and not set(d["pliegues"]["1"]) & set(d["pliegues"]["2"])
        assert abs(len(d["pliegues"]["1"]) - len(d["pliegues"]["2"])) <= 2  # grupos enteros; un grupo de 2
        assert d["prefijo_30"] == d["tareas"][:30]
        imp = [i for i in d["tareas"] if "imp:" in i]
        assert len(imp) == 2 and d["grupos_implicacion_fundidos"] == 1
        assert p1["tareas"][imp[0]]["pliegue"] == p1["tareas"][imp[1]]["pliegue"]
    # otra semilla de submuestra cambiaría el orden; con la registrada, la permutación es fija
    sel = p1["familias"]["pibase | F1"]["tareas"]
    assert sel != sorted(sel)
    # sin corpus: ordena por SHA del id (declarado) y lo anota
    p3 = P.construir_plan(censo, None)
    assert p3["con_sha256_tarea_del_corpus"] is False and p3["F"] == 4


def test_plan_escribe_sha_y_orden_de_fase1(mundo, tmp_path):
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    sha = P.escribir_plan(plan, tmp_path / "plan.json")
    plan2, sha2 = P.cargar_plan(tmp_path / "plan.json")
    assert sha == sha2 and plan2["F"] == 4 and (tmp_path / "plan.sha256").read_text().startswith(sha)
    fams = P.orden_familias_fase1(plan)
    assert sorted(fams) == sorted(plan["familias"]) and fams == P.orden_familias_fase1(plan2)
    o1 = P.orden_construccion(plan, fams[0], 1, 1)
    o2 = P.orden_construccion(plan, fams[0], 1, 2)
    assert sorted(o1) == sorted(o2) == sorted(plan["familias"][fams[0]]["pliegues"]["1"]) and o1 != o2


def test_contrabalanceo_y_celdas_comparten_construccion(mundo):
    for i in ("a", "b", "pibase:F1:t03"):
        c1, c2 = F1.construccion_asignada(i, 1), F1.construccion_asignada(i, 2)
        assert {c1, c2} == {1, 2} and F1.construccion_asignada(i, 3) in (1, 2)
        assert F1.construccion_asignada(i, 1) == c1  # determinista
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    anexo = _anexo_sintetico(plan)
    cs = F2.celdas(plan, anexo)
    por = {}
    for c in cs:
        if c["c"] is not None:
            por.setdefault((c["tarea"], c["semilla"]), set()).add(c["c"])
    assert all(len(v) == 1 for v in por.values())  # misma construcción en D100, P, D100-texto, R-texto, D50 de la misma (tarea, semilla)
    cuenta = {r: sum(1 for c in cs if c["rama"] == r) for r in PR.RAMAS}
    n_t = sum(1 for c in cs if c["rama"] == "D50")
    assert cuenta == {"SC": 3 * n_t, "D100": 3 * n_t, "P": 2 * n_t, "D100-texto": 3 * n_t, "R-texto": 3 * n_t, "SC_ig": 2 * n_t, "D50": n_t}


def _anexo_sintetico(plan, h4_evaluable=True, excluir=()):
    fams = sorted(plan["familias"])
    bloques = {}
    for i, t in plan["tareas"].items():
        bloques[i] = {c: {"D100": [_ent("cu_a", "(n : Nat) : n = n")], "P": [_ent("cu_p", "(n : Nat) : n + 0 = n")],
                          "R-texto": [_ent("cu_r", "(n : Nat) : n = 7")], "D50": [_ent("cu_a", "(n : Nat) : n = n")]} for c in ("1", "2")}
    return {"plan": plan, "bloques": bloques, "familias_construidas": fams,
            "exclusion": {"por_tarea": {i: {"excluida": i in excluir} for i in plan["tareas"]}, "por_familia": {f: {"sigue": True} for f in fams}},
            "h4": {"evaluable": h4_evaluable, "familias_h4": fams if h4_evaluable else []}, "plan_b": {"plan_b": False}, "modelo_api": "seco-1"}


def test_orden_de_celdas_sc_ig_fuera_del_primer_10_por_ciento(mundo):
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    cola = F2.ordenar_celdas(F2.celdas(plan, _anexo_sintetico(plan)))
    cola2 = F2.ordenar_celdas(F2.celdas(plan, _anexo_sintetico(plan)))
    assert [c["celda"] for c in cola["celdas"]] == [c["celda"] for c in cola2["celdas"]]
    n10 = cola["n10"]
    assert n10 == -(-cola["n_total"] // 10)
    assert all(c["rama"] != "SC_ig" for c in cola["celdas"][:n10]) and any(c["rama"] == "SC_ig" for c in cola["celdas"][n10:])
    assert [c["indice"] for c in cola["celdas"]] == list(range(cola["n_total"]))
    # las celdas no están agrupadas por tarea ni por rama (barajadas)
    assert len({c["rama"] for c in cola["celdas"][:30]}) > 2


# ============================================================================== prompts por rama


def test_cabecera_texto_identica_y_sc_sin_cuaderno_y_sin_origen():
    ent = [_ent("cu_a", "(n : Nat) : n = n"), _ent("cu_b", "(n : Nat) : n + 0 = n")]
    assert PR.cabecera("D100-texto", ent) == PR.cabecera("R-texto", ent)
    assert PR.cabecera("D100", ent) == PR.cabecera("P", ent) == PR.cabecera("D50", ent) == PR.cabecera("CC", ent)
    assert PR.cabecera("SC", ent) == [] and PR.cabecera("SC_ig", ent) == []
    t = K.tarea_de(_reg("pibase:F1:t00", 0, "pibase", "F1"))
    p_sc = PR.construir_prompt(t, "SC", [], [], [], 4, 3)
    p_d = PR.construir_prompt(t, "D100", ent, [], [], 4, 3)
    p_tx = PR.construir_prompt(t, "D100-texto", ent, [], [], 4, 3)
    assert PR.TITULO_CUADERNO not in p_sc and PR.TITULO_TEXTO not in p_sc and "cu_a" not in p_sc
    assert PR.TITULO_CUADERNO in p_d and "secreto" not in p_d and "unknown identifier" not in p_d
    assert PR.TITULO_TEXTO in p_tx and "unknown identifier" in p_tx and "certificad" not in p_tx.split(PR.TITULO_TEXTO)[1].split("# Presupuesto")[0]
    assert "rechaz" not in p_tx and "secreto" not in p_tx
    assert p_tx.replace(PR.TITULO_TEXTO, PR.TITULO_CUADERNO).replace(PR.INSTRUCCION_TEXTO, PR.INSTRUCCION_CUADERNO) == p_d
    # SISTEMA de test: sin «tareas futuras»; el de la fase 1 es la v5 literal
    assert "tareas futuras" not in PR.SISTEMA_TEST and PR.SISTEMA_FASE1 == K.SISTEMA and "tareas futuras" in PR.SISTEMA_FASE1
    assert PR.lineas_bloque(ent) == ["- `cu_a` : (n : Nat) : n = n", "- `cu_b` : (n : Nat) : n + 0 = n"]


def test_episodio_v6_declara_el_bloque_solo_si_es_invocable(mundo, tmp_path):
    t = K.tarea_de(mundo["tareas"]["pibase:F1:t00"])
    ent = [_ent("cu_a", "(n : Nat) : n = n")]
    for rama in ("D100", "D100-texto", "SC"):
        lake = LakeV6()
        ref = K.referencia(t, lake)
        carpeta = tmp_path / rama
        carpeta.mkdir()
        res = PR.episodio_v6(t, rama, PR.config_de(rama), PR.ProveedorSecoV6(), lake, ent if rama != "SC" else [], carpeta, f"ep-{rama}", ref)
        assert res["lemas_admitidos"] == ["cu_seco"] and not res["resuelto"] and res["llamadas_facturadas"] == res["llamadas"] == 6
        assert res["modelos_api"] == ["seco-1"] and res["tokens"]["salida"] == 6 * 300 and res["k"] == 4
        lemas_lean = [a for a in lake.archivos if "theorem cu_seco" in a]
        assert all(("theorem cu_a" in a) == (rama == "D100") for a in lemas_lean)
        assert all("tarea secreta" not in a for a in lake.archivos)


def test_k_ig_formula():
    assert PR.k_ig(1.0) == 4 and PR.k_ig(0.3) == 4 and PR.k_ig(1.6) == 6 and PR.k_ig(2.0) == 8 and PR.k_ig(5.0) == 12
    with pytest.raises(ValueError):
        PR.config_de("SC_ig")
    assert PR.config_de("SC_ig", 7).intentos == 7 and PR.config_de("SC").intentos == 4


# ============================================================================== igualación de largo


def test_igualacion_tolerancia_y_lemas_enteros(tmp_path):
    import random
    conteos = Conteos(tmp_path / "c.json", ContadorFalso())
    pool = [_ent(f"cu_{k}", "(n : Nat) : n + " + " + ".join(["1"] * (k % 5 + 1)) + " = n") for k in range(60)]
    objetivo = 200
    r = F1.igualar(pool, objetivo, conteos, random.Random("x"))
    assert objetivo * 0.95 <= r["tokens"] <= objetivo * 1.05 and r["estado"] == "ok"
    assert all(e in pool for e in r["entradas"]) and r["n"] == len(r["entradas"])  # enteros, nunca partidos
    assert sum(conteos.tokens_bloque(PR.lineas_bloque([e])) for e in r["entradas"]) == r["tokens"]
    corto = F1.igualar(pool[:2], 1000, conteos, random.Random("x"))
    assert corto["estado"] == "corto" and corto["n"] == 2
    # determinista con la misma semilla
    assert [e["nombre"] for e in F1.igualar(pool, objetivo, conteos, random.Random("x"))["entradas"]] == [e["nombre"] for e in r["entradas"]]
    # los conteos se guardan y la verificación exige el método de la API
    conteos.guardar()
    motivos = verificar_conteos(tmp_path / "c.json", PR.lineas_bloque(pool))
    assert any("count_tokens" in m for m in motivos) and not any("faltan" in m for m in motivos)
    assert verificar_conteos(tmp_path / "c.json", PR.lineas_bloque(pool), exigir_api=False) == []
    assert verificar_conteos(tmp_path / "c.json", ["- `x` : nueva"], exigir_api=False) and verificar_conteos(tmp_path / "no.json", [])


# ============================================================================== guardia del registro y fase 1 en seco


def test_guardia_del_registro(tmp_path, mundo):
    m = tmp_path / "PRERREGISTRO_REGISTRADO"
    with pytest.raises(ValueError, match="no existe"):
        F1.verificar_registro(m)
    m.write_text(json.dumps({"osf": "pendiente", "sha256_prerregistro": "0" * 64, "fecha": "2026-10-27"}))
    with pytest.raises(ValueError, match="OSF"):
        F1.verificar_registro(m)
    pre = tmp_path / "prerregistro.md"
    pre.write_text("texto congelado")
    sha = hashlib.sha256(pre.read_bytes()).hexdigest()
    m.write_text(json.dumps({"osf": "https://osf.io/abcd1", "sha256_prerregistro": "0" * 64, "fecha": "2026-10-27"}))
    with pytest.raises(ValueError, match="cambió"):
        F1.verificar_registro(m, pre)
    m.write_text(json.dumps({"osf": "10.17605/OSF.IO/ABCD1", "sha256_prerregistro": sha, "fecha": "2026-10-27"}))
    assert F1.verificar_registro(m, pre)["sha256_prerregistro"] == sha
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    with pytest.raises(ValueError, match="registro"):
        F1.construir(plan, mundo["tareas"], tmp_path / "f1", LakeV6(), PR.ProveedorSecoV6, registro=None)


def _fase1_seca(mundo, tmp_path, familias=None, tope=F1.TOPE_FASE1_USD, usd=0.001, tope_duro=False):
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    reg = {"osf": "https://osf.io/abcd1", "sha256_prerregistro": "a" * 64, "fecha": "2026-10-27"}
    salida = tmp_path / "fase1"
    prov = PR.ProveedorSecoV6(usd_por_llamada=usd, tope_usd=tope if tope_duro else None)
    estado = F1.construir(plan, mundo["tareas"], salida, LakeV6(), lambda: prov, reg, tope_usd=tope, paralelo=4, familias=familias)
    return plan, salida, estado


def test_fase1_en_seco_orden_cuadernos_y_reanudacion(mundo, tmp_path):
    fams = P.orden_familias_fase1(P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"]))[:1]
    plan, salida, estado = _fase1_seca(mundo, tmp_path, familias=fams)
    assert estado["motivo_fin"] == "completo" and estado["modelo_api"] == "seco-1"
    fam = fams[0]
    clave = plan["familias"][fam]["clave"]
    filas = F1._leer_jsonl(salida / "construcciones.jsonl")
    assert len(filas) == 2 * len(plan["familias"][fam]["tareas"])  # cada tarea está en un pliegue y se construye con c = 1 y c = 2
    for p in (1, 2):
        for c in (1, 2):
            c_id = F1.cid(clave, p, c)
            orden = [r["tarea"] for r in sorted((r for r in filas if r["cid"] == c_id), key=lambda r: r["posicion"])]
            assert orden == P.orden_construccion(plan, fam, p, c)
            assert estado["construcciones"][c_id]["completa"] and estado["construcciones"][c_id]["n_lemas"] == 1  # cu_seco una vez por cuaderno
            ent = json.loads((salida / "cuadernos" / clave / f"p{p}_c{c}" / "entradas.json").read_text())
            assert [e["nombre"] for e in ent] == ["cu_seco"]
    assert F1.familias_construidas(estado, plan) == [fam]
    # reanudar no repite nada
    n_llamadas = len(F1._leer_jsonl(salida / "llamadas.jsonl"))
    estado2 = F1.construir(plan, mundo["tareas"], salida, LakeV6(), PR.ProveedorSecoV6, {"osf": "x", "sha256_prerregistro": "a" * 64, "fecha": "f"},
                           continuar=True, familias=fams)
    assert estado2["motivo_fin"] == "completo" and len(F1._leer_jsonl(salida / "llamadas.jsonl")) == n_llamadas
    with pytest.raises(ValueError, match="ya existe"):
        F1.construir(plan, mundo["tareas"], salida, LakeV6(), PR.ProveedorSecoV6, {"osf": "x", "sha256_prerregistro": "a" * 64, "fecha": "f"})


def test_fase1_tope_deja_fuera_las_familias_sin_construir(mundo, tmp_path):
    # 0,5 USD por llamada y tope duro de 24 (como el libro): la primera familia se corta a mitad (incompleta, fuera) y las
    # demás no empiezan (fuera por tope). Ninguna llega al test.
    plan, salida, estado = _fase1_seca(mundo, tmp_path, tope=24.0, usd=0.5, tope_duro=True)
    fams = P.orden_familias_fase1(plan)
    assert estado["familias_incompletas"] == [fams[0]] and estado["familias_fuera_por_tope"] == sorted(fams[1:])
    assert "GastoExcedido" in estado["motivo_fin"] and F1.familias_construidas(estado, plan) == []
    assert estado["usd"] <= 24.0 + 0.5
    # con 0,012 estimado y tope 0,9 USD (sin tope duro): la primera familia cabe en la proyección inicial (0,012 × 46 = 0,55);
    # la segunda ya no cabe con el costo medio realizado (≈ 0,49 + 0,49) → queda fuera sin empezar, igual que las siguientes
    plan, salida, estado = _fase1_seca(mundo, tmp_path / "b", tope=0.9, usd=0.012 / 6)
    assert len(F1.familias_construidas(estado, plan)) == 1 and len(estado["familias_fuera_por_tope"]) == 3 and "tope" in estado["motivo_fin"]


def test_filtro_de_compilacion_quita_lo_que_no_compila_e_itera(mundo, tmp_path):
    t = K.tarea_de(mundo["tareas"]["pibase:F1:t00"])
    ok = [_ent("cu_a", "(n : Nat) : n = n"), _ent("cu_b", "(n : Nat) : n + 0 = n", "theorem cu_b (n : Nat) : n + 0 = n := by FALLA"),
          _ent("cu_c", "(n : Nat) : n = n")]
    lake = LakeV6()
    quedan, caidas = F1.filtrar_bloque(lake, t, ok)
    assert [e["nombre"] for e in quedan] == ["cu_a", "cu_c"] and [c["nombre"] for c in caidas] == ["cu_b"]
    assert len(lake.archivos) == 3  # una pasada con error, la recompilación limpia y la comprobación de deriva
    filtro = F1.FiltroCompilacion(lake, tmp_path / "cache.json")
    q1, _ = filtro.filtrar(t, ok)
    n = len(lake.archivos)
    q2, _ = filtro.filtrar(K.tarea_de(mundo["tareas"]["pibase:F1:t01"]), ok)  # mismo contexto → la compilación sale de la caché
    assert [e["nombre"] for e in q1] == [e["nombre"] for e in q2] == ["cu_a", "cu_c"] and len(lake.archivos) == n + 1  # solo la deriva (otro enunciado)
    q3, _ = filtro.filtrar(K.tarea_de(mundo["tareas"]["pibase:F1:t01"]), ok)  # todo en caché
    assert len(lake.archivos) == n + 1
    # C2: una entrada que cambia el enunciado (instancia/def que hace fallar unirl_chk) cae aunque compile sin error
    mala = _ent("cu_inst", "(n : Nat) : n = n", "instance cu_inst : HAdd Nat Nat Nat := ⟨fun _ b => b⟩ -- CAMBIA_ENUNCIADO")
    quedan, caidas = F1.filtrar_bloque(LakeV6(), t, [_ent("cu_a", "(n : Nat) : n = n"), mala])
    assert [e["nombre"] for e in quedan] == ["cu_a"] and caidas[0]["nombre"] == "cu_inst" and "enunciado" in caidas[0]["motivo"]
    assert F1.deriva_enunciado(LakeV6(), t, [mala]) is True and F1.deriva_enunciado(LakeV6(), t, [_ent("cu_a", "(n : Nat) : n = n")]) is False
    # con la referencia textual: un tipo impreso distinto también es deriva
    ref = K.referencia(t, LakeV6())
    assert F1.deriva_enunciado(LakeV6(), t, [_ent("cu_a", "(n : Nat) : n = n")], ref) is False
    assert F1.deriva_enunciado(LakeV6(), t, [_ent("cu_a", "(n : Nat) : n = n")], ref + " ∨ True") is True
    lento = [_ent("cu_l", "(n : Nat) : n = n", "theorem cu_l (n : Nat) : n = n := by LENTO"), _ent("cu_a", "(n : Nat) : n = n")]
    quedan, caidas = F1.filtrar_bloque(LakeV6(), t, lento)
    assert [e["nombre"] for e in quedan] == ["cu_a"] and caidas[0]["motivo"] == "timeout del filtro"


def test_rechazados_elaboran_dedupe_y_fuera_sintaxis_y_certificados(mundo, tmp_path):
    salida = tmp_path / "f1"
    salida.mkdir()
    c_id = "fam__p1_c1"
    ep = f"{c_id}#pibase:F1:t00#pos0"
    regs = [
        {"episodio": ep, "tipo": "intento", "n": 1, "reflexion": "", "lemas": [
            {"bloque": "theorem cu_x (n : Nat) : n + 1 = 1 + n := by FALLA", "resultado": {"etiqueta": "PROOF_FAILED", "motivo": "cu_x: Lean dio errores", "nombres": ["cu_x"], "errores": ["(línea 1 de tu prueba) unsolved goals"]}},
            {"bloque": "theorem cu_y (m : Nat) : m + 1 = 1 + m := by FALLA", "resultado": {"etiqueta": "PROOF_FAILED", "motivo": "cu_y: Lean dio errores", "nombres": ["cu_y"], "errores": ["(línea 1 de tu prueba) unsolved goals"]}},
            {"bloque": "theorem cu_s (n : Nat) : n = := by FALLA", "resultado": {"etiqueta": "PROOF_FAILED", "motivo": "cu_s: Lean dio errores", "nombres": ["cu_s"], "errores": ["(línea 1 de tu prueba) unexpected token ':='; expected term"]}},
            {"bloque": "theorem cu_cert (n : Nat) : doble n = 2 * n := by FALLA", "resultado": {"etiqueta": "PROOF_FAILED", "motivo": "cu_cert: Lean dio errores", "nombres": ["cu_cert"], "errores": ["x"]}},
            {"bloque": "theorem cu_f : (1 : Nat) = 1 := by sorry", "resultado": {"etiqueta": "FORBIDDEN", "motivo": "contiene «sorry»", "nombres": []}},
            {"bloque": "theorem cu_z (n : Nat) : n * 2 = 2 * n := by FALLA", "resultado": {"etiqueta": "PROOF_FAILED", "motivo": "cu_z: Lean dio errores", "nombres": ["cu_z"], "errores": ["x"]}}]},
        {"episodio": ep, "tipo": "exploracion", "evals": []}]
    (salida / "intentos.jsonl").write_text("".join(json.dumps(r) + "\n" for r in regs))
    cuadernos = {c_id: [_ent("cu_ok", "(k : Nat) : doble k = 2 * k")]}
    out = F1.rechazados(salida, LakeV6(), mundo["tareas"], cuadernos)
    r = out[c_id]
    assert r["candidatos"] == 4  # cu_f (FORBIDDEN) y cu_s (sintaxis) no entran ni como candidatos
    assert [e["nombre"] for e in r["entradas"]] == ["cu_x", "cu_z"]  # cu_y α-equivalente a cu_x; cu_s sintaxis; cu_cert α-equivalente a cu_ok
    assert r["descartados"] == {"no_elabora": 0, "alfa_duplicado": 1, "alfa_certificado": 1, "sin_dato": 0}
    assert r["entradas"][0]["enunciados"]["cu_x"] == "(n : Nat) : n + 1 = 1 + n" and r["entradas"][0]["origen"].startswith("pibase:F1:t00")
    assert PR.lineas_bloque(r["entradas"]) == ["- `cu_x` : (n : Nat) : n + 1 = 1 + n", "- `cu_z` : (n : Nat) : n * 2 = 2 * n"]


def test_compilar_copias_exclusion_y_martillo(mundo):
    t = K.tarea_de(mundo["tareas"]["pibase:F1:t00"])
    res = F1.compilar_copias(LakeV6(), t, "theorem cu_a (n : Nat) : n = n := by rfl", ["first | exact cu_a | simpa using cu_a", "first | exact FALLA | simpa using FALLA"],
                             "unirl_excl", 60, exigir_axiomas=False)
    assert res == ["cierra", "falla"]
    res = F1.compilar_copias(LakeV6(), t, "", ["rfl", "FALLA", "omega"], "unirl_mt", 60)
    assert res == ["cierra", "falla", "cierra"]
    lento = F1.compilar_copias(LakeV6(), t, "", ["LENTO"], "unirl_mt", 60)
    assert lento == ["sin_dato"]


def test_fondos_h4_plan_b_y_anexo_integro(mundo, tmp_path):
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    fams = sorted(plan["familias"])
    cuadernos, rechaz = {}, {}
    for fam in fams:
        clave = plan["familias"][fam]["clave"]
        for p in (1, 2):
            for c in (1, 2):
                c_id = F1.cid(clave, p, c)
                cuadernos[c_id] = [_ent(f"cu_{clave[:6]}_{p}{c}_{k}", f"(n : Nat) : n + {k + 10} = {k + 10} + n") for k in range(6)]
                # rechazados: en pibase sobran; en etp solo uno (no llega al 80 %)
                n_r = 8 if fam.startswith("pibase") else 1
                rechaz[c_id] = {"entradas": [_ent(f"cu_r_{p}{c}_{k}", f"(m : Nat) : m * {k + 10} = {k + 10} * m + 1") for k in range(n_r)], "descartados": {}, "candidatos": n_r}
    conteos = Conteos(tmp_path / "c.json", ContadorFalso())
    lake = LakeV6()
    filtro = F1.FiltroCompilacion(lake, None)
    fondos = F1.fondos(plan, mundo["tareas"], cuadernos, rechaz, filtro, conteos, fams)
    i = plan["familias"]["pibase | F1"]["tareas"][0]
    b = fondos["bloques"][i]["1"]
    assert b["construccion"].endswith(f"p{P.otro_pliegue(plan['tareas'][i]['pliegue'])}_c1")
    assert len(b["D100"]) == 6 and b["igualacion"]["objetivo_tokens"] == conteos.tokens_bloque(PR.lineas_bloque(b["D100"]))
    # P viene de otra fuente (etp) e iguala
    assert all("etp" in e["nombre"] or not e["nombre"].startswith("cu_pibase") for e in b["P"]) and b["igualacion"]["P"]["estado"] == "ok"
    # R-texto: rechazados de la misma construcción, igualado a D100-TEXTO con la tolerancia de §17.7 (≥ un lema): «ok»
    ig = b["igualacion"]
    assert all(e["nombre"].split("_")[1] == "r" for e in b["R-texto"]) and ig["R-texto"]["estado"] == "ok"
    assert ig["R-texto"]["tolerancia"] == ig["tolerancia_texto"] >= 0.05 * ig["objetivo_tokens_texto"]
    assert abs(ig["R-texto"]["tokens"] - ig["objetivo_tokens_texto"]) <= ig["tolerancia_texto"] and ig["R-texto"]["diferencia"] == ig["R-texto"]["tokens"] - ig["objetivo_tokens_texto"]
    assert [e["nombre"] for e in b["D100-texto"]] == [e["nombre"] for e in b["D100"]]  # aquí todos elaboran solos
    c1 = F1.construccion_asignada(i, 1)
    assert fondos["bloques"][i][str(c1)]["D50"] is not None and len(fondos["bloques"][i][str(c1)]["D50"]) == 3
    assert fondos["bloques"][i][str(3 - c1)]["D50"] is None
    # P se iguala al D100 FILTRADO de esa construcción, lemas enteros, con la tolerancia de §17.7; el total es el del bloque entero
    tk_p = conteos.tokens_bloque(PR.lineas_bloque(b["P"]))
    assert tk_p == ig["P"]["tokens"] and abs(tk_p - ig["objetivo_tokens"]) <= ig["tolerancia"] and ig["P"]["estado"] == "ok"
    h4 = F1.lista_h4(plan, cuadernos, rechaz, conteos, fams)
    assert set(h4["familias_h4"]) == {"pibase | F1", "pibase | F2"} and h4["evaluable"] is False  # < 12
    # C7: H4 se calcula sobre las familias que SIGUEN tras la exclusión
    excl_c7 = {"por_familia": {f: {"sigue": f != "pibase | F2"} for f in fams}, "por_tarea": {}}
    siguen = F1.familias_que_siguen(excl_c7, fams)
    assert siguen == ["etp | V1", "etp | V2", "pibase | F1"] and F1.lista_h4(plan, cuadernos, rechaz, conteos, siguen)["familias_h4"] == ["pibase | F1"]
    bl_d100 = {i: {c: v["D100"] for c, v in bl.items()} for i, bl in fondos["bloques"].items()}
    # con el Lean simulado todo `first | exact L | simpa using L` cierra: todas excluidas y ninguna familia sigue (< 10)
    excl_todo = F1.exclusion_previa(plan, mundo["tareas"], lake, bl_d100, fams[:1])
    assert all(v["excluida"] and len(v["cierran"]) == 12 for v in excl_todo["por_tarea"].values())
    assert excl_todo["por_familia"][fams[0]] == {"excluidas": 23, "quedan": 0, "sigue": False}
    excl = F1.exclusion_previa(plan, mundo["tareas"], LakeExcl(), bl_d100, fams)
    assert all(not v["excluida"] for v in excl["por_tarea"].values()) and all(v["sigue"] for v in excl["por_familia"].values())
    mart = F1.martillo_cuaderno(plan, mundo["tareas"], lake, bl_d100, fams[:1])
    assert all(v["cerrable"] for v in mart.values())
    pb = F1.evaluar_plan_b(plan, cuadernos, excl, h4, fams)
    assert pb["mediana_lemas"] == 6 and pb["F_tras_exclusion"] == 4 and pb["plan_b"] is True and pb["F_menor_que_12"]  # 4 < 12
    estado = {"construcciones": {}, "modelo_api": "seco-1"}
    anexo = tmp_path / "anexo"
    sha = F1.escribir_anexo(anexo, plan, estado, cuadernos, rechaz, fondos, excl, mart, h4, pb, conteos, fams)
    assert F1.verificar_anexo(anexo) == [] and (anexo / "SHA256SUMS").exists() and len(sha) == 64
    (anexo / "h4_familias.json").write_text("{}")
    assert any("no coincide" in m for m in F1.verificar_anexo(anexo))


# ============================================================================== fase 2: guardia, ITT, K_ig, modelo, recorte


def _anexo_en_disco(mundo, tmp_path, h4_evaluable=True):
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    fams = sorted(plan["familias"])
    cuadernos = {F1.cid(plan["familias"][f]["clave"], p, c): [_ent(f"cu_{k}", f"(n : Nat) : n + {k} = {k} + n") for k in range(3)]
                 for f in fams for p in (1, 2) for c in (1, 2)}
    rechaz = {c_id: {"entradas": [_ent(f"cu_r{k}", f"(m : Nat) : m * {k} = 0") for k in range(4)], "descartados": {}, "candidatos": 4} for c_id in cuadernos}
    conteos = Conteos(tmp_path / "c.json", ContadorFalso())
    lake = LakeV6()
    fondos = F1.fondos(plan, mundo["tareas"], cuadernos, rechaz, F1.FiltroCompilacion(lake, None), conteos, fams)
    bl_d100 = {i: {c: v["D100"] for c, v in bl.items()} for i, bl in fondos["bloques"].items()}
    excl = F1.exclusion_previa(plan, mundo["tareas"], LakeExcl(), bl_d100, fams)
    h4 = F1.lista_h4(plan, cuadernos, rechaz, conteos, fams)
    h4["evaluable"] = h4_evaluable  # con 4 familias nunca llega a 12: se fuerza para probar la cola con R-texto
    pb = {"plan_b": False}
    anexo = tmp_path / "anexo"
    F1.escribir_anexo(anexo, plan, {"construcciones": {}, "modelo_api": "seco-1"}, cuadernos, rechaz, fondos, excl, {}, h4, pb, conteos, fams)
    return plan, anexo


def test_fase2_no_arranca_sin_anexo_ni_registro_ni_conteos_api(mundo, tmp_path):
    assert F2.verificar_antes_de_fase2(tmp_path / "nada")
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    motivos = F2.verificar_antes_de_fase2(anexo)
    assert any("ANEXO_REGISTRADO" in m for m in motivos) and any("count_tokens" in m for m in motivos)
    with pytest.raises(ValueError, match="no arranca"):
        F2.correr(tmp_path / "f2", anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6)
    (anexo / "ANEXO_REGISTRADO").write_text(json.dumps({"url": "https://osf.io/x", "fecha": "f", "sha256_SHA256SUMS": "0" * 64}))
    assert any("no coincide" in m for m in F2.verificar_antes_de_fase2(anexo, exigir_api_conteos=False))
    sha = K._sha((anexo / "SHA256SUMS").read_text())
    (anexo / "ANEXO_REGISTRADO").write_text(json.dumps({"url": "https://osf.io/x", "fecha": "f", "sha256_SHA256SUMS": sha}))
    assert F2.verificar_antes_de_fase2(anexo, exigir_api_conteos=False) == []
    (anexo / "evaluacion_plan_b.json").write_text(json.dumps({"plan_b": True}))
    assert any("SHA256SUMS" in m for m in F2.verificar_antes_de_fase2(anexo, exigir_api_conteos=False))  # el anexo ya no es íntegro


def test_fase2_cola_itt_kig_retenida_y_reanudacion(mundo, tmp_path):
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    # fallos de proveedor en las llamadas 7..10 (los 4 intentos de la segunda celda): ninguna llamada facturada → ITT
    prov = PR.ProveedorSecoV6(fallar_en=set(range(7, 11)))
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), lambda: prov, paralelo=1, exigir_registro=False, exigir_api_conteos=False, limite=12)
    cola = json.loads((f2 / "cola.json").read_text())
    res = F1._leer_jsonl(f2 / "resultados.jsonl")
    rep = F1._leer_jsonl(f2 / "reprogramar.jsonl")
    assert len(rep) == 1 and rep[0]["celda"] == cola["celdas"][1]["celda"] and rep[0]["llamadas_facturadas"] == 0
    assert len(res) == 11 and all(r["celda"] != rep[0]["celda"] for r in res)
    assert all(r["k"] == 4 and r["rama"] == F2.partes_celda(r["celda"])[1] for r in res)
    # K_ig: aún faltan celdas del primer 10 %
    with pytest.raises(ValueError, match="faltan"):
        F2.calcular_k_ig(f2)
    # el resto de la cola en seco, hasta el primer SC_ig: se retiene sin K_ig
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=3, continuar=True, exigir_registro=False, exigir_api_conteos=False)
    assert estado["motivo_fin"].startswith("RETENIDA") and estado["K_ig"] is None
    hechas = {r["celda"] for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r}
    assert not any(F2.partes_celda(c)[1] == "SC_ig" for c in hechas)
    assert all(c["celda"] in hechas or c["celda"] == rep[0]["celda"] for c in cola["celdas"][: cola["n10"]])
    kig = F2.calcular_k_ig(f2)
    assert kig["K_ig"] == PR.k_ig(kig["r"]) and (f2 / "enmiendas" / "K_ig.json").exists() and kig["r"] > 0 and kig["n_celdas_D100"] > 0
    # con K_ig la cola termina y la celda sin llamada se reprograma UNA vez al final
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=4, continuar=True, exigir_registro=False, exigir_api_conteos=False)
    assert estado["motivo_fin"] == "completo" and estado["reprogramaciones"] == 1 and estado["K_ig"] == kig["K_ig"]
    res = {r["celda"]: r for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r}
    assert len(res) == cola["n_total"] and res[rep[0]["celda"]]["reprogramacion"] is True
    assert all(r["k"] == kig["K_ig"] for r in res.values() if r["rama"] == "SC_ig") and estado["por_rama"]["SC_ig"]["hechas"] == cola["por_rama"]["SC_ig"]
    assert estado["por_rama"]["R-texto"]["hechas"] > 0 and all(r["n_bloque"] == 0 for r in res.values() if r["rama"] in ("SC", "SC_ig"))
    # cada llamada del libro lleva la celda (aquí el seco no escribe libro; se comprueba el id del episodio en llamadas.jsonl)
    eps = {l["episodio"] for l in F1._leer_jsonl(f2 / "llamadas.jsonl")}
    assert rep[0]["celda"] + "#R" in eps


def test_fase2_interrumpida_dos_veces_cuenta_como_no_resuelta(mundo, tmp_path):
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    cola = F2.ordenar_celdas(F2.celdas(plan, F2.cargar_anexo(anexo)))
    c0 = cola["celdas"][0]
    f2.mkdir()
    (f2 / "interrumpidos.jsonl").write_text("".join(json.dumps({"celda": c0["celda"], "rama": c0["rama"]}) + "\n" for _ in range(2)))
    cola["anexo_sha256sums"] = "x"
    (f2 / "cola.json").write_text(json.dumps(cola))
    F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=1, continuar=True, exigir_registro=False, exigir_api_conteos=False, limite=2)
    res = F1._leer_jsonl(f2 / "resultados.jsonl")
    assert res[0]["celda"] == c0["celda"] and res[0]["resuelto"] is False and "dos veces" in res[0]["motivo"]


def test_fase2_cambio_de_modelo_detiene(mundo, tmp_path):
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    prov = PR.ProveedorSecoV6(cambiar_modelo_en=8)
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), lambda: prov, paralelo=1, exigir_registro=False, exigir_api_conteos=False, limite=5)
    assert "CambioDeModelo" in estado["motivo_fin"] and (f2 / "cambio_modelo.json").exists()
    assert len([r for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r]) == 1  # la celda en curso no se registra
    # al empezar, el modelo esperado es el de la fase 1 (anexo): uno distinto detiene en la primera llamada
    (anexo / "modelo_api.json").write_text(json.dumps({"modelo_api_fase1": "otro-modelo"}))
    F1.escribir_anexo  # (el anexo deja de ser íntegro; se salta la verificación con un SHA256SUMS regenerado)
    import hashlib as h
    sumas = [f"{h.sha256(f.read_bytes()).hexdigest()}  {f.name}" for f in sorted(anexo.iterdir()) if f.name != "SHA256SUMS" and f.is_file()]
    (anexo / "SHA256SUMS").write_text("\n".join(sumas) + "\n")
    estado = F2.correr(tmp_path / "f2b", anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=1, exigir_registro=False, exigir_api_conteos=False, limite=2)
    assert "CambioDeModelo" in estado["motivo_fin"] and estado["celdas_hechas"] == 0


def test_proyeccion_de_gasto_solo_lee_el_libro_y_recorta_en_orden(mundo, tmp_path):
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    cola = F2.ordenar_celdas(F2.celdas(plan, F2.cargar_anexo(anexo)))
    f2 = tmp_path / "f2"
    (f2 / "enmiendas").mkdir(parents=True)
    (f2 / "cola.json").write_text(json.dumps(cola))
    libro = tmp_path / "gasto.json"
    fase = f"confirmatorio:{F2.NOMBRE_FASE2}"
    # antes del 10 %: aún no
    (libro).write_text(json.dumps({"llamadas": [{"fase": fase, "corrida": cola["celdas"][0]["celda"], "usd": 0.01}]}))
    assert F2.proyectar_gasto(libro, f2 / "cola.json", f2 / "enmiendas")["decision"] == "aun_no"
    # 10 % de celdas a 0,03 USD cada una → proyección ≈ 0,03 × N; con tope bajo recorta en orden
    llamadas = [{"fase": fase, "corrida": c["celda"], "usd": 0.03} for c in cola["celdas"][: cola["n10"]]]
    llamadas.append({"fase": "confirmatorio:fase1", "corrida": "otra", "usd": 100.0})  # otra fase: no cuenta
    libro.write_text(json.dumps({"llamadas": llamadas}))
    n = cola["n_total"]
    out = F2.proyectar_gasto(libro, f2 / "cola.json", f2 / "enmiendas", tope_usd=0.03 * n * 2)
    assert out["decision"] == "sin_cambio" and out["pasos_vigentes"] == [] and not (f2 / "enmiendas" / "recorte.json").exists()
    assert abs(out["proyeccion"] - 0.03 * (n - cola["por_rama"]["SC_ig"]) - 0.03 * 1.5 * cola["por_rama"]["SC_ig"]) < 0.5
    # tope justo por debajo: quitar D50 basta
    sin_d50 = out["proyeccion"] - 0.03 * cola["por_rama"]["D50"]
    out = F2.proyectar_gasto(libro, f2 / "cola.json", f2 / "enmiendas", tope_usd=sin_d50 + 0.01)
    assert out["decision"] == "recortar" and out["pasos_vigentes"] == ["quitar_D50"]
    assert json.loads((f2 / "enmiendas" / "recorte.json").read_text())["pasos"] == ["quitar_D50"]
    # tope muy bajo: los cuatro pasos de §11, en orden, y nunca más que eso (a la cadena de α no se le quita ninguna rama)
    out = F2.proyectar_gasto(libro, f2 / "cola.json", f2 / "enmiendas", tope_usd=0.01)
    assert out["pasos_vigentes"] == ["quitar_D50", "P_k1", "tope_familia_30", "quitar_s3"] and out["sigue_sobre_el_tope"] is True
    hist = json.loads((f2 / "enmiendas" / "recorte.json").read_text())["historial"]
    assert [h["paso"] for h in hist] == ["quitar_D50", "P_k1", "tope_familia_30", "quitar_s3"]
    for rama in ("SC", "D100", "D100-texto", "R-texto"):  # paso 4 (B-b): se quita la semilla 3 de estas ramas y solo de estas
        assert F2.celda_recortada({"rama": rama, "semilla": 3, "en_prefijo_30": True}, out["pasos_vigentes"]) == "quitar_s3"
        assert F2.celda_recortada({"rama": rama, "semilla": 1, "en_prefijo_30": True}, out["pasos_vigentes"]) is None
    assert F2.celda_recortada({"rama": "SC_ig", "semilla": 2, "en_prefijo_30": True}, out["pasos_vigentes"]) is None
    assert F2.celda_recortada({"rama": "SC", "semilla": 1, "en_prefijo_30": True}, out["pasos_vigentes"]) is None
    assert F2.celda_recortada({"rama": "P", "semilla": 2, "en_prefijo_30": True}, out["pasos_vigentes"]) == "P_k1"
    assert F2.celda_recortada({"rama": "P", "semilla": 1, "en_prefijo_30": True}, out["pasos_vigentes"]) is None
    assert F2.celda_recortada({"rama": "SC", "semilla": 1, "en_prefijo_30": False}, out["pasos_vigentes"]) == "tope_familia_30"
    # la cola respeta los recortes: las celdas recortadas se anotan y no se corren
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=2, continuar=True, exigir_registro=False, exigir_api_conteos=False, limite=40)
    filas = F1._leer_jsonl(f2 / "resultados.jsonl")
    assert any("recortada" in r for r in filas) and all(r["rama"] != "D50" for r in filas if "resuelto" in r)


def test_proveedor_por_celda_pone_la_celda_en_la_corrida_del_libro(tmp_path):
    class Interno:
        model = "claude-haiku-5-5"
        def respuesta(self, s, u): ...
        def texto(self, r): ...
    libro = K.LibroConReservas(ruta=tmp_path / "g.json", tope_usd=10, topes_fase={})
    prov = F2.ProveedorPorCelda(Interno(), libro, fase="confirmatorio:fase2", corrida="fase2")
    assert prov.corrida == "fase2"
    prov.celda("t|D100|s1")
    assert prov.corrida == "t|D100|s1"
    prov.celda(None)
    assert prov.corrida == "fase2"


def test_anexo_b_y_flags(tmp_path):
    from unirl import confirmatorio_v6 as C
    txt = C.texto_anexo_b()
    assert PR.SISTEMA_TEST in txt and PR.INSTRUCCION_TEXTO in txt and "True" in txt and "max_tokens" in txt
    for rama in PR.RAMAS:
        assert f"rama {rama}" in txt
    assert C.main(["prompts", "--salida", str(tmp_path / "b.md")]) == 0 and (tmp_path / "b.md").exists()


def test_rejuicio_sin_salida_con_900s_sin_api(mundo, tmp_path):
    """Una celda cuyo principal fue SIN_SALIDA_LEAN se rejuzga con otro Lean (900 s) a partir de la respuesta registrada."""
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"

    class LakeSinSalida(LakeV6):
        def compilar(self, texto):
            c = super().compilar(texto)
            if "UNIRL_MARCA" in texto and "decide" in texto:  # el juicio principal: Lean «muere» sin veredicto
                return {"rc": -11, "salida": "", "s": 0.1}
            return c
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeSinSalida(), lambda: PR.ProveedorSecoV6(resolver=True), paralelo=1,
                       exigir_registro=False, exigir_api_conteos=False, limite=3)
    res = [r for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r]
    assert len(res) == 3 and all(not r["resuelto"] for r in res) and sum(r["sin_salida_lean"] for r in res) >= 1
    lake900 = LakeV6()
    lake900.timeout_s = 900.0
    out = F2.rejuzgar_sin_salida(f2, anexo, mundo["tareas"], lake900)
    assert out["rejuzgadas"] >= 1 and out["resueltas_por_rejuicio"] >= 1
    fin = {r["celda"]: r for r in F1._leer_jsonl(f2 / "resultados_finales.jsonl")}
    rej = F1._leer_jsonl(f2 / "rejuicios.jsonl")
    assert all(x["timeout_s"] == 900.0 for r in rej for x in r["rejuzgadas"] if "timeout_s" in x)
    assert any(fin[r["celda"]].get("rejuicio_900s") for r in rej if r["resuelto"])
    # una sola vez por celda
    assert F2.rejuzgar_sin_salida(f2, anexo, mundo["tareas"], lake900)["rejuzgadas"] == 0


# ============================================================================== ronda 2


def test_r2_tolerancia_17_7_y_conteo_del_bloque_entero(tmp_path):
    """B-a: tolerancia = máx(5 %, mediana de tokens por lema del bloque objetivo). C3: el largo es el del bloque entero
    como un solo mensaje, sin el armazón; la cuenta por línea (con armazón) no sesga contra los bloques de muchas líneas."""
    import random
    conteos = Conteos(tmp_path / "c.json", ContadorFalso(armazon=7))
    assert conteos.armazon() == 7 and conteos.tokens_linea("- `a` : b") == conteos.tokens("- `a` : b") - 7
    largos = [_ent(f"cu_L{k}", "(n : Nat) : n + " + " + ".join(["1"] * 20) + " = n") for k in range(3)]      # 3 lemas largos
    cortos = [_ent(f"cu_c{k}", "(n : Nat) : n + " + " + ".join(["1"] * 5) + f" = n + {k}") for k in range(40)]  # muchos cortos
    objetivo = conteos.tokens_bloque(PR.lineas_bloque(largos))
    assert objetivo == conteos.tokens("\n".join(PR.lineas_bloque(largos))) - 7  # un solo mensaje, sin armazón
    tol = F1.tolerancia_de(objetivo, largos, conteos)
    mediana = sorted(conteos.tokens_linea(l) for l in PR.lineas_bloque(largos))[1]
    assert tol == max(math_ceil(0.05 * objetivo), mediana) == mediana > 0.05 * objetivo
    r = F1.igualar(cortos, objetivo, conteos, random.Random("x"), tolerancia=tol)
    assert r["tokens"] == conteos.tokens_bloque(PR.lineas_bloque(r["entradas"])) and r["tolerancia"] == tol
    assert abs(r["diferencia"]) <= tol and r["estado"] == "ok"
    # sin corregir el armazón, 7 tokens × línea harían creer que cada lema corto cuesta ~1,6 veces más y se elegirían menos
    por_linea_crudo = sum(conteos.tokens(l) for l in PR.lineas_bloque(r["entradas"]))
    assert por_linea_crudo - r["tokens"] == 7 * len(r["entradas"]) and r["n"] >= 6
    # la ventana del ±5 % sola (igualar sin tolerancia) sería más estrecha que un lema → «corto» con el mismo fondo
    r5 = F1.igualar(cortos, objetivo, conteos, random.Random("x"))
    assert r5["tolerancia"] == 0.05 * objetivo and r5["tokens"] <= objetivo + r5["tolerancia"]
    # la verificación de conteos exige el armazón y los bloques enteros
    conteos.guardar()
    assert any("armaz" in m for m in verificar_conteos(tmp_path / "c2.json", []) ) is False  # archivo inexistente → otro motivo
    ok = verificar_conteos(tmp_path / "c.json", PR.lineas_bloque(r["entradas"]), exigir_api=False, bloques_necesarios=[PR.lineas_bloque(r["entradas"])])
    assert ok == []
    assert any("bloques enteros" in m for m in verificar_conteos(tmp_path / "c.json", [], exigir_api=False, bloques_necesarios=[["- `z` : nunca"]]))


def math_ceil(x):
    import math
    return math.ceil(x)


def test_r2_filtro_de_texto_simetrico_en_las_dos_ramas(mundo, tmp_path):
    """C4: D100-texto y R-texto pasan el MISMO filtro: cada enunciado, solo, elabora en el contexto de la tarea de test."""
    t = K.tarea_de(mundo["tareas"]["pibase:F1:t00"])
    ent = [_ent("cu_a", "(n : Nat) : n = n"), _ent("cu_dep", "(n : Nat) : cu_f n = 0 FALLA", "def cu_f (n : Nat) : Nat := 0\ntheorem cu_dep (n : Nat) : cu_f n = 0 := by rfl"),
           _ent("cu_b", "(m : Nat) : m + 0 = m")]
    ok, caidas = F1.filtrar_texto(LakeV6(), t, ent)
    assert [e["nombre"] for e in ok] == ["cu_a", "cu_b"] and caidas[0]["nombre"] == "cu_dep" and "elabora solo" in caidas[0]["motivo"]
    # en fondos: D100-texto ⊂ D100 (cu_dep sigue en D100, invocable, con su def) y R-texto filtrado igual en el contexto de test
    plan = P.construir_plan(P.leer_censo(mundo["censo"]), mundo["tareas"])
    fams = sorted(plan["familias"])
    cuadernos, rechaz = {}, {}
    for fam in fams:
        clave = plan["familias"][fam]["clave"]
        for p in (1, 2):
            for c in (1, 2):
                c_id = F1.cid(clave, p, c)
                cuadernos[c_id] = [_ent(f"cu_{clave[:5]}{p}{c}_{k}", f"(n : Nat) : n + {k + 10} = {k + 10} + n") for k in range(4)] + \
                    [_ent(f"cu_dep{clave[:5]}{p}{c}", "(n : Nat) : cu_g n = 0 FALLA", f"def cu_g{clave[:5]}{p}{c} (n : Nat) : Nat := 0\ntheorem cu_dep{clave[:5]}{p}{c} (n : Nat) : cu_g{clave[:5]}{p}{c} n = 0 := by rfl")]
                rechaz[c_id] = {"entradas": [_ent(f"cu_r{p}{c}_{k}", f"(m : Nat) : m * {k + 10} = 0 + 1") for k in range(6)] +
                                [_ent(f"cu_rdep{p}{c}", "(m : Nat) : cu_h m = 1 FALLA")], "descartados": {}, "candidatos": 7}
    conteos = Conteos(tmp_path / "c.json", ContadorFalso(armazon=3))
    fondos = F1.fondos(plan, mundo["tareas"], cuadernos, rechaz, F1.FiltroCompilacion(LakeV6(), None), conteos, fams)
    i = plan["familias"]["pibase | F1"]["tareas"][0]
    b = fondos["bloques"][i]["1"]
    assert len(b["D100"]) == 5 and len(b["D100-texto"]) == 4 and all("dep" not in e["nombre"] for e in b["D100-texto"])
    assert all("rdep" not in e["nombre"] for e in b["R-texto"]) and b["caidas"]["D100-texto"] == 1 and b["caidas"]["R-texto"] == 1
    assert b["igualacion"]["objetivo_tokens_texto"] == conteos.tokens_bloque(PR.lineas_bloque(b["D100-texto"])) < b["igualacion"]["objetivo_tokens"]
    assert fondos["caidas_por_familia"]["pibase | F1"]["D100-texto"] > 0
    # la celda de D100-texto recibe SU bloque (no el de D100), y D100 el suyo
    anexo = {"bloques": fondos["bloques"]}
    assert F2.entradas_de_celda(anexo, {"celda": "x", "tarea": i, "rama": "D100-texto", "c": 1}) == b["D100-texto"]
    assert F2.entradas_de_celda(anexo, {"celda": "x", "tarea": i, "rama": "D100", "c": 1}) == b["D100"]
    assert F2.entradas_de_celda(anexo, {"celda": "x", "tarea": i, "rama": "SC", "c": None}) == []


def test_r2_retencion_de_sc_ig_no_interrumpe_celdas_en_curso(mundo, tmp_path):
    """C1: al llegar a la primera SC_ig sin K_ig se deja de despachar; las celdas en curso terminan y no cuentan como interrumpidas."""
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), PR.ProveedorSecoV6, paralelo=4, exigir_registro=False, exigir_api_conteos=False)
    assert estado["motivo_fin"].startswith("RETENIDA") and not (f2 / "interrumpidos.jsonl").exists()
    cola = json.loads((f2 / "cola.json").read_text())
    res = [r for r in F1._leer_jsonl(f2 / "resultados.jsonl") if "resuelto" in r]
    primera_ig = next(c["indice"] for c in cola["celdas"] if c["rama"] == "SC_ig")
    assert all(r["intentos"] == 4 and r["llamadas"] >= 4 for r in res)  # ninguna a medias
    assert {r["celda"] for r in res} >= {c["celda"] for c in cola["celdas"][:primera_ig]}  # todo lo anterior a la retención, hecho
    assert not any(r["rama"] == "SC_ig" for r in res) and estado["reprogramaciones"] == 0  # la retención no es el fin de la ventana
    # las celdas despachadas justo antes de la retención también terminaron (paralelo 4): como mucho, 3 índices después de la primera SC_ig
    assert max(r["indice"] for r in res) < primera_ig + 4


def test_r2_proyeccion_automatica_en_n10_y_tope_duro(mundo, tmp_path):
    """C6: la proyección se corre sola, una vez, al completarse n10; recorta si hace falta. B-b: el tope duro detiene y
    se cuentan las celdas perdidas por rama."""
    plan, anexo = _anexo_en_disco(mundo, tmp_path)
    f2 = tmp_path / "f2"
    libro = K.Libro(ruta=tmp_path / "gasto.json", tope_usd=1e9, topes_fase={})
    # el libro cobra con los precios reales de Haiku (≈ 0,0013 USD por celda; ≈ 2,2 USD las 1 564 celdas): con tope 1,5 USD
    # la proyección en n10 debe recortar
    prov = PR.ProveedorSecoV6(usd_por_llamada=0.006, libro=libro, fase=f"confirmatorio:{F2.NOMBRE_FASE2}")
    cola = F2.ordenar_celdas(F2.celdas(plan, F2.cargar_anexo(anexo)))
    estado = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), lambda: prov, paralelo=2, exigir_registro=False, exigir_api_conteos=False,
                       limite=cola["n10"] + 25, libro_ruta=tmp_path / "gasto.json", tope_usd=1.5)
    assert estado["proyeccion_n10_hecha"] is True
    py = json.loads((f2 / "enmiendas" / "proyeccion_n10.json").read_text())
    assert py["automatica"] is True and py["decision"] == "recortar" and py["celdas_con_llamada"] >= cola["n10"]
    assert py["pasos_vigentes"][:1] == ["quitar_D50"] and estado["pasos_recorte"] == py["pasos_vigentes"]
    # la proyección leyó el libro real: cada llamada lleva su celda en `corrida`
    entradas = json.loads((tmp_path / "gasto.json").read_text())["llamadas"]
    assert all("|" in e["corrida"] for e in entradas) and len({e["corrida"] for e in entradas}) >= cola["n10"]
    # las celdas posteriores respetan el recorte y la proyección no se repite al continuar
    filas = F1._leer_jsonl(f2 / "resultados.jsonl")
    assert any("recortada" in r for r in filas)
    mt = (f2 / "enmiendas" / "proyeccion_n10.json").stat().st_mtime_ns
    estado2 = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), lambda: prov, paralelo=2, continuar=True, exigir_registro=False,
                        exigir_api_conteos=False, limite=5, libro_ruta=tmp_path / "gasto.json", tope_usd=1.5)
    assert (f2 / "enmiendas" / "proyeccion_n10.json").stat().st_mtime_ns == mt and estado2["proyeccion_n10_hecha"] is True
    # B-b: tope duro simulado → GastoExcedido detiene; estado cuenta las celdas perdidas por rama (planificadas, no recortadas, sin resultado)
    F2.calcular_k_ig(f2)  # ya pasó el primer 10 %: K_ig fijado para que la cola no se retenga
    prov2 = PR.ProveedorSecoV6(usd_por_llamada=0.006, tope_usd=0.05)
    estado3 = F2.correr(f2, anexo, mundo["tareas"], LakeV6(), lambda: prov2, paralelo=2, continuar=True, exigir_registro=False,
                        exigir_api_conteos=False, libro_ruta=tmp_path / "gasto.json", tope_usd=1.5)
    assert "GastoExcedido" in estado3["motivo_fin"] and estado3["celdas_perdidas"] > 0
    assert estado3["celdas_perdidas_por_rama"]["D50"] == 0  # D50 está recortada, no perdida
    assert sum(estado3["celdas_perdidas_por_rama"].values()) == estado3["celdas_perdidas"]


def _fase2_sintetica(mundo, tmp_path, efecto_d100=0.15, semilla=1, F=4):
    """Resultados de fase 2 sintéticos: p_SC por tarea ~ U(0,1), D100 y D100-texto con +efecto, R-texto sin él."""
    import random
    plan, anexo_dir = _anexo_en_disco(mundo, tmp_path)
    a = F2.cargar_anexo(anexo_dir)
    cola = F2.ordenar_celdas(F2.celdas(plan, a))
    rng = random.Random(semilla)
    p_sc = {i: rng.uniform(0.1, 0.8) for i in plan["tareas"]}
    filas = []
    for c in cola["celdas"]:
        p = p_sc[c["tarea"]] + (efecto_d100 if c["rama"] in ("D100", "D100-texto", "D50") else 0.0)
        filas.append({**c, "resuelto": rng.random() < p, "intentos": 4, "k": 4})
    f2 = tmp_path / "f2s"
    f2.mkdir()
    (f2 / "cola.json").write_text(json.dumps(cola))
    (f2 / "resultados.jsonl").write_text("".join(json.dumps(r) + "\n" for r in filas))
    return f2, anexo_dir, plan


def test_r2_analisis_estadistico_y_grafo(mundo, tmp_path):
    """C5: θ̂, t, p exhaustiva, IC, grafo con dirección y orden (B-c), TOST y sensibilidades sobre datos sintéticos."""
    from unirl import analisis_v6 as A
    import itertools
    import numpy as np
    # p_exhaustiva coincide con la fuerza bruta (F = 5)
    S, m = np.array([3.0, -1.0, 2.5, 0.5, -2.0]), np.array([10.0, 8.0, 12.0, 9.0, 11.0])
    _, _, t0 = A.t_studentizado(S, m)
    bruto = sum(abs(A.t_studentizado(np.array(sg) * S, m)[2]) >= abs(t0) - 1e-12 for sg in itertools.product((1, -1), repeat=5)) / 32
    assert abs(A.p_exhaustiva(S, m) - bruto) < 1e-12
    # grafo: consecuencias de §8.1
    g = A.grafo([0.001, 0.02, 0.5, 0.01, 0.5], [True] * 5, True)
    assert g["rechazadas"] == {"H1": True, "H2": True, "H3": False, "H4": True, "H5": False} and [o["hipotesis"] for o in g["orden"]] == ["H1", "H4", "H2"]
    assert abs(g["alfa_local"]["H2"] - 0.05) < 1e-12 and abs(g["alfa_local"]["H4"] - 0.0375) < 1e-12
    # B-c: el orden lo fija p/w; un rechazo en contra se registra y su peso se pierde
    g1 = A.grafo([0.0005, 0.02, 0.5, 0.001, 0.5], [False, True, True, True, True], True)   # H1 primero (en contra): H4 → H2 recibe 0,025
    assert [o["hipotesis"] for o in g1["orden"]] == ["H1", "H4", "H2"] and g1["rechazo_en_contra"]["H1"] and not g1["orden"][0]["propaga"]
    g2 = A.grafo([0.002, 0.02, 0.5, 0.001, 0.5], [False, True, True, True, True], True)    # H4 primero: H1 a 0,05, cae en contra, H2 sin α
    assert [o["hipotesis"] for o in g2["orden"]] == ["H4", "H1"] and not g2["rechazadas"]["H2"] and abs(g2["alfa_local"]["H1"] - 0.05) < 1e-12
    gh = A.grafo([0.03, 0.5, 0.5, 0.5, 0.5], [True] * 5, False)                            # H4 no evaluable: H1 a 0,05
    assert gh["rechazadas"]["H1"] and abs(gh["alfa_local"]["H1"] - 0.05) < 1e-12 and gh["no_alcanzadas"] == ["H3", "H5"]
    # datos sintéticos con efecto: H1 y H5-nulo; H4 con efecto (D100-texto > R-texto)
    f2, anexo_dir, plan = _fase2_sintetica(mundo, tmp_path, efecto_d100=0.2)
    (f2 / "enmiendas").mkdir()
    (f2 / "enmiendas" / "recorte.json").write_text(json.dumps({"pasos": ["quitar_D50"]}))
    d = A.cargar(f2, anexo_dir)
    res = A.analizar(d)
    h1 = res["primario"]["H1"]
    assert h1["A"] == "D100" and h1["B"] == "SC" and h1["F"] == 4 and h1["n_tareas"] == len(plan["tareas"]) and h1["theta"] > 0.1
    assert h1["ic95"][0] < h1["theta"] < h1["ic95"][1] and 0 <= h1["p"] <= 1 and h1["se"] > 0
    assert res["primario"]["H4"]["F"] == 4 and res["primario"]["H5"]["theta"] is not None
    assert set(res["grafo"]["rechazadas"]) == set(A.HIP) and set(res["sensibilidades"]) >= {"ponderada_por_familia", "etp_un_cluster", "sin_estrato_martillo_cuaderno", "sin_familias_entrenamiento_ge_085"}
    assert res["sensibilidades"]["etp_un_cluster"]["H1"]["F"] == 3 and res["sensibilidades"]["ponderada_por_familia"]["H1"]["F"] == 4
    assert res["celdas_apartadas_por_recorte"] == {} and res["secundarios"]["P-SC"]["n_tareas"] > 0
    for H, t in res["tost"].items():
        assert not res["grafo"]["rechazadas"][H] and "equivalente" in t
    # tope duro / recorte 3 y 4: las celdas ya corridas fuera del prefijo o de la semilla 3 se apartan; faltantes → semillas completadas
    (f2 / "enmiendas" / "recorte.json").write_text(json.dumps({"pasos": ["quitar_D50", "P_k1", "tope_familia_30", "quitar_s3"]}))
    filas = F1._leer_jsonl(f2 / "resultados.jsonl")
    (f2 / "resultados.jsonl").write_text("".join(json.dumps(r) + "\n" for r in filas[: len(filas) // 2]))  # la mitad quedó sin correr
    d2 = A.cargar(f2, anexo_dir)
    r2 = A.analizar(d2)
    assert r2["celdas_apartadas_por_recorte"]["quitar_s3"] > 0 and sum(r2["celdas_perdidas_por_rama"].values()) > 0
    assert r2["primario"]["H1"]["n_tareas"] < h1["n_tareas"] and r2["primario"]["H1"]["n_tareas"] > 0
    assert all(n in (1, 2) for (_, rama), (_, n) in A.tasas(A.celdas_primarias(d2)[0]).items() if rama == "D100")  # sin semilla 3
    aud = A.muestra_auditoria(d)
    assert all(len(v) <= 20 for v in aud["por_rama"].values()) and aud["semilla"] == 20261034 and len(aud["ciega"]) == sum(len(v) for v in aud["por_rama"].values())
    assert A.main(["--fase2", str(f2), "--anexo", str(anexo_dir), "--salida", str(tmp_path / "an.json")]) == 0 and (tmp_path / "an.md").exists()
