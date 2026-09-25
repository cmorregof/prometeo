"""Driver de VCs: genera una teoría de trabajo, corre `vcg` sobre la tripleta de Hoare,
y sobre cada VC abierta intenta (1) métodos de una línea (`try0`) y (2) Sledgehammer con
timeout fijo. Todo se ejecuta dentro de `isabelle build` de una sesión de trabajo
(`IsaRL_Scratch`), que carga el heap de la sesión del paper. El resultado se escribe en
JSON desde ML y se lee aquí.

Una VC cuenta como «automática» (definición del pie de la Tabla 1 del paper) si la cierra
una llamada directa a un prover: un método de una línea de `try0` (simp, auto, blast,
linarith, force, ...) o el `by (metis ...)`/`by (smt ...)` sugerido por Sledgehammer y
verificado por preplay. Nada estructurado en Isar cuenta como automático.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import config

SCRATCH_SESSION = "IsaRL_Scratch"

ML_DRIVER = r'''
ML \<open>
local
  fun esc s =
    String.translate (fn #"\"" => "\\\"" | #"\\" => "\\\\" | #"\n" => "\\n" | #"\t" => "\\t"
                        | c => if Char.ord c < 32 then " " else String.str c) s
  fun jstr s = "\"" ^ esc s ^ "\""
  fun jlist xs = "[" ^ String.concatWith "," xs ^ "]"
  fun jobj kvs = "{" ^ String.concatWith "," (map (fn (k, v) => jstr k ^ ":" ^ v) kvs) ^ "}"
  fun jbool b = if b then "true" else "false"
  fun ms t = Int.toString (Time.toMilliseconds t)
  fun plain s = XML.content_of (YXML.parse_body s)

  val ctxt = @{context}
  val thy = Proof_Context.theory_of ctxt
  val out_path = Path.explode "__OUT__"
  val sh_timeout = __SH_TIMEOUT__
  val try0_timeout = __TRY0_TIMEOUT__
  val concl = @{prop \<open>__CONCL__\<close>}

  fun apply_method_text txt st =
    let val (text, _) = Method.read_closure_input (Proof.context_of st) (Input.string txt)
    in case Seq.pull (Proof.apply (text, Position.no_range) st) of
         SOME (Seq.Result st', _) => SOME st'
       | _ => NONE
    end

  (* try0 sobre el primer subobjetivo; devuelve el comando de una línea si lo hay *)
  fun run_try0 st =
    case Exn.result (fn () =>
      let
        val res = Try0.try0 (SOME (seconds (Real.fromInt try0_timeout))) [] st
        val res2 = if null res then Try0.try0 (SOME (seconds (Real.fromInt try0_timeout)))
                       [((Facts.named "assms", []), [Try0.Use])] st else []
      in res @ res2 end) () of
      Exn.Res [] => NONE
    | Exn.Res ({command, time, ...} :: _) => SOME (command, time, true)
    | Exn.Exn _ => NONE

  (* Sledgehammer sobre el primer subobjetivo; captura los mensajes *)
  fun run_sh st =
    let
      val msgs = Unsynchronized.ref ([] : string list)
      val params = Sledgehammer_Commands.default_params thy
        [("timeout", Int.toString sh_timeout), ("verbose", "false"), ("isar_proofs", "false")]
      val timer = Timing.start ()
      val r = Exn.result (fn () =>
        Sledgehammer.run_sledgehammer params Sledgehammer_Prover.Normal
          (SOME (fn s => msgs := s :: !msgs)) 1 Sledgehammer_Fact.no_fact_override st) ()
      val elapsed = #elapsed (Timing.result timer)
    in
      case r of
        Exn.Res (found, (outcome, msg)) =>
          (found, Sledgehammer.short_string_of_sledgehammer_outcome outcome, plain msg, map plain (rev (!msgs)), elapsed)
      | Exn.Exn exn => (false, "exception", plain (Runtime.exn_message exn), [], elapsed)
    end

  (* vcg sobre la tripleta *)
  val st0 = Proof.theorem NONE (K I) [[(concl, [])]] ctxt
  val timer_vcg = Timing.start ()
  val st1 = case apply_method_text "vcg" st0 of SOME st => st | NONE => error "vcg failed"
  val vcg_ms = ms (#elapsed (Timing.result timer_vcg))
  val goal_thm = #goal (Proof.goal st1)
  val vcs = Thm.prems_of goal_thm
  val n = length vcs

  val only = [__ONLY__] : int list
  val given = [__GIVEN__] : (int * string) list  (* (índice, método) *)
  fun check_given i vc =
    case AList.lookup (op =) given i of
      NONE => "null"
    | SOME m =>
        let
          val st = Proof.theorem NONE (K I) [[(vc, [])]] ctxt
          val timer = Timing.start ()
          val closed = (case Exn.result (fn () => apply_method_text m st) () of
              Exn.Res (SOME st') => Thm.no_prems (#goal (Proof.goal st'))
            | _ => false)
          val t = ms (#elapsed (Timing.result timer))
        in jobj [("method", jstr m), ("closed", jbool closed), ("ms", t)] end

  fun one_vc (i, vc) =
    let
      val text = plain (Syntax.string_of_term ctxt vc)
      val st_i = Proof.theorem NONE (K I) [[(vc, [])]] ctxt
      val (t0, t0_ms, t0_plain) = case run_try0 st_i of
          SOME (cmd, t, p) => (jstr cmd, Int.toString t, p) | NONE => ("null", "0", false)
      val (sh_found, sh_outcome, sh_msg, sh_msgs, sh_t) =
        if t0 <> "null" then (false, "skipped", "", [], Time.zeroTime) else run_sh st_i
      val _ = writeln ("[isarl] VC " ^ Int.toString i ^ "/" ^ Int.toString n ^ ": try0=" ^ t0 ^ " sh=" ^ sh_outcome)
    in
      jobj [("index", Int.toString i), ("goal", jstr text),
            ("try0", t0), ("try0_ms", t0_ms), ("try0_without_assms", jbool t0_plain),
            ("sh_found", jbool sh_found), ("sh_outcome", jstr sh_outcome), ("sh_message", jstr sh_msg),
            ("sh_messages", jlist (map jstr sh_msgs)), ("sh_ms", ms sh_t), ("given", check_given i vc)]
    end

  val results = map one_vc (filter (fn (i, _) => null only orelse member (op =) only i) (map_index (fn (i, vc) => (i + 1, vc)) vcs))
  val json = jobj [("n_vcs", Int.toString n), ("vcg_ms", vcg_ms), ("vcs", jlist results),
                   ("provers", jstr (plain (Sledgehammer_Commands.default_params thy [] |> #provers |> String.concatWith " ")))]
in
  val _ = File.write out_path json
  val _ = writeln ("[isarl] written " ^ Path.print out_path)
end
\<close>
'''

THEORY_TEMPLATE = '''theory Driver
  imports __IMPORTS__
begin

__PROGRAM__

context
  fixes __FIXES__
  assumes __ASSUMES__
begin

__PRELUDE__

__ML__

end

end
'''


@dataclass
class VCResult:
    index: int
    goal: str
    try0: str | None
    try0_ms: int
    try0_without_assms: bool
    sh_found: bool
    sh_outcome: str
    sh_message: str
    sh_messages: list[str]
    sh_ms: int
    given: dict | None = None

    @property
    def one_liner(self) -> str | None:
        """Comando de una línea que cierra la VC, si lo hay (try0 o Sledgehammer con preplay)."""
        if self.try0:
            return self.try0
        if self.sh_found:
            m = re.search(r"Try this: (by .*?|using .*?)(?: \(\d+ ms\)| \(\d+(?:\.\d+)? s\))?\s*$", self.sh_message, re.S)
            if m:
                return m.group(1).strip()
        return None

    @property
    def method(self) -> str:
        if self.try0:
            return "try0:" + self.try0.split()[1].strip("()") if len(self.try0.split()) > 1 else "try0"
        if self.sh_found:
            return "sledgehammer"
        return "open"


@dataclass
class DriverResult:
    ok: bool
    n_vcs: int
    vcg_ms: int
    vcs: list[VCResult]
    provers: str
    elapsed_s: float
    build_rc: int
    raw_log: str
    error: str = ""

    @property
    def n_closed_auto(self) -> int:
        return sum(1 for v in self.vcs if v.one_liner)

    @property
    def open_vcs(self) -> list[VCResult]:
        return [v for v in self.vcs if not v.one_liner]

    def to_dict(self) -> dict:
        d = asdict(self)
        for v, vd in zip(self.vcs, d["vcs"]):
            vd["one_liner"] = v.one_liner
            vd["method"] = v.method
        d["n_closed_auto"] = self.n_closed_auto
        return d


def isabelle_env() -> dict[str, str]:
    """Qué provers externos ve Isabelle (para el README: el 13/15 depende de esto)."""
    out = subprocess.run([str(config.ISABELLE_BIN), "getenv"] + config.PROVER_ENV_VARS, capture_output=True, text=True).stdout
    env = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


def write_scratch(work: Path, imports: str, program: str, fixes: str, assumes: str, concl: str, prelude: str,
                  sh_timeout: int, try0_timeout: int, only: tuple[int, ...] = (), given: dict[int, str] | None = None) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    out = work / "result.json"
    ml = (ML_DRIVER.replace("__OUT__", str(out)).replace("__SH_TIMEOUT__", str(sh_timeout))
          .replace("__TRY0_TIMEOUT__", str(try0_timeout)).replace("__CONCL__", concl)
          .replace("__ONLY__", ", ".join(str(i) for i in only))
          .replace("__GIVEN__", ", ".join("(%d, Input.string_of \\<open>%s\\<close>)" % (i, m) for i, m in (given or {}).items())))
    thy = (THEORY_TEMPLATE.replace("__IMPORTS__", imports).replace("__PROGRAM__", program).replace("__FIXES__", fixes)
           .replace("__ASSUMES__", assumes).replace("__PRELUDE__", prelude).replace("__ML__", ml))
    (work / "Driver.thy").write_text(thy, encoding="utf-8")
    (work / "ROOT").write_text(
        f'session {SCRATCH_SESSION} = {config.PAPER_SESSION} +\n  options [document = false, timeout = 0]\n  theories\n    Driver\n',
        encoding="utf-8")
    return out


def build(work: Path, timeout_s: float) -> tuple[int, str, float]:
    cmd = [str(config.ISABELLE_BIN), "build", "-o", "document=false", "-v"]
    for d in config.session_dirs() + [str(work)]:
        cmd += ["-d", d]
    cmd.append(SCRATCH_SESSION)
    t = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        rc, log = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired as e:
        rc, log = -9, (e.stdout or b"").decode(errors="replace") + "\n[isarl] TIMEOUT tras %.0f s" % timeout_s
    return rc, log, time.time() - t


def run_driver(imports: str, program: str, fixes: str, assumes: str, concl: str, prelude: str = "",
               sh_timeout: int = 60, try0_timeout: int = 5, build_timeout_s: float = 3600,
               work: Path | None = None, only: tuple[int, ...] = (), given: dict[int, str] | None = None) -> DriverResult:
    work = work or (config.SCRATCH / f"driver-{int(time.time())}-{os.getpid()}")
    out = write_scratch(work, imports, program, fixes, assumes, concl, prelude, sh_timeout, try0_timeout, only, given)
    if out.exists():
        out.unlink()
    rc, log, elapsed = build(work, build_timeout_s)
    if not out.exists():
        return DriverResult(False, 0, 0, [], "", elapsed, rc, log, error="el driver no escribió result.json (¿falló vcg o la teoría?)")
    data = json.loads(out.read_text(encoding="utf-8"))
    vcs = [VCResult(**v) for v in data["vcs"]]
    return DriverResult(rc == 0, data["n_vcs"], int(data["vcg_ms"]), vcs, data.get("provers", ""), elapsed, rc, log)
