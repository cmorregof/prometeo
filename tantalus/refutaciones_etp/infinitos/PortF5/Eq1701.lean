import PortF5.FactsSyntax
import PortF5.Ecuaciones

/- Derivado de teorth/equational_theories, commit 1aec8a7 (ManuallyProved/Equation1701.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


/-
  The proof follows the general strategy set out in InfModel_1701. We start from
  a simple infinite model of 1701, then patch it to break consequents. The bulk is
  showing that the patch construction retains 1701, the counterexamples part is
  immediate. Since this has to be done by a case analysis both on the patched
  cases and the rest of the numbers modulo 2, we use the following mod_two
  lemmata.
-/

theorem mod_two_succ_0_1_from (n : ℕ) : n % 2 = 0 → (n + 1) % 2 = 1 := by omega
theorem mod_two_succ_1_0_from (n : ℕ) : n % 2 = 1 → (n + 1) % 2 = 0 := by omega
theorem mod_two_pred_0_1_to (n : ℕ) : (n + 1) % 2 = 0 → n % 2 = 1 := by omega
theorem mod_two_pred_1_0_to (n : ℕ) : (n + 1) % 2 = 1 → n % 2 = 0 := by omega
theorem mod_two_ne_down_to (n m : ℕ) : (n + 1) % 2 = m % 2 → ¬ n % 2 = m % 2 := by omega
theorem mod_two_eq_down_to (n m : ℕ) : (n + 1) % 2 ≠ m % 2 → n % 2 = m % 2 := by omega
theorem mod_two_ne_up_from (n m : ℕ) : n % 2 = m % 2 → ¬ (n + 1) % 2 = m % 2 := by omega
theorem mod_two_eq_up_from (n m : ℕ) : n % 2 ≠ m % 2 → (n + 1) % 2 = m % 2 := by omega

/-
  The model we start with is the transpose of the original model for 1661.
  Showing that 1701 does not imply 8 is exceedingly simple: we need only truncate,
  not patch further. However, 3253 and 4587 cannot be refuted this way: those have
  to be dealt with in two separate constructions.
-/

def op_1701_8 (x : ℕ) (y : ℕ) : ℕ :=
  match y with
  | 0 => 0
  | n + 1 =>
    if x % 2 = y % 2
    then n else n + 2

/-
  This proof is much nicer than the others in InfModel_1661 and below, since simp here
  does not time out with (deterministic) timeout at `isDefEq`.
  TODO: Write a macro which simplifies this kind of argument.
-/

theorem op_1701_8_satisfies_1701 :
  ∀ (x y z : ℕ), x = op_1701_8 (op_1701_8 y x) (op_1701_8 (op_1701_8 z x) x) := by
  intro xo yo zo
  match xo,yo,zo with
  | x+1, y+1, z+1 =>
    by_cases sx_cong_sz : ((x + 1) % 2 = (z + 1) % 2)
    · by_cases sx_cong_0 : ((x + 1) % 2 = 0)
      · have sz_cong_0 : ((z + 1) % 2 = 0) := by omega
        have x_cong_1 : (x % 2 = 1) := mod_two_pred_0_1_to x sx_cong_0
        have ssx_cong_1 : ((x + 2) % 2 = 1) := mod_two_succ_0_1_from _ sx_cong_0
        by_cases sy_cong_0 : ((y + 1) % 2 = 0)
        · simp [op_1701_8,sx_cong_sz,x_cong_1,sz_cong_0,ssx_cong_1,sy_cong_0]
        · have sy_cong_1 : ((y + 1) % 2 = 1) := Nat.mod_two_ne_zero.mp sy_cong_0
          simp [op_1701_8,sx_cong_sz,x_cong_1,sz_cong_0,ssx_cong_1,sy_cong_1]
      · have sx_cong_1 : (x + 1) % 2 = 1 := by omega
        have sz_cong_1 : (z + 1) % 2 = 1 := by omega
        by_cases sy_cong_0 : ((y + 1) % 2 = 0)
        · simp [op_1701_8, sx_cong_sz, sy_cong_0, sz_cong_1, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from,
              mod_two_pred_0_1_to, mod_two_pred_1_0_to]
        · have sy_cong_1 : (y + 1) % 2 = 1 := by omega
          simp [op_1701_8, sx_cong_sz, sy_cong_1, sz_cong_1, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from, mod_two_pred_0_1_to,
              mod_two_pred_1_0_to]

    · by_cases sx_cong_0 : ((x + 1) % 2 = 0)
      · have sz_cong_1 : ((z + 1) % 2 = 1) := by omega
        by_cases sy_cong_0 : ((y + 1) % 2 = 0)
        · simp [op_1701_8, sx_cong_sz, sx_cong_0, sy_cong_0, sz_cong_1, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from, mod_two_pred_0_1_to,
              mod_two_pred_1_0_to]
        · have sy_cong_1 : ((y + 1) % 2 = 1) := Nat.mod_two_ne_zero.mp sy_cong_0
          simp [op_1701_8, sx_cong_sz, sx_cong_0, sy_cong_1, sz_cong_1, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from, mod_two_pred_0_1_to,
              mod_two_pred_1_0_to]
      · have sx_cong_1 : (x + 1) % 2 = 1 := by omega
        have sz_cong_0 : (z + 1) % 2 = 0 := by omega
        by_cases sy_cong_0 : ((y + 1) % 2 = 0)
        · simp [op_1701_8, sx_cong_sz, sx_cong_1, sy_cong_0, sz_cong_0, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from, mod_two_pred_0_1_to,
              mod_two_pred_1_0_to]
        · have sy_cong_1 : (y + 1) % 2 = 1 := by omega
          simp [op_1701_8, sx_cong_sz, sx_cong_1, sy_cong_1, sz_cong_0, Nat.mod_two_ne_zero,
            mod_two_ne_down_to, mod_two_succ_0_1_from, mod_two_succ_1_0_from, mod_two_pred_0_1_to,
              mod_two_pred_1_0_to]
  | x+1, y+1, 0 | x+1, 0, y+1 | 0, _+1, _+1 =>
    simp [op_1701_8]
    try{
      by_cases sx_cong_0 : (x + 1) % 2 = 0
      · by_cases sy_cong_0 : (y + 1) % 2 = 0
        · simp [sx_cong_0,sy_cong_0,Nat.mod_two_ne_zero,mod_two_ne_down_to,mod_two_succ_0_1_from,
            mod_two_succ_1_0_from,mod_two_pred_0_1_to,mod_two_pred_1_0_to]
        · simp [sx_cong_0,sy_cong_0, Nat.mod_two_ne_zero, mod_two_ne_down_to, mod_two_succ_0_1_from,
            mod_two_succ_1_0_from, mod_two_pred_0_1_to, mod_two_pred_1_0_to]
      · have sx_cong_1 : (x + 1) % 2 = 1 := by omega
        by_cases sy_cong_0 : (y + 1) % 2 = 0
        · simp [sx_cong_1,sy_cong_0
              ,Nat.mod_two_ne_zero,mod_two_ne_down_to
              ,mod_two_succ_0_1_from,mod_two_succ_1_0_from
              ,mod_two_pred_0_1_to,mod_two_pred_1_0_to
              ]
        · have sy_cong_1 : (y + 1) % 2 = 1 := by omega
          simp [sx_cong_1,sy_cong_1
              ,Nat.mod_two_ne_zero,mod_two_ne_down_to
              ,mod_two_succ_0_1_from,mod_two_succ_1_0_from
              ,mod_two_pred_0_1_to,mod_two_pred_1_0_to
              ]
    }
   | x+1, 0, 0 | 0, _+1, 0 | 0, 0, _+1 =>
      simp [op_1701_8]
      try {
        by_cases sx_cong_0 : (x + 1) % 2 = 0
        · simp [sx_cong_0
              ,Nat.mod_two_ne_zero,mod_two_ne_down_to
              ,mod_two_succ_0_1_from,mod_two_succ_1_0_from
              ,mod_two_pred_0_1_to,mod_two_pred_1_0_to
              ]
        · have sx_cong_1 : (x + 1) % 2 = 1 := by omega
          simp [sx_cong_1
              ,Nat.mod_two_ne_zero,mod_two_ne_down_to
              ,mod_two_succ_0_1_from,mod_two_succ_1_0_from
              ,mod_two_pred_0_1_to,mod_two_pred_1_0_to
              ]
      }
   | 0, 0, 0 => simp [op_1701_8]

end ETP
