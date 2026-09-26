"""Sledgehammer sobre objetivos sueltos, en el contexto de las hipótesis de la bisección (sin vcg).
Sirve para probar si «adelgazar las premisas» de una VC permite a Sledgehammer encontrar la prueba.
Usa la misma configuración que el driver de 08 (proveedores por defecto, preplay) y el mismo timeout.

    python tools/sh_goal.py --timeout 60
Escribe runs/_baseline/sh_goals.json.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / "08_isabelle"))
from isarl import config, driver  # noqa: E402

FIXES = 'f :: "real \\<Rightarrow> real" and a b tol :: real'
ASSUMES = ('postive_tolerance: "0 < tol"\n    and sufficiently_small_tol: "tol < b-a"\n'
           '    and continuous_f: "continuous_on {a..b} f"\n    and opposite_signs: "f(a)*f(b)<0"')
# Los tres hechos que el paper establece antes de `proof (vcg)`.
PAPER_PRELUDE = '''lemma a_less_than_b: "a < b" using postive_tolerance sufficiently_small_tol by auto
lemma ln2_g_0 [simp]: "\\<lceil>log 2 ((b - a) / tol)\\<rceil> > 0" using sufficiently_small_tol postive_tolerance by force
lemma log_pos [simp]: "0 < log 2 ((b - a) / tol)" using ln2_g_0 zero_less_ceiling by simp'''
VAR = "nat \\<lceil>log 2 ((b - a) / tol)\\<rceil> - Suc iter < nat \\<lceil>log 2 ((b - a) / tol)\\<rceil> - iter"
GOALS = {
    # la VC 4 tal como la produce vcg con el invariante del paper (7 premisas)
    "full": "\\<And>iter u xmid. \\<lbrakk>0 < f xmid * f ((xmid + u) / 2); a \\<le> xmid; u \\<le> b; xmid < u; f xmid * f u \\<le> 0; "
            "u - xmid = (b - a) / 2 ^ iter; tol < (b - a) / 2 ^ iter\\<rbrakk> \\<Longrightarrow> " + VAR,
    # la misma VC con una sola premisa, como la enuncia el paper
    "thin": "\\<And>iter. tol < (b - a) / 2 ^ iter \\<Longrightarrow> " + VAR,
}
ML = r'''
ML \<open>
local
  fun esc s = String.translate (fn #"\"" => "\\\"" | #"\\" => "\\\\" | #"\n" => " " | c => String.str c) s
  fun plain s = XML.content_of (YXML.parse_body s)
  val ctxt = @{context}
  val thy = Proof_Context.theory_of ctxt
  fun run (name, goal) =
    let
      val msgs = Unsynchronized.ref ([] : string list)
      val params = Sledgehammer_Commands.default_params thy [("timeout", "__T__"), ("isar_proofs", "false")]
      val st = Proof.theorem NONE (K I) [[(goal, [])]] ctxt
      val timer = Timing.start ()
      val r = Exn.result (fn () => Sledgehammer.run_sledgehammer params Sledgehammer_Prover.Normal
                (SOME (fn s => msgs := s :: !msgs)) 1 Sledgehammer_Fact.no_fact_override st) ()
      val ms = Int.toString (Time.toMilliseconds (#elapsed (Timing.result timer)))
      val (found, oc, msg) = case r of Exn.Res (b, (oc0, m)) => (b, Sledgehammer.short_string_of_sledgehammer_outcome oc0, plain m)
                                     | Exn.Exn e => (false, "exception", plain (Runtime.exn_message e))
    in "{\"name\":\"" ^ name ^ "\",\"found\":" ^ (if found then "true" else "false") ^ ",\"outcome\":\"" ^ esc oc ^
       "\",\"message\":\"" ^ esc msg ^ "\",\"messages\":\"" ^ esc (String.concatWith " | " (map plain (rev (!msgs)))) ^ "\",\"ms\":" ^ ms ^ "}" end
  val goals = [__GOALS__]
in
  val _ = File.write (Path.explode "__OUT__") ("[" ^ String.concatWith "," (map run goals) ^ "]")
end
\<close>
'''

ap = argparse.ArgumentParser()
ap.add_argument("--timeout", type=int, default=60)
a = ap.parse_args()
results = {}
for prelude_name, prelude in (("sin_prelude", ""), ("con_prelude_del_paper", PAPER_PRELUDE)):
    work = config.SCRATCH / f"shgoal-{prelude_name}-{int(time.time())}"
    work.mkdir(parents=True, exist_ok=True)
    out = work / "out.json"
    goals = ", ".join(f'("{n}", @{{prop \\<open>{g}\\<close>}})' for n, g in GOALS.items())
    thy = ("theory Driver\n  imports \"ITree_Numeric_VCG.ITree_Numeric_VCG\"\nbegin\n\ncontext\n  fixes " + FIXES +
           "\n  assumes " + ASSUMES + "\nbegin\n\n" + prelude + "\n" +
           ML.replace("__T__", str(a.timeout)).replace("__GOALS__", goals).replace("__OUT__", str(out)) + "\nend\n\nend\n")
    (work / "Driver.thy").write_text(thy, encoding="utf-8")
    (work / "ROOT").write_text(f"session {driver.SCRATCH_SESSION} = {config.PAPER_SESSION} +\n  options [document = false, timeout = 0]\n  theories\n    Driver\n", encoding="utf-8")
    rc, log, el = driver.build(work, 1800)
    res = json.loads(out.read_text()) if out.exists() else [{"error": [l for l in log.splitlines() if l.startswith("***")][:5]}]
    results[prelude_name] = res
    for g in res:
        print(prelude_name, g.get("name"), g.get("outcome"), g.get("ms"), (g.get("message") or str(g.get("error")))[:160])
dest = HERE / "runs" / "_baseline" / "sh_goals.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps({"timeout": a.timeout, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
print("→", dest)
