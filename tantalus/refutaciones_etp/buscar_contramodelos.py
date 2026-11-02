"""Pasos 1 y 2 del encargo: extrae las 200 falsas del ETP y busca un contramodelo finito para cada una.

Solo lee el corpus congelado. Sin Lean ni API. Una tabla solo se acepta si la evaluación exhaustiva confirma que
cumple LeyA y no cumple LeyB, venga de la búsqueda propia o del repositorio del ETP.

Uso: python3 buscar_contramodelos.py [--testigos DIR] [--limite 120]
  --testigos: carpeta con los Refutation*.lean del ETP (commit 1aec8a7), nombrados con '/' cambiado por '_'.
Escribe tareas_etp.jsonl y contramodelos.jsonl. Reanudable: no repite lo ya resuelto en contramodelos.jsonl.
"""
import argparse, hashlib, itertools, json, re, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CORPUS = AQUI.parent.parent / "corpus_compilar" / "FINAL" / "corpus_compilado.jsonl"
COMMIT = "1aec8a7acf223b7c56e4830977b6e90d4ef1924b"
FALSA = "∀ (G : Type) [Magma G], LeyA G → LeyB G"


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def parse(s):
    toks = re.findall(r"[A-Za-z_]\w*|[()◇]", s)
    pos = 0

    def atom():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == "(":
            e = expr()
            assert toks[pos] == ")"; pos += 1
            return e
        return t

    def expr():
        nonlocal pos
        a = atom()
        while pos < len(toks) and toks[pos] == "◇":
            pos += 1; a = ("op", a, atom())
        return a

    e = expr(); assert pos == len(toks), s
    return e


def ley(ctx, nombre):
    m = re.search(r"def %s \(G : Type _\) \[Magma G\] : Prop :=\s*\n\s*∀ ([\w ]+) : G, (.+)" % nombre, ctx)
    izq, der = m.group(2).strip().split(" = ")
    return {"vars": m.group(1).split(), "izq": parse(izq), "der": parse(der), "texto": f"∀ {m.group(1)} : G, {m.group(2).strip()}"}


def ev(t, env, T):
    if isinstance(t, str):
        return env[t]
    a = ev(t[1], env, T)
    if a is None:
        return None
    b = ev(t[2], env, T)
    if b is None:
        return None
    return T[a][b]


def viola(L, T, n):
    for a in itertools.product(range(n), repeat=len(L["vars"])):
        env = dict(zip(L["vars"], a))
        x = ev(L["izq"], env, T)
        if x is None:
            continue
        y = ev(L["der"], env, T)
        if y is not None and x != y:
            return True
    return False


def es_contramodelo(A, B, T):
    n = len(T)
    ok = all(len(f) == n and all(0 <= v < n for v in f) for f in T)
    return ok and not viola(A, T, n) and viola(B, T, n)


def buscar(A, B, n, limite):
    """Retroceso exhaustivo con poda por LeyA. Devuelve tabla, o None si no existe; TimeoutError si se pasa."""
    T = [[None] * n for _ in range(n)]
    celdas = [(i, j) for i in range(n) for j in range(n)]
    t0 = time.time()

    def bt(k):
        if time.time() - t0 > limite:
            raise TimeoutError
        if k == len(celdas):
            return viola(B, T, n)
        i, j = celdas[k]
        for v in range(n):
            T[i][j] = v
            if not viola(A, T, n) and bt(k + 1):
                return True
        T[i][j] = None
        return False

    return [f[:] for f in T] if bt(0) else None


def testigo_repo(tarea, carpeta):
    """Tabla del archivo del ETP citado en prueba_publica: tabla explícita o polinomio módulo n."""
    ruta = tarea["prueba_publica"].split(COMMIT + "/")[1].split("#")[0]
    f = Path(carpeta) / ruta.replace("/", "_")
    if not f.exists():
        return None, None
    txt = f.read_text(encoding="utf-8")
    m = re.search(r"operator table:\s*\n(\[\[.*?\]\])", txt)
    if m:
        return json.loads(m.group(1)), ruta
    m = re.search(r"'\((\d+) \* x\*\*2 \+ (\d+) \* y\*\*2 \+ (\d+) \* x \+ (\d+) \* y \+ (\d+) \* x \* y\) % (\d+)'", txt)
    if m:
        a, b, c, d, e, n = map(int, m.groups())
        return [[(a * x * x + b * y * y + c * x + d * y + e * x * y) % n for y in range(n)] for x in range(n)], ruta
    return None, ruta


def extraer():
    filas = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    fal = [r for r in filas if r["fuente"] == "etp" and r["verdad"] == "falso"]
    assert len(fal) == 200
    tareas = []
    for r in fal:
        ctx = r["contexto_lean"]
        m = re.match(r"\s*theorem\s+(\S+)\s*:(.*):=\s*by\s+sorry\s*$", r["enunciado_lean"], re.S)
        guardado = m.group(2).strip()
        assert guardado == "¬ " + FALSA, guardado
        A, B = ley(ctx, "LeyA"), ley(ctx, "LeyB")
        # El texto «∀ G, LeyA G → LeyB G» es idéntico en las 200: lo que distingue la tarea son las definiciones,
        # así que el hash del enunciado falso se toma sobre contexto + enunciado.
        completo = ctx.rstrip("\n") + "\n\n" + f"theorem falsa_{r['id'].split(':')[1]} : {FALSA}"
        tareas.append({"id": r["id"], "id_corto": r["id"].split(":")[1], "familia": r["familia"],
                       "subfamilia": r["subfamilia"], "ley_a": A["texto"], "ley_b": B["texto"],
                       "enunciado_guardado": r["enunciado_lean"], "verdad_guardada": r["verdad"],
                       "enunciado_falso": FALSA, "enunciado_falso_completo": completo,
                       "sha256_enunciado_falso": sha(completo), "sha256_tarea_corpus": r["sha256_tarea"],
                       "contexto_lean": ctx, "prueba_publica": r["prueba_publica"], "notas": r["notas"]})
    with open(AQUI / "tareas_etp.jsonl", "w", encoding="utf-8") as f:
        for t in tareas:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return tareas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testigos")
    ap.add_argument("--limite", type=float, default=120)
    a = ap.parse_args()
    tareas = extraer()
    sal = AQUI / "contramodelos.jsonl"
    hechos = {}
    if sal.exists():
        for l in sal.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            hechos[r["id"]] = r
    for t in tareas:
        previo = hechos.get(t["id"])
        if previo and previo["estado"] == "ok":
            continue
        A, B = ley(t["contexto_lean"], "LeyA"), ley(t["contexto_lean"], "LeyB")
        fam = t["familia"][:2]
        t0 = time.time()
        res = None
        vistos = []
        if fam == "F4" and a.testigos:  # las notas ya descartan n ≤ 4: se parte del testigo del repositorio
            T, ruta = testigo_repo(t, a.testigos)
            if T and es_contramodelo(A, B, T):
                res = {"estado": "ok", "n": len(T), "tabla": T, "origen": f"repositorio ETP: {ruta}"}
            else:
                vistos.append(f"testigo del repositorio rechazado ({ruta})")
        if res is None:
            for n in (2, 3, 4):
                try:
                    T = buscar(A, B, n, a.limite)
                except TimeoutError:
                    vistos.append(f"n={n}: tiempo agotado ({a.limite:.0f} s)")
                    continue
                if T:
                    assert es_contramodelo(A, B, T)
                    res = {"estado": "ok", "n": n, "tabla": T, "origen": "búsqueda propia exhaustiva"}
                    break
                vistos.append(f"n={n}: no existe (exhaustivo)")
        if res is None:
            res = {"estado": "sin_contramodelo_hasta_4", "detalle": vistos}
        hechos[t["id"]] = {"id": t["id"], "familia": t["familia"], "ley_a": t["ley_a"], "ley_b": t["ley_b"], **res,
                           "s": round(time.time() - t0, 2)}
        print(t["id"], t["familia"][:2], res["estado"], res.get("n"), hechos[t["id"]]["s"], flush=True)
        with open(sal, "w", encoding="utf-8") as f:
            for tt in tareas:
                if tt["id"] in hechos:
                    f.write(json.dumps(hechos[tt["id"]], ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
