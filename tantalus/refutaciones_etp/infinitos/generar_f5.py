"""Genera PortF5/Tareas.lean y lean_f5/ETP_<id>.lean para las 30 tareas F5, y los compila contra PortF5.

Cada tarea sale de un modelo infinito del ETP (o de su opuesto). Los argumentos de cada instancia se calculan aquí por
unificación sintáctica de las leyes, para no escribir a mano ni cambiar variables por error; Lean chequea el resultado.

Uso: python3 generar_f5.py generar | compilar [-j 4]"""
import argparse, concurrent.futures as cf, hashlib, itertools, json, re, subprocess, sys, time
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
import buscar_contramodelos as B
import generar_y_compilar as G

ECU = {int(m[1]): (m[2].split(), m[3]) for m in re.finditer(r"abbrev Equation(\d+) .*?:= ∀ ([\w ]+) : G, (.+)", (AQUI/"PortF5/Ecuaciones.lean").read_text())}
def ley_ecu(k):
    vs, tx = ECU[k]; i, d = tx.split(" = ")
    return {"vars": vs, "izq": B.parse(i), "der": B.parse(d)}
def dual(t):
    return t if isinstance(t, str) else ("op", dual(t[2]), dual(t[1]))
def unif(p, t, s):
    if isinstance(p, str):
        if p in s: return s[p] == t
        s[p] = t; return True
    return not isinstance(t, str) and unif(p[1], t[1], s) and unif(p[2], t[2], s)
def instancia(gen, esp):
    """Valores de las variables de gen que dan esp, y si hay que voltear la igualdad."""
    for volt, (i, d) in ((False, (esp["izq"], esp["der"])), (True, (esp["der"], esp["izq"]))):
        s = {}
        if unif(gen["izq"], i, s) and unif(gen["der"], d, s):
            return s, volt
    raise SystemExit(f"no unifica {gen} con {esp}")
def enop(t, o="o"):
    return t if isinstance(t, str) else f"({o} {enop(t[1], o)} {enop(t[2], o)})"
def plano(L):
    return f"∀ {' '.join(L['vars'])} : G, {enop(L['izq'])} = {enop(L['der'])}"

# id: (dual, base, fuente) con base = («facts», teorema, ley base, ley refutada) o («nat», tipo, op, satisface, ley base, testigo)
LISTAS = {"rw481": [1496, 2035, 3050, 3056], "rw1523": [2035, 2124, 2132], "rw3588": [3878, 3917, 3955],
          "rw1443": [4065, 4067], "rw1633": [4268, 4282]}
def proyeccion(th, kb):
    """hB.1, hB.2.1, … para sacar ¬Equation kb de la conjunción de Facts."""
    l = LISTAS.get(th.split(".")[0])
    if not l: return "hB"
    i = l.index(kb)
    return "hB" + ".2" * i + (".1" if i < len(l) - 1 else "")
def fact(th, a, b): return ("facts", th, a, b)
def nat(ty, op, sat, a, w): return ("nat", ty, op, sat, a, w)
M1437 = lambda w: nat("ℕ × Fin 3", "Eq1437.op", "Eq1437.satisface1437", 1437, w)
M1659 = lambda w: nat("ℕ", "op_1659_4315", "op_1659_4315_satisfies_1659", 1659, w)
M1661 = lambda w: nat("ℕ", "op_1661_1657", "op_1661_1657_satisfies_1661", 1661, w)
M1701 = lambda w: nat("ℕ", "op_1701_8", "op_1701_8_satisfies_1701", 1701, w)
PLAN = {
 "3161_473": (1, fact("rw481.«Facts»", 481, 3056)), "3161_411": (1, fact("rw481.«Facts»", 481, 3050)),
 "481_2035": (0, fact("rw481.«Facts»", 481, 2035)), "481_1496": (0, fact("rw481.«Facts»", 481, 1496)),
 "2291_4647": (1, fact("rw1276.«Facts»", 1276, 4332)),
 "2132_1523": (1, fact("rw1523.«Facts»", 1523, 2132)), "2132_1426": (1, fact("rw1523.«Facts»", 1523, 2035)),
 "1523_2124": (0, fact("rw1523.«Facts»", 1523, 2124)),
 "3917_3511": (1, fact("rw3588.«Facts»", 3588, 3955)), "3588_3955": (0, fact("rw3588.«Facts»", 3588, 3955)),
 "3994_3549": (1, fact("rw3588.«Facts»", 3588, 3917)), "3588_3878": (0, fact("rw3588.«Facts»", 3588, 3878)),
 "1441_4067": (0, fact("rw1443.«Facts»", 1443, 4067)), "2037_3253": (1, fact("rw1443.«Facts»", 1443, 4065)),
 "1633_4282": (0, fact("rw1633.«Facts»", 1633, 4282)), "1958_4587": (1, fact("rw1633.«Facts»", 1633, 4268)),
 "883_2035": (0, fact("Eq883.Equation883_not_implies_Equation2035", 883, 2035)),
 "883_2304": (0, fact("Eq883.Equation883_not_implies_Equation2304", 883, 2304)),
 "2744_1526": (1, fact("Eq883.Equation883_not_implies_Equation2101", 883, 2101)),
 "3994_3588": (0, fact("Equation3994_not_implies_Equation3588", 3994, 3588)),
 "2070_4631": (1, M1437("(0, 0) (0, 0) (0, 2)")),
 "1659_1852": (0, M1659("0 0 1")), "1659_3519": (0, M1659("0 1")),
 "2000_1897": (1, M1659("0 1")), "2000_4615": (1, M1659("0 0 1")),
 "1979_1742": (1, M1661("0 3 0")), "1979_1681": (1, M1661("3 0")),
 "1661_4282": (0, M1661("3 0 1")), "1661_4314": (0, M1661("0 3")),
 "1681_3877": (0, M1701("1 0")),
}
def tareas():
    return [t for t in G.leer("../tareas_etp.jsonl") if t["familia"].startswith("F5")] if False else \
           [json.loads(l) for l in (RAIZ/"tareas_etp.jsonl").read_text().splitlines() if '"F5_' in l]
def arg(t, inst):  # término en la operación del modelo base
    return t if isinstance(t, str) else f"({inst} {arg(t[1], inst)} {arg(t[2], inst)})"
def teorema(t):
    cid = t["id_corto"]; es_dual, b = PLAN[cid]
    A, C = B.ley(t["contexto_lean"], "LeyA"), B.ley(t["contexto_lean"], "LeyB")
    enunc = f"theorem t_{cid} : ∃ (G : Type) (o : G → G → G),\n    ({plano(A)}) ∧ ¬ ({plano(C)}) := by\n"
    tr = (lambda x: dual(x)) if es_dual else (lambda x: x)
    Ad = {"izq": tr(A["izq"]), "der": tr(A["der"])}
    if b[0] == "facts":
        _, th, ka, kb = b
        s, v = instancia(ley_ecu(ka), Ad)
        ga = " ".join(arg(s[x], "Magma.op") for x in ley_ecu(ka)["vars"])
        ha = f"(hA {ga})" + (".symm" if v else "")
        Cd = {"izq": tr(C["izq"]), "der": tr(C["der"])}
        Lb = ley_ecu(kb)
        s2, v2 = instancia({"izq": Cd["izq"], "der": Cd["der"]}, Lb)
        gb = " ".join(s2.get(x, "x_libre") for x in C["vars"])
        hb = f"(h {gb})" + (".symm" if v2 else "")
        o = "fun a b => Magma.op b a" if es_dual else "fun a b => Magma.op a b"
        cuerpo = (f"  obtain ⟨G, _, hA, hB⟩ := {th}\n  refine ⟨G, {o}, ?_, ?_⟩\n"
                  f"  · intro {' '.join(A['vars'])}\n    exact {ha}\n"
                  f"  · intro h\n    exact {proyeccion(th, kb)} (fun {' '.join(Lb['vars'])} => {hb})\n")
        if "x_libre" in gb: raise SystemExit(cid + ": variable libre")
    else:
        _, ty, op, sat, ka, w = b
        s, v = instancia(ley_ecu(ka), Ad)
        ga = " ".join(arg(s[x], op) for x in ley_ecu(ka)["vars"])
        o = f"fun a b => {op} b a" if es_dual else f"fun a b => {op} a b"
        cuerpo = (f"  refine ⟨{ty}, {o}, ?_, ?_⟩\n  · intro {' '.join(A['vars'])}\n    exact {'(' + sat + ' ' + ga + ')' + ('.symm' if v else '')}\n"
                  f"  · intro h\n    have h' := h {w}\n    revert h'\n    decide\n")
    return enunc + cuerpo
def archivo_final(t):
    cid = t["id_corto"]
    return ("import Mathlib\nimport PortF5.Tareas\nset_option relaxedAutoImplicit false\nset_option maxSynthPendingDepth 3\n\n"
            f"{t['contexto_lean'].rstrip()}\n\n"
            f"/-- Refutación con un magma infinito: {t['id']} es un par de Austin, así que no hay contramodelo finito. -/\n"
            f"theorem refuta_{cid} : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) := by\n  intro h\n"
            f"  obtain ⟨G, o, hA, hB⟩ := ETP.t_{cid}\n  letI : Magma G := ⟨o⟩\n  exact hB (h G hA)\n\n#print axioms refuta_{cid}\n")
def generar():
    ts = tareas(); assert len(ts) == 30 and {t["id_corto"] for t in ts} == set(PLAN)
    imps = "import PortF5.Confluence2\nimport PortF5.Confluence3\nimport PortF5.Confluence4\nimport PortF5.Eq1437\nimport PortF5.Eq1659\nimport PortF5.Eq1661\nimport PortF5.Eq1701\nimport PortF5.Inf3994\nimport PortF5.Eq883\n"
    (AQUI/"PortF5/Tareas.lean").write_text(imps + "\n/- Los 30 enunciados F5 en forma plana, sin clase Magma. -/\n\nnamespace ETP\n\nopen FreeMagma Confluence\n\n" + "\n".join(teorema(t) for t in ts) + "\nend ETP\n")
    (AQUI/"lean_f5").mkdir(exist_ok=True)
    for t in ts: (AQUI/"lean_f5"/f"ETP_{t['id_corto']}.lean").write_text(archivo_final(t))
    print("generadas", len(ts))
def compilar(j, solo=()):
    r = subprocess.run(["lake","env","env"],cwd=G.PROYECTO,capture_output=True,text=True,check=True)
    env = dict(l.split("=",1) for l in r.stdout.splitlines() if "=" in l); env["LEAN_PATH"] = f"{AQUI/'build'}:{env['LEAN_PATH']}"
    def una(t):
        cid = t["id_corto"]; t0 = time.time()
        p = subprocess.run(["lean","--json","-j","1",str(AQUI/"lean_f5"/f"ETP_{cid}.lean")],cwd=G.PROYECTO,env=env,capture_output=True,text=True,timeout=900)
        msgs = [{"sev":j_.get("severity"),"texto":j_.get("data") or ""} for j_ in map(json.loads,[l for l in p.stdout.splitlines() if l.startswith("{")])]
        err = [m["texto"][:300] for m in msgs if m["sev"]=="error"]; ax = G.axiomas(msgs,f"refuta_{cid}")
        ok = p.returncode==0 and not err and ax is not None and not set(ax)-G.PERMITIDOS
        return {"id":t["id"],"id_corto":cid,"familia":t["familia"],"compilo":ok,"axiomas":ax,"motivo":(err or [""])[0],"s":round(time.time()-t0,1)}
    ts = [t for t in tareas() if not solo or t["id_corto"] in solo]
    with cf.ThreadPoolExecutor(j) as ex, open(AQUI/"resultados_f5.jsonl","a" if solo else "w") as f:
        for k,r in enumerate(ex.map(una,ts),1):
            f.write(json.dumps(r,ensure_ascii=False)+"\n"); print(f"[{k}/30] {r['id']} {'ok' if r['compilo'] else 'FALLA '+r['motivo'][:160]} {r['axiomas']} {r['s']} s",flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser(); a.add_argument("accion",choices=["generar","compilar"]); a.add_argument("-j",type=int,default=4); a.add_argument("--solo",default=""); x=a.parse_args()
    generar() if x.accion=="generar" else compilar(x.j,set(filter(None,x.solo.split(","))))
