"""Tests de unirl. Sin LLM. Los de PEP necesitan cvxpy/clarabel; los de Isabelle marcados `isabelle`
necesitan Isabelle2025 en ~/isabelle (se saltan si no está)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unirl.cli import summarize
from unirl.env import ProofEnv, reward
from unirl.loop import run_episodes
from unirl.verifiers import IsabelleVerifier, LemmaGraphVerifier, Outcome, PEPVerifier, check_annotation, check_lemmas

PROJECTS = ["01_biseccion", "02_punto_fijo", "03_taylor", "04_newton", "05_secante"]
HAS_ISABELLE = (Path.home() / "isabelle" / "Isabelle2025.app" / "bin" / "isabelle").exists()


def topological_chain(v: LemmaGraphVerifier) -> list[str]:
    req, order, done = v.kb.REQUIRED_KEYS, [], set()
    while len(order) < len(req):
        for s in v.steps:
            if s.key in req and s.key not in done and all(d in done for d in s.deps):
                order.append(v.alias[s.key])
                done.add(s.key)
    return order


# --------------------------------------------------------------------------- V_G

@pytest.mark.parametrize("project", PROJECTS)
def test_graph_accepts_topological_chain_and_rejects_errors(project):
    v = LemmaGraphVerifier(project)
    t = v.target()
    chain = topological_chain(v)
    assert v.verify(t, chain).outcome_label == "ACCEPTED"
    assert len(chain) == t["min_length"]
    distractor = next(v.alias[s.key] for s in v.steps if s.distractor)
    assert v.verify(t, [distractor] + chain).outcome_label == "DISTRACTOR"
    assert v.verify(t, chain[::-1]).outcome_label == "INVALID_STEP"  # orden inverso: dependencias no establecidas
    assert v.verify(t, chain[:1] + chain[:1]).outcome_label == "INVALID_STEP"  # repetido
    inc = v.verify(t, chain[:-1])
    assert inc.outcome_label == "INCOMPLETE" and inc.partial_credit == pytest.approx((len(chain) - 1) / len(chain))
    assert v.verify(t, ["L99"]).outcome_label == "UNKNOWN_LEMMA"
    assert v.verify(t, chain + chain).outcome_label == "ACCEPTED"  # se acepta al llegar a QED; lo que sigue se ignora


def test_graph_partial_credit_counts_only_required_lemmas():
    v = LemmaGraphVerifier("01_biseccion")
    extra = [s for s in v.steps if not s.distractor and s.key not in v.required and not s.deps]
    for s in extra:  # un lema verdadero pero innecesario no suma progreso
        assert v.verify(v.target(), [v.alias[s.key]]).partial_credit == 0.0


@pytest.mark.parametrize("project", PROJECTS)
def test_nothing_shown_gives_the_distractor_away(project):
    v = LemmaGraphVerifier(project)
    text = v.describe(v.target())
    assert "Distractor" not in text and "Non sequitur" not in text  # títulos ocultos
    for lem in v.target()["lemmas"]:  # refutaciones del profesor
        assert "¡" not in lem["text"] and "falso" not in lem["text"].lower() and "eso es bisección" not in lem["text"], lem


def test_refutation_stripping_touches_exactly_seven_distractors():
    n = 0
    for p in PROJECTS:
        v = LemmaGraphVerifier(p)
        for s in v.steps:
            if v.shown_text(s) != s.text:
                assert s.distractor
                n += 1
    assert n == 7


# --------------------------------------------------------------------------- MDP y bucle

class ScriptedProvider:
    def __init__(self, answers):
        self.answers = list(answers)

    def complete(self, system, user):
        return self.answers.pop(0)


def test_loop_logs_every_attempt_and_summary_censors_tstar(tmp_path):
    v = LemmaGraphVerifier("04_newton")
    chain = topological_chain(v)
    bad, good = json.dumps({"steps": chain[::-1]}), json.dumps({"steps": chain})
    env = ProofEnv(v, budget=3)
    meta = {"env": "t", "judge": v.name, "provider": "mock", "model": "m", "effort": "", "budget": 3, "run": "r1"}
    eps = run_episodes(env, ScriptedProvider([bad, good, bad, bad, bad]), 2, tmp_path / "t" / "r1", meta, verbose=False)
    assert eps[0]["accepted"] and eps[0]["steps"] == 2
    assert not eps[1]["accepted"] and eps[1]["steps"] == 3
    lines = [json.loads(l) for l in (tmp_path / "t" / "r1" / "attempts.jsonl").read_text().splitlines()]
    assert len(lines) == 5 and lines[1]["reward"] == 1.0 and lines[0]["reward"] == 0.0
    # una segunda corrida el mismo día no debe mezclar episodios con la primera
    run_episodes(ProofEnv(v, budget=3), ScriptedProvider([good, good]), 2, tmp_path / "t" / "r2", {**meta, "run": "r2"}, verbose=False)
    row = summarize(tmp_path)[0]
    assert row["episodes"] == 4 and row["accepted_eps"] == 3
    assert row["tstar_dist"] == {1: 2, 2: 1, 3: 1}  # el episodio fallido cuenta con t* = B = 3


def test_reward_base_shaped_and_drift():
    fail = Outcome(False, "VC_OPEN", 0.6, 0.0)
    assert reward(fail) == 0.0
    assert reward(fail, shaped=True, beta=0.5) == pytest.approx(0.3)
    assert reward(Outcome(True, "ACCEPTED", 1.0, 0.0), shaped=True) == 1.0
    drift = Outcome(False, "STATEMENT_DRIFT", 0.0, 0.0)
    assert reward(drift) == 0.0 and reward(drift, drift_penalty=0.2) == -0.2
    with pytest.raises(ValueError):
        ProofEnv(LemmaGraphVerifier("01_biseccion"), beta=0.9)


# --------------------------------------------------------------------------- V_P

def test_pep_modes():
    known = "def schedule(n):\n    return [1.4142, 1.8768][:n]"  # óptimo conocido para n = 2
    v_imp, v_match = PEPVerifier(n=2, mode="improve"), PEPVerifier(n=2, mode="match")
    assert v_imp.verify(v_imp.target(), known).outcome_label == "NOT_IMPROVED"  # igualar no es mejorar
    assert v_match.verify(v_match.target(), known).outcome_label == "MATCHED"
    const = v_match.verify(v_match.target(), "def schedule(n):\n    return [1.0]*n")
    assert const.outcome_label == "NOT_IMPROVED" and 0 < const.partial_credit < 1
    assert v_imp.verify(v_imp.target(), "def schedule(n):\n    return [0.0]*n").outcome_label == "INVALID_SCHEDULE"


EXPLOIT_VP = r'''
def schedule(n):
    sysmod = None
    for c in ().__class__.__base__.__subclasses__():
        try:
            g = c.__init__.__globals__
        except Exception:
            continue
        if "sys" in g:
            sysmod = g["sys"]
            break
    env = sysmod.modules["steprl.env"]
    T = ().__class__.__class__
    R = T("R", (), {"value": 1e-3})
    C = T("C", (), {"ok": True, "tau_float": 1e-3, "to_json": lambda self: {}})
    env.gd_worst_case = lambda *a, **k: R()
    env.certify = lambda *a, **k: C()
    return [1.0] * n
'''


def test_pep_program_cannot_patch_the_judge():
    """Hallazgo de la revisión adversarial: por introspección, el programa alcanzaba los módulos del juez y
    obtenía CERTIFIED con el paso constante. Ahora corre en un intérprete aparte."""
    v = PEPVerifier(n=4, mode="improve")
    t = v.target()
    o = v.verify(t, EXPLOIT_VP)
    assert o.outcome_label == "NOT_IMPROVED" and o.raw["tau"] > 0.05  # el peor caso real del paso constante (≈ 0,0556)
    o2 = v.verify(t, "def schedule(n):\n    return [1.0]*n")
    assert o2.raw["tau"] == pytest.approx(o.raw["tau"])  # y no deja rastro en el proceso del juez


def test_pep_program_cannot_write_to_disk(tmp_path):
    """Segunda ronda de revisión: numpy da acceso al disco sin introspección (np.savetxt); el hijo corre sin escritura."""
    target = tmp_path / "escrito.txt"
    v = PEPVerifier(n=2, mode="match")
    code = f"import numpy as np\ndef schedule(n):\n    np.savetxt({str(target)!r}, [1.0])\n    return [1.4142, 1.8768][:n]"
    o = v.verify(v.target(), code)
    if v.sandboxed:
        assert not target.exists() and o.outcome_label == "INVALID_SCHEDULE" and o.raw["error"] == "PermissionError"


# --------------------------------------------------------------------------- V_I (sin Isabelle)

def test_isabelle_parse_distinguishes_invariant_and_variant():
    p = IsabelleVerifier.parse(IsabelleVerifier, "INVARIANT: <<< a \\<le> l >>>\nVARIANT: <<< nat n - iter >>>")
    assert p == {"invariant": "a \\<le> l", "variant": "nat n - iter"}
    # el cierre pegado a un símbolo que termina en '>' no debe comerse ese '>'
    q = IsabelleVerifier.parse(IsabelleVerifier, "INVARIANT: <<<x \\<le> \\<lceil>y\\<rceil>>>>\nVARIANT: <<<nat \\<lceil>z\\<rceil>>>>")
    assert q == {"invariant": "x \\<le> \\<lceil>y\\<rceil>", "variant": "nat \\<lceil>z\\<rceil>"}
    # «\\<rceil>>>»: el modelo escribió tres '>' en total; el símbolo quedaría sin cerrar y se repara
    r = IsabelleVerifier.parse(IsabelleVerifier, "INVARIANT: <<<True>>>\nVARIANT: <<<nat \\<lceil>z\\<rceil>>>")
    assert r["variant"] == "nat \\<lceil>z\\<rceil>"


def test_annotation_allowlist():
    assert check_annotation("fl = f l \\<and> a \\<le> l \\<and> (\\<exists>c::real. f c = 0 \\<and> c \\<in> {l..u})") is None
    assert check_annotation("nat \\<lceil>log 2 ((b - a) / tol)\\<rceil> - iter") is None
    for s, lab in [('True" od', "STATEMENT_DRIFT"), ("x __CONCL__", "STATEMENT_DRIFT"), ("a (* b", "STATEMENT_DRIFT"),
                   ("iter := 1", "STATEMENT_DRIFT"), ("a; b", "STATEMENT_DRIFT"), ("\\<open>x\\<close>", "STATEMENT_DRIFT"),
                   ("x \\<le> y \\<and> sorry", "UNSOUND"), ("x \\<Rightarrow> y", "INVALID_PROPOSAL"), ("x ∧ y", "INVALID_PROPOSAL")]:
        assert check_annotation(s)[0] == lab, s


@pytest.mark.skipif(not HAS_ISABELLE, reason="sin Isabelle2025")
def test_isabelle_rejects_before_building():
    v = IsabelleVerifier("bisection")
    t = v.target()
    assert v.verify(t, {"invariant": "", "variant": "1"}).outcome_label == "INVALID_PROPOSAL"
    assert v.verify(t, {"invariant": "True", "variant": "sorry"}).outcome_label == "UNSOUND"
    # salir del hueco (cerrar la cadena del programa, cerrar el bucle) = cambiar la pregunta
    assert v.verify(t, {"invariant": 'True" od', "variant": "1"}).outcome_label == "STATEMENT_DRIFT"
    assert v.verify(t, {"invariant": "True", "variant": "1 do skip od"}).outcome_label == "STATEMENT_DRIFT"
    assert v.verify(t, {"invariant": 'True" od', "variant": ""}).outcome_label == "STATEMENT_DRIFT"  # la deriva va antes que lo demás
    assert v.verify(t, {"invariant": "x __FIXES__", "variant": "1"}).outcome_label == "STATEMENT_DRIFT"
    assert v.verify({**t, "hash": "otro"}, {"invariant": "True", "variant": "1"}).outcome_label == "STATEMENT_DRIFT"


def test_isabelle_one_liner_requires_finished_preplay():
    class V:  # imita VCResult de 08
        try0, try0_ms, sh_found, sh_ms = None, 0, True, 1000
        sh_messages = ["vampire found a proof..."]
    ok, late, failed = V(), V(), V()
    ok.sh_message = "Try this: by (smt (verit) foo) (12 ms)"
    late.sh_message = "Try this: by (metis foo) (> 1.0 s, timed out)"
    failed.sh_message = "Try this: by (metis foo) (failed)"
    assert IsabelleVerifier.one_liner(ok) == ("by (smt (verit) foo)", "sledgehammer", "vampire", 1000)
    assert IsabelleVerifier.one_liner(late) is None and IsabelleVerifier.one_liner(failed) is None


# --------------------------------------------------------------------------- V_I (con Isabelle, lentos)

@pytest.mark.isabelle
@pytest.mark.skipif(not HAS_ISABELLE, reason="sin Isabelle2025")
def test_isabelle_countdown_end_to_end(tmp_path):
    v = IsabelleVerifier("countdown")
    t = v.target()
    ok = v.verify(t, {"invariant": "\\<exists>k. i + k = n", "variant": "i"})
    assert ok.outcome_label == "ACCEPTED" and ok.raw["final"]["oracles"] == [] and ok.raw["same_program"] == "ok"
    assert "countdown_ref" in ok.raw["final"]["prop"]  # el teorema aceptado es sobre el programa congelado
    assert v.verify(t, {"invariant": "i \\<le> n", "variant": "n"}).outcome_label == "VC_OPEN"  # el variante no decrece
    assert v.verify(t, {"invariant": "i \\<le>", "variant": "i"}).outcome_label == "VCG_FAILED"  # no se analiza (etapa 0)
    cheat = v.assemble("\\<exists>k. i + k = n", "i", ["by (tactic \\<open>Skip_Proof.cheat_tac @{context} 1\\<close>)"], tmp_path / "cheat")
    assert cheat["rc"] == 0 and cheat["skip_proof"] and "Pure.skip_proof" in cheat["oracles"]


@pytest.mark.isabelle
@pytest.mark.skipif(not HAS_ISABELLE, reason="sin Isabelle2025")
def test_isabelle_stage0_detects_a_changed_program():
    """La etapa 0 debe distinguir «solo cambian las anotaciones» de «cambió el programa»."""
    v = IsabelleVerifier("bisection")
    assert v.same_program(v.spec["paper_invariant"], v.spec["paper_variant"])[0] == "ok"
    v.program_cmd = v.program_cmd.replace("iter := iter + 1", "iter := iter + 2")  # simula un programa alterado
    assert v.same_program(v.spec["paper_invariant"], v.spec["paper_variant"])[0] == "drift"


LUNA_VI = Path(__file__).resolve().parent.parent / "runs" / "bisection_isabelle" / "20260923-155924-gpt-6-luna-high" / "attempts.jsonl"


@pytest.mark.skipif(not LUNA_VI.exists(), reason="sin los datos de la corrida de V_I")
def test_vc_kind_matches_manual_recount():
    """Recuento manual de la segunda revisión: la clasificación debe mirar premisas y variante, no solo la conclusión."""
    from collections import Counter
    from unirl.report import vc_kind
    tot, rows = Counter(), {}
    for line in LUNA_VI.read_text().splitlines():
        r = json.loads(line)
        c = Counter(vc_kind(v["goal"], r["proposal"]["variant"]) for v in r["raw"]["vcs"] if not v["closed_by"])
        tot += c
        rows[(r["episode"], r["step"])] = dict(c)
    assert dict(tot) == {"invariante": 50, "variante": 30, "postcondición": 21}
    assert rows[(3, 1)] == {"invariante": 4, "variante": 4, "postcondición": 2}
    assert rows[(3, 2)] == {"invariante": 4, "postcondición": 4}
    assert rows[(2, 3)] == {"invariante": 6, "postcondición": 2}


def test_lemma_filter():
    ok = 'lemma half_log: "0 < x \\<Longrightarrow> log 2 (x / 2) = log 2 x - 1"\n  by (simp add: log_divide)'
    assert check_lemmas(ok) is None
    assert check_lemmas('lemma x [simp]: "end = 1" proof - show ?thesis by simp qed') is None  # palabras entre comillas no cuentan
    assert check_lemmas('lemma x: "True" (* (* anidado " *) sigue *) by simp') is None  # comentarios anidados como en Isabelle
    assert check_lemmas('lemma x: "length [] = 0" by (simp add: List.length_0_conv)') is None  # identificadores largos legítimos
    for text, lab in [('lemma x: "True" sorry', "UNSOUND"), ('lemma x: "True" by simp\naxiomatization where ax: "False"', "UNSOUND"),
                      ('end\nlemma x: "True" by simp', "STATEMENT_DRIFT"), ('lemma x: "True" by (tactic \\<open>all_tac\\<close>)', "STATEMENT_DRIFT"),
                      ('notation plus (infixl "*" 70)\nlemma x: "True" by simp', "STATEMENT_DRIFT"), ('declare [[quick_and_dirty]]', "STATEMENT_DRIFT"),
                      ('lemma x: "a __CONCL__" by simp', "STATEMENT_DRIFT"), ('definition g where "g = 1"', "INVALID_PROPOSAL"),
                      ('have x: "True" by simp', "INVALID_PROPOSAL"),
                      # revisión adversarial: una comilla dentro de un comentario desincronizaba el filtro anterior
                      ('lemma a: "True" by simp\n(* " *)\nML "File.write (Path.explode \\"/tmp/x\\") \\"\\""\n(* " *)', "STATEMENT_DRIFT"),
                      ('lemma x: "True" by simp\nmethod m = simp', "STATEMENT_DRIFT"),
                      # segunda revisión: «ML.5» es un solo identificador para un filtro ingenuo, pero Isabelle lee ML . 5
                      ('lemma foo: "True" by simp\nML.5', "STATEMENT_DRIFT"), ('lemma foo: "True" by simp\nend.9', "STATEMENT_DRIFT"),
                      ('lemma foo: "True" by simp\nML._x', "STATEMENT_DRIFT"), ("lemma foo: \"True\" by simp\nML.'a", "STATEMENT_DRIFT"),
                      ('lemma foo: "True" by simp\naxiomatization.0 where c: "False"', "UNSOUND"),
                      ('lemma x: "True" \\<comment> \\<open>c\\<close> by simp', "STATEMENT_DRIFT")]:
        assert check_lemmas(text)[0] == lab, text


def test_lemmas_only_parsed_when_allowed():
    text = 'INVARIANT: <<<True>>>\nVARIANT: <<<iter>>>\nLEMMAS: <<<lemma a: "True" by simp>>>'
    assert "lemmas" not in IsabelleVerifier.parse(IsabelleVerifier("countdown"), text)
    assert IsabelleVerifier.parse(IsabelleVerifier("countdown", allow_lemmas=True), text)["lemmas"] == 'lemma a: "True" by simp'


@pytest.mark.isabelle
@pytest.mark.skipif(not HAS_ISABELLE, reason="sin Isabelle2025")
def test_isabelle_lemma_action_countdown():
    v = IsabelleVerifier("countdown", allow_lemmas=True)
    t = v.target()
    ok = v.verify(t, {"invariant": "\\<exists>k. i + k = n", "variant": "i",
                      "lemmas": 'lemma aux_add:\n  fixes x y :: nat\n  shows "x + y = y + x"\n  by simp'})
    assert ok.outcome_label == "ACCEPTED" and ok.raw["final"]["prop_ok"] and ok.raw["final"]["axioms_ok"]
    bad = v.verify(t, {"invariant": "\\<exists>k. i + k = n", "variant": "i",
                       "lemmas": 'lemma falso:\n  fixes x :: nat\n  shows "x = x + 1"\n  by simp'})
    assert bad.outcome_label == "LEMMA_FAILED" and bad.raw["errors"]


class RecordingProvider(ScriptedProvider):
    def __init__(self, answers):
        super().__init__(answers)
        self.prompts = []

    def complete(self, system, user):
        self.prompts.append(user)
        return super().complete(system, user)


def test_memory_carries_episode_summaries(tmp_path):
    from unirl.loop import Memory
    v = LemmaGraphVerifier("04_newton")
    chain = topological_chain(v)
    bad = json.dumps({"steps": chain[::-1]})
    prov = RecordingProvider([bad, bad, json.dumps({"steps": chain})])
    mem = Memory(tmp_path / "mem.json")
    meta = {"env": "t", "judge": v.name, "provider": "mock", "model": "m", "effort": "", "budget": 2, "run": "r"}
    eps = run_episodes(ProofEnv(v, budget=2), prov, 2, tmp_path / "r", meta, verbose=False, memory=mem)
    assert "MEMORIA" not in prov.prompts[0]           # el primer episodio empieza sin memoria
    assert "MEMORIA" in prov.prompts[2] and "Episodio 1" in prov.prompts[2]  # el segundo ve el resumen del primero
    assert eps[1]["accepted"] and json.loads((tmp_path / "mem.json").read_text())["episodes"][0]["episode"] == 1


@pytest.mark.isabelle
@pytest.mark.skipif(not HAS_ISABELLE, reason="sin Isabelle2025")
def test_memory_reuses_verified_lemmas_countdown(tmp_path):
    from unirl.loop import Memory
    v = IsabelleVerifier("countdown", allow_lemmas=True)
    lem = 'lemma swap_add:\n  fixes x y :: nat\n  shows "x + y = y + x"\n  by simp'
    ep1 = f'INVARIANT: <<<i \\<le> n>>>\nVARIANT: <<<n>>>\nLEMMAS: <<<{lem}>>>'          # VC_OPEN, pero el lema se demuestra
    ep2 = 'INVARIANT: <<<\\<exists>k. i + k = n>>>\nVARIANT: <<<i>>>\nLEMMAS: <<< >>>'       # no repite el lema
    prov = RecordingProvider([ep1, ep2])
    mem = Memory(tmp_path / "mem.json")
    meta = {"env": "t", "judge": v.name, "provider": "mock", "model": "m", "effort": "", "budget": 1, "run": "r"}
    eps = run_episodes(ProofEnv(v, budget=1), prov, 2, tmp_path / "r", meta, verbose=False, memory=mem)
    assert "swap_add" in mem.library and "swap_add" in prov.prompts[1]
    assert eps[1]["accepted"]
    last = [json.loads(l) for l in (tmp_path / "r" / "attempts.jsonl").read_text().splitlines()][-1]
    assert last["memory_library"] == ["swap_add"] and last["raw"]["n_lemmas"] == 1  # la biblioteca entró sola


def test_memory_wording_versions(tmp_path):
    from unirl.loop import Memory
    for w, frag in (("v1", "Lemas que Isabelle YA DEMOSTRÓ."), ("v2", "Lemas que TÚ demostraste")):
        m = Memory(tmp_path / f"{w}.json", wording=w)
        m.add_lemmas([{"name": "foo", "text": "lemma foo: True by simp"}])
        assert frag in m.render()
    with pytest.raises(ValueError):
        Memory(None, wording="v3")


def test_memory_render_unchanged_for_program_judge(tmp_path):
    """El texto que ve el proponente en el juez de programa no cambia con la generalización a PEP y teoremas."""
    from unirl.loop import Memory
    m = Memory(tmp_path / "m.json", wording="v1")
    att = [{"accepted": False, "outcome_label": "VC_OPEN", "raw": {"n_closed_auto": 10, "n_vcs": 30}, "proposal": {"invariant": "I", "variant": "V", "lemmas": ""}, "feedback": "fb1"},
           {"accepted": False, "outcome_label": "LEMMA_FAILED", "raw": {"verified_lemmas": []}, "proposal": {"invariant": "I2", "variant": "V2", "lemmas": "x"}, "feedback": "fb2"}]
    m.end_episode(1, att)
    assert "best_extra" not in m.episodes[0]
    expected = ("MEMORIA DE EPISODIOS ANTERIORES (mismo objetivo y mismo juez; viene de tus intentos anteriores):\n"
                '- Episodio 1: mejor intento VC_OPEN, 10/30 VCs cerradas; anotación: {"invariant": "I", "variant": "V"}\n'
                "  Retroalimentación del último intento: fb2")
    assert m.render() == expected


def test_memory_pep_keeps_best_tau(tmp_path):
    from unirl.loop import Memory
    m = Memory(tmp_path / "m.json")
    mk = lambda tau, pc: {"accepted": False, "outcome_label": "NOT_IMPROVED", "partial_credit": pc,
                          "raw": {"tau": tau, "tau_ref": 0.017, "h": [1.5, 1.5]}, "proposal": f"def schedule(n): return [{tau}]", "feedback": "f"}
    m.end_episode(1, [mk(0.03, 0.4), mk(0.018, 0.94), mk(0.02, 0.8)])
    assert "0.0180000" in m.episodes[0]["best_extra"] and "0.018" in m.episodes[0]["best_proposal"]
    assert "τ = 0.0180000" in m.render()


def test_provider_fatal_aborts(tmp_path):
    """Sin créditos: la corrida se detiene en el primer intento en vez de registrar PROVIDER_ERROR hasta el final."""
    from unirl.loop import ProviderFatal, run_episodes
    from unirl.env import ProofEnv
    from unirl.verifiers import LemmaGraphVerifier

    class SinCredito:
        def complete(self, system, user):
            raise RuntimeError("Error code: 429 - insufficient_quota: You have no credits remaining")

    env = ProofEnv(LemmaGraphVerifier("01_biseccion"), budget=4)
    with pytest.raises(ProviderFatal):
        run_episodes(env, SinCredito(), 3, tmp_path, {"env": "t"}, verbose=False)
    assert sum(1 for _ in open(tmp_path / "attempts.jsonl")) == 0
