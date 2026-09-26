theory Driver
  imports "Numerical_Methods_Paper.Bisection"
begin



context
  fixes f :: "real \<Rightarrow> real" and a b tol :: real
  assumes postive_tolerance: "0 < tol"
    and sufficiently_small_tol: "tol < b-a"
    and continuous_f: "continuous_on {a..b} f"
    and opposite_signs: "f(a)*f(b)<0"
begin

lemma a_less_than_b: "a < b" using postive_tolerance sufficiently_small_tol by auto
lemma ln2_g_0 [simp]: "\<lceil>log 2 ((b - a) / tol)\<rceil> > 0" using sufficiently_small_tol postive_tolerance by force
lemma log_pos [simp]: "0 < log 2 ((b - a) / tol)" using ln2_g_0 zero_less_ceiling by simp


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
  val out_path = Path.explode "/Users/cmorregof/isabelle/scratch/driver-1790194055-19878/result.json"
  val sh_timeout = 15
  val try0_timeout = 5
  val concl = @{prop \<open>H[True] bisection(f,a,b,tol) [\<exists> c::real. f(c) = 0 \<and> c \<in> {a<..<b} \<and> u-l \<le> tol \<and> \<bar>c-xmid\<bar> \<le> (b-a)/2^iter \<and> \<bar>c-xmid\<bar> \<le> tol \<and> iter = \<lceil>log 2 ((b-a) / tol)\<rceil>]\<close>}

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

  val only = [4, 8, 9, 10] : int list
  val given = [(4, Input.string_of \<open>(smt (verit, del_insts) Groups.add_ac(2) a_less_than_b divide_divide_eq_right divide_pos_pos frac_le le_diff_conv less_log_of_power linear linorder_not_le nonzero_mult_div_cancel_left not_less_eq_eq of_nat_Suc of_nat_add of_nat_diff of_nat_le_iff order_le_less postive_tolerance real_nat_ceiling_ge)\<close>), (8, Input.string_of \<open>(smt (verit, del_insts) Groups.add_ac(2) a_less_than_b divide_divide_eq_right divide_pos_pos frac_le le_diff_conv less_log_of_power linear linorder_not_le nonzero_mult_div_cancel_left not_less_eq_eq of_nat_Suc of_nat_add of_nat_diff of_nat_le_iff order_le_less postive_tolerance real_nat_ceiling_ge)\<close>), (9, Input.string_of \<open>(smt (verit, del_insts) Groups.add_ac(2) a_less_than_b divide_divide_eq_right divide_pos_pos frac_le le_diff_conv less_log_of_power linear linorder_not_le nonzero_mult_div_cancel_left not_less_eq_eq of_nat_Suc of_nat_add of_nat_diff of_nat_le_iff order_le_less postive_tolerance real_nat_ceiling_ge)\<close>), (10, Input.string_of \<open>(smt (verit, del_insts) Groups.add_ac(2) a_less_than_b divide_divide_eq_right divide_pos_pos frac_le le_diff_conv less_log_of_power linear linorder_not_le nonzero_mult_div_cancel_left not_less_eq_eq of_nat_Suc of_nat_add of_nat_diff of_nat_le_iff order_le_less postive_tolerance real_nat_ceiling_ge)\<close>)] : (int * string) list  (* (índice, método) *)
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


end

end
