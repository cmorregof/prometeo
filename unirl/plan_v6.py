"""Población, submuestra y partición en pliegues del confirmatorio (prerregistro v2, §2.2 punto 7, §2.3, §3.1, Anexo A).

Todo es determinista y sin API: sale del censo de elegibilidad (`censo_elegibilidad_v5/`: `elegibles.json` y
`referencias.jsonl`, con el SHA de ambos en el plan) y, si se le da el corpus, del `sha256_tarea` de cada tarea.

  1. Familias elegibles: las claves de `elegibles.json["sin_fundir"]` (las seis V1–V6 del ETP son familias separadas,
     §2.2 punto 6). Las tareas de cada familia son las filas `ok` de `referencias.jsonl` con esa familia.
  2. Casi-duplicados (§2.2 punto 5): clave = (tipo normalizado, SHA del contexto sin comentarios), con el MISMO
     `normalizar` del censo. Se deja un representante por grupo: el de menor id (orden lexicográfico). Los demás
     quedan anotados como duplicados y fuera de la población.
  3. Tope de 40 (§2.2 punto 7): las tareas distintas se ordenan por su SHA-256 (sha256_tarea del corpus; si no hay
     corpus, el SHA-256 del id), se barajan con Random(20261026) y se toman las primeras 40. Las primeras 30 de esa
     permutación son el prefijo del recorte de §11.
  4. Pliegues (§3.1): los grupos (representantes; los que son «variantes de una misma implicación» —ids con el mismo
     `imp:Pa-Pb` en la misma familia— se funden en un grupo) se ordenan por el menor SHA de sus miembros, se barajan
     con Random(20261027) y cada grupo va al pliegue con menos tareas; en empate, al pliegue 1.

`escribir_plan` deja plan.json y devuelve su SHA-256. Nada de esto llama a Lean ni a la API.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path

SEMILLAS = {
    "submuestra": 20261026,          # submuestra por familia (tope 40, prefijo 30)
    "pliegues": 20261027,            # partición en pliegues
    "celdas": 20261028,              # orden de las celdas de test y de SC_ig
    "fondo_igualacion": 20261029,    # fondo de P e igualación de largo (también R-texto)
    "construccion_asignada": 20261030,  # construcción asignada por (tarea, semilla)
    "orden_construccion": 20261031,  # + c: orden de las tareas en la construcción c
    "d50": 20261032,                 # submuestra del 50 %
    "orden_familias": 20261033,      # orden de las familias en la fase 1
    "auditoria": 20261034,           # muestra de la auditoría a mano
}
TOPE_FAMILIA = 40
PREFIJO_RECORTE = 30
MIN_FAMILIA = 20
MIN_TRAS_EXCLUSION = 10
MIN_F = 12
VERSION_PLAN = "v6"
_IMP = re.compile(r"\bimp:(P\d+)-(P\d+)")


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def normalizar(tipo: str) -> str:
    """Copia literal de `normalizar` de censo_elegibilidad.py (la clave de casi-duplicados del censo)."""
    t = tipo.split(" : ", 1)[1] if " : " in tipo else tipo
    t = re.sub(r"\s+", " ", t).strip()
    ligadas = []
    for m in re.finditer(r"(?:[∀∃λ]|fun|\()\s*\{?\(?([^\s:(){}\[\],]+(?:\s+[^\s:(){}\[\],]+)*)\s*:", t):
        for v in m.group(1).split():
            if v not in ligadas and re.fullmatch(r"[A-Za-zα-ωΑ-Ω_][\w'₀-₉]*", v):
                ligadas.append(v)
    for k, v in enumerate(ligadas):
        t = re.sub(rf"(?<![\w.']){re.escape(v)}(?![\w'])", f"⟦{k}⟧", t)
    return t


def clave_duplicado(fila: dict) -> str:
    return normalizar(fila["tipo"]) + "\x00" + str(fila.get("ctx_sha", ""))


def grupo_implicacion(tarea_id: str) -> str | None:
    """`imp:Pa-Pb` del id, si lo tiene: las variantes de una misma implicación van al mismo pliegue (§3.1)."""
    m = _IMP.search(tarea_id)
    return f"imp:{m.group(1)}-{m.group(2)}" if m else None


def leer_censo(carpeta: Path) -> dict:
    """elegibles.json (familias elegibles) y referencias.jsonl (una fila por tarea censada; la última de un id gana)."""
    carpeta = Path(carpeta)
    eleg_txt = (carpeta / "elegibles.json").read_text(encoding="utf-8")
    refs_txt = (carpeta / "referencias.jsonl").read_text(encoding="utf-8")
    eleg = json.loads(eleg_txt)
    filas: dict[str, dict] = {}
    for l in refs_txt.splitlines():
        if l.strip():
            f = json.loads(l)
            filas[f["id"]] = f
    return {"elegibles": eleg, "filas": filas, "sha_elegibles": _sha(eleg_txt), "sha_referencias": _sha(refs_txt)}


def _partir(fuente_familia: str) -> tuple[str, str]:
    a, _, b = fuente_familia.partition(" | ")
    return a.strip(), b.strip()


def clave_carpeta(fuente: str, familia: str) -> str:
    """Igual que corpus_confirmatorio.clave_familia, sin importar ese módulo: nombre de carpeta legible y único."""
    legible = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{fuente}__{familia}")[:60]
    return legible + "_" + hashlib.sha256((fuente + "\x00" + familia).encode()).hexdigest()[:8]


def construir_plan(censo: dict, corpus: dict[str, dict] | None = None, excluir: set[str] | None = None) -> dict:
    """El plan entero. `corpus` (id → registro) da el sha256_tarea; `excluir` son ids que no pueden ser de test (se
    anotan; el prerregistro no prevé ninguno, ver REVISION_V6.md)."""
    excluir = set(excluir or ())
    elegibles = censo["elegibles"]["sin_fundir"]
    por_fam: dict[str, list[dict]] = defaultdict(list)
    for f in censo["filas"].values():
        if f.get("ok") and f["familia"] in elegibles:
            por_fam[f["familia"]].append(f)
    familias, tareas, avisos = {}, {}, []
    for fam in sorted(elegibles):
        filas = sorted(por_fam.get(fam, []), key=lambda f: f["id"])
        fuente, familia = _partir(fam)
        grupos: dict[str, list[str]] = defaultdict(list)
        for f in filas:
            grupos[clave_duplicado(f)].append(f["id"])
        representantes = {min(ids): sorted(ids) for ids in grupos.values()}  # representante = menor id
        if len(representantes) != elegibles[fam]:
            avisos.append(f"{fam}: el censo cuenta {elegibles[fam]} tipos distintos y aquí salen {len(representantes)}")
        if len(representantes) < MIN_FAMILIA:
            avisos.append(f"{fam}: menos de {MIN_FAMILIA} tareas distintas ({len(representantes)}): fuera")
            continue

        def sha_de(i: str) -> str:
            r = (corpus or {}).get(i)
            return r["sha256_tarea"] if r and r.get("sha256_tarea") else _sha(i)
        distintas = sorted(representantes, key=sha_de)
        random.Random(SEMILLAS["submuestra"]).shuffle(distintas)
        seleccion = distintas[:TOPE_FAMILIA]
        prefijo = seleccion[:PREFIJO_RECORTE]
        # grupos para los pliegues: cada representante es un grupo; se funden los de la misma implicación
        imp_grupos: dict[str, list[str]] = defaultdict(list)
        sueltos = []
        for i in seleccion:
            g = grupo_implicacion(i)
            (imp_grupos[g] if g else sueltos).append(i)
        grupos_pliegue = [sorted(v) for v in imp_grupos.values()] + [[i] for i in sueltos]
        grupos_pliegue.sort(key=lambda g: min(sha_de(i) for i in g))
        random.Random(SEMILLAS["pliegues"]).shuffle(grupos_pliegue)
        pliegues: dict[int, list[str]] = {1: [], 2: []}
        for g in grupos_pliegue:
            destino = 1 if len(pliegues[1]) <= len(pliegues[2]) else 2  # menos tareas; en empate, el 1
            pliegues[destino] += g
        fundidos = sum(1 for g in grupos_pliegue if len(g) > 1)
        clave = clave_carpeta(fuente, familia)
        familias[fam] = {"fuente": fuente, "familia": familia, "clave": clave, "n_censadas": len(filas),
                         "n_distintas": len(representantes), "n_tope": len(seleccion), "tareas": seleccion,
                         "prefijo_30": prefijo, "pliegues": {"1": sorted(pliegues[1]), "2": sorted(pliegues[2])},
                         "grupos_pliegue": grupos_pliegue, "grupos_implicacion_fundidos": fundidos,
                         "duplicados": {r: [x for x in ids if x != r] for r, ids in representantes.items() if len(ids) > 1},
                         "fuera_del_tope": sorted(distintas[TOPE_FAMILIA:]),
                         "en_exclusion_externa": sorted(i for i in seleccion if i in excluir)}
        for i in seleccion:
            tareas[i] = {"familia": fam, "clave": clave, "fuente": fuente, "pliegue": 1 if i in pliegues[1] else 2,
                         "en_prefijo_30": i in prefijo, "sha256_tarea": sha_de(i), "ctx_sha": censo["filas"][i].get("ctx_sha", ""),
                         "tipo": censo["filas"][i]["tipo"]}
    return {"version": VERSION_PLAN, "semillas": SEMILLAS, "tope_familia": TOPE_FAMILIA, "prefijo_recorte": PREFIJO_RECORTE,
            "censo": {"sha_elegibles": censo["sha_elegibles"], "sha_referencias": censo["sha_referencias"]},
            "con_sha256_tarea_del_corpus": corpus is not None, "F": len(familias), "n_tareas": len(tareas),
            "familias": familias, "tareas": tareas, "avisos": avisos}


def texto_plan(plan: dict) -> str:
    return json.dumps(plan, ensure_ascii=False, indent=1, sort_keys=True)


def escribir_plan(plan: dict, ruta: Path) -> str:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    txt = texto_plan(plan)
    ruta.write_text(txt, encoding="utf-8")
    sha = _sha(txt)
    ruta.with_suffix(".sha256").write_text(f"{sha}  {ruta.name}\n", encoding="utf-8")
    return sha


def cargar_plan(ruta: Path) -> tuple[dict, str]:
    txt = Path(ruta).read_text(encoding="utf-8")
    return json.loads(txt), _sha(txt)


def otro_pliegue(p: int) -> int:
    return 2 if int(p) == 1 else 1


def orden_familias_fase1(plan: dict) -> list[str]:
    fams = sorted(plan["familias"])
    random.Random(SEMILLAS["orden_familias"]).shuffle(fams)
    return fams


def orden_construccion(plan: dict, fam: str, pliegue: int, c: int) -> list[str]:
    ids = sorted(plan["familias"][fam]["pliegues"][str(pliegue)])
    random.Random(SEMILLAS["orden_construccion"] + int(c)).shuffle(ids)
    return ids
