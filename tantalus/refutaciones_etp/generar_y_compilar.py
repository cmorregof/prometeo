"""Pasos 3 a 5 del encargo: genera lean/ETP_<id>.lean, los compila contra el entorno fijado y registra.

Entorno: Lean 4.34.1 + Mathlib v4.34.1 de corpus_compilar/corpus_lean, con la misma cabecera del corpus.
Solo `decide` sobre el magma finito; primero el `decide` normal y, si no alcanza, `decide +kernel` (también lo chequea
el kernel y no añade axiomas). Nunca native_decide. No toca el corpus ni ningún juez.

Uso:
  python3 generar_y_compilar.py generar
  python3 generar_y_compilar.py compilar [-j 1] [--solo 265_3347,29_2279] [--limite 900]
  python3 generar_y_compilar.py registrar     # escribe resumen.csv y SHA256SUMS; no compila
"""
import argparse, concurrent.futures as cf, csv, hashlib, json, os, re, subprocess, threading, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parent.parent / "corpus_compilar" / "corpus_lean"
LEAN_DIR = AQUI / "lean"
RES = AQUI / "resultados_compilacion.jsonl"
PERMITIDOS = {"propext", "Classical.choice", "Quot.sound"}
# Igual que corpus_compilar/compilar_v2.py: `lake env lean` no aplica leanOptions del lakefile.
CABECERA = "import Mathlib\nset_option relaxedAutoImplicit false\nset_option maxSynthPendingDepth 3\n\n"
PROHIBIDO = re.compile(r"native_decide|\bsorry\b|\badmit\b|\baxiom\b|implemented_by|ofReduceBool|unsafe")


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def leer(nombre):
    return [json.loads(l) for l in (AQUI / nombre).read_text(encoding="utf-8").splitlines() if l.strip()]


def texto_lean(t, cm, tactica):
    n, T = cm["n"], cm["tabla"]
    cid = t["id_corto"]
    casos = "\n".join(f"  | {i}, {j} => ⟨{T[i][j]}, by decide⟩" for i in range(n) for j in range(n))
    return (
        f"{CABECERA}{t['contexto_lean'].rstrip()}\n\n"
        f"set_option maxHeartbeats 40000000\nset_option maxRecDepth 200000\n\n"
        f"/-- Contramodelo de {t['id']}: tabla de operación sobre `Fin {n}`. -/\n"
        f"def tabla_{cid} : Fin {n} → Fin {n} → Fin {n} := fun a b =>\n"
        f"  match a.val, b.val with\n{casos}\n  | _, _ => ⟨0, by decide⟩\n\n"
        f"instance magma_{cid} : Magma (Fin {n}) := ⟨tabla_{cid}⟩\n\n"
        f"theorem cumple_A_{cid} : LeyA (Fin {n}) := by\n  unfold LeyA\n  {tactica}\n\n"
        f"theorem no_cumple_B_{cid} : ¬ LeyB (Fin {n}) := by\n  unfold LeyB\n  {tactica}\n\n"
        f"theorem refuta_{cid} : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=\n"
        f"  fun h => no_cumple_B_{cid} (h (Fin {n}) cumple_A_{cid})\n\n"
        f"#print axioms refuta_{cid}\n"
    )


def ruta_de(t):
    return LEAN_DIR / f"ETP_{t['id_corto']}.lean"


def generar():
    LEAN_DIR.mkdir(exist_ok=True)
    cms = {c["id"]: c for c in leer("contramodelos.jsonl")}
    k = 0
    for t in leer("tareas_etp.jsonl"):
        cm = cms[t["id"]]
        if cm["estado"] != "ok":
            continue
        ruta_de(t).write_text(texto_lean(t, cm, "decide"), encoding="utf-8")
        k += 1
    print("archivos generados:", k)


class Lean:
    def __init__(self):
        r = subprocess.run(["lake", "env", "env"], cwd=PROYECTO, capture_output=True, text=True, check=True)
        self.env = dict(l.split("=", 1) for l in r.stdout.splitlines() if "=" in l)
        v = subprocess.run(["lean", "--version"], cwd=PROYECTO, env=self.env, capture_output=True, text=True).stdout
        print(v.strip(), flush=True)
        if "4.34.1" not in v:
            raise SystemExit("Toolchain distinto de 4.34.1; me detengo.")

    def correr(self, ruta, limite):
        t0 = time.time()
        try:
            r = subprocess.run(["lean", "--json", "-j", "1", str(ruta)], cwd=PROYECTO, env=self.env,
                               capture_output=True, text=True, timeout=limite)
        except subprocess.TimeoutExpired:
            return None, 1, time.time() - t0
        msgs = []
        for ln in r.stdout.splitlines():
            if ln.startswith("{"):
                j = json.loads(ln)
                msgs.append({"sev": j.get("severity"), "texto": j.get("data") or ""})
        if r.returncode not in (0, 1) or r.stderr.strip():
            msgs.append({"sev": "error", "texto": f"rc={r.returncode} {r.stderr[:300]}"})
        return msgs, r.returncode, time.time() - t0


def axiomas(msgs, nombre):
    for m in msgs:
        tx = m["texto"].replace("\n", " ")
        if f"'{nombre}'" in tx:
            if "does not depend on any axioms" in tx:
                return []
            mm = re.search(r"depends on axioms: \[([^\]]*)\]", tx)
            if mm:
                return [a.strip() for a in mm.group(1).split(",") if a.strip()]
    return None


def compilar(j, solo, limite):
    lean = Lean()
    cms = {c["id"]: c for c in leer("contramodelos.jsonl")}
    tareas = [t for t in leer("tareas_etp.jsonl") if cms[t["id"]]["estado"] == "ok"]
    if solo:
        tareas = [t for t in tareas if t["id_corto"] in solo]
    hechos = {r["id"] for r in leer(RES.name) if r["compilo"]} if RES.exists() else set()
    cola = sorted((t for t in tareas if t["id"] not in hechos), key=lambda t: cms[t["id"]]["n"])
    print(f"por compilar: {len(cola)} (ya compiladas: {len(hechos)})", flush=True)
    lock = threading.Lock()

    def una(t):
        cm, cid, ruta = cms[t["id"]], t["id_corto"], ruta_de(t)
        res = None
        for tactica in ("decide", "decide +kernel"):
            ruta.write_text(texto_lean(t, cm, tactica), encoding="utf-8")
            msgs, rc, seg = lean.correr(ruta, limite)
            if msgs is None:
                res = {"compilo": False, "motivo": f"tiempo agotado con `{tactica}` ({limite} s)", "s": round(seg, 1)}
                continue
            errores = [m["texto"][:400] for m in msgs if m["sev"] == "error"]
            ax = axiomas(msgs, f"refuta_{cid}")
            if not errores and rc == 0 and ax is not None and not set(ax) - PERMITIDOS:
                res = {"compilo": True, "axiomas": ax, "s": round(seg, 1), "tactica": tactica}
                break
            res = {"compilo": False, "motivo": (errores[:1] or [f"axiomas {ax}"])[0], "axiomas": ax, "s": round(seg, 1)}
        return {"id": t["id"], "id_corto": cid, "familia": t["familia"], "n": cm["n"], **res}

    with cf.ThreadPoolExecutor(j) as ex:
        for k, r in enumerate(ex.map(una, cola), 1):
            with lock, open(RES, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(cola)}] {r['id']} n={r['n']}: {'ok' if r['compilo'] else 'FALLA ' + r['motivo'][:200]}"
                  f" {r.get('tactica', '')} {r['s']} s", flush=True)
    registrar()


def registrar():
    tareas = leer("tareas_etp.jsonl")
    cms = {c["id"]: c for c in leer("contramodelos.jsonl")}
    res = {}
    if RES.exists():
        for r in leer(RES.name):  # el último intento manda
            res[r["id"]] = r
    filas, sumas = [], []
    f5 = AQUI / "infinitos" / "resultados_f5.jsonl"
    res_f5 = {r["id"]: r for r in leer("infinitos/resultados_f5.jsonl")} if f5.exists() else {}
    for t in tareas:
        if t["id"] in res_f5:  # F5: modelo infinito portado del ETP, en infinitos/lean_f5/
            r = res_f5[t["id"]]
            txt = (AQUI / "infinitos" / "lean_f5" / f"ETP_{t['id_corto']}.lean").read_text(encoding="utf-8")
            sumas.append(f"{sha(txt)}  infinitos/lean_f5/ETP_{t['id_corto']}.lean")
            filas.append({"id": t["id"], "familia": t["familia"], "n_contramodelo": "infinito",
                          "compilo": "sí" if r["compilo"] else "no", "axiomas": " ".join(r["axiomas"] or []),
                          "tactica": "modelo infinito del ETP, portado", "segundos": r["s"],
                          "sha256_enunciado_falso": t["sha256_enunciado_falso"], "sha256_lean": sha(txt),
                          "motivo_si_no": "" if r["compilo"] else r["motivo"]})
            continue
        cm, r, ruta = cms[t["id"]], res.get(t["id"]), ruta_de(t)
        txt = ruta.read_text(encoding="utf-8") if ruta.exists() else None
        limpio = None
        if txt is not None:
            sin_print = txt.replace(f"#print axioms refuta_{t['id_corto']}", "")
            limpio = not PROHIBIDO.search(sin_print)
            sumas.append(f"{sha(txt)}  lean/{ruta.name}")
        compilo = bool(r and r["compilo"] and limpio)
        motivo = "" if compilo else (r["motivo"] if r and not r["compilo"] else
                                     "sin contramodelo finito (par de Austin: A ⇒ B en todo magma finito)"
                                     if t["familia"].startswith("F5") else "sin compilar")
        filas.append({"id": t["id"], "familia": t["familia"], "n_contramodelo": cm.get("n", ""),
                      "compilo": "sí" if compilo else "no",
                      "axiomas": (" ".join(r["axiomas"]) or "ninguno") if compilo else "",
                      "tactica": r.get("tactica", "") if r else "", "segundos": r["s"] if r else "",
                      "sha256_enunciado_falso": t["sha256_enunciado_falso"], "sha256_lean": sha(txt) if txt else "",
                      "motivo_si_no": motivo})
    with open(AQUI / "resumen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
    # Cada enunciado falso va en su propio archivo para que `shasum -a 256 -c SHA256SUMS` valide todas las líneas.
    (AQUI / "enunciados").mkdir(exist_ok=True)
    for t in tareas:
        (AQUI / "enunciados" / f"ETP_{t['id_corto']}.falso.txt").write_text(t["enunciado_falso_completo"], encoding="utf-8")
        sumas.append(f"{t['sha256_enunciado_falso']}  enunciados/ETP_{t['id_corto']}.falso.txt")
    for f in sorted((AQUI / "infinitos" / "PortF5").glob("*.lean")):  # la biblioteca de la que dependen las F5
        sumas.append(f"{sha(f.read_text(encoding='utf-8'))}  infinitos/PortF5/{f.name}")
    (AQUI / "SHA256SUMS").write_text("\n".join(sumas) + "\n", encoding="utf-8")
    print("refutadas:", sum(f["compilo"] == "sí" for f in filas), "de", len(filas))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["generar", "compilar", "registrar"])
    ap.add_argument("-j", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--limite", type=int, default=900)
    a = ap.parse_args()
    if a.accion == "generar":
        generar()
    elif a.accion == "compilar":
        compilar(a.j, set(filter(None, a.solo.split(","))), a.limite)
    else:
        registrar()
