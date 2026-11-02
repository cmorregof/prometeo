import PortF5.FactsSyntax
import PortF5.Ecuaciones

/- Derivado de teorth/equational_theories, commit 1aec8a7 (ManuallyProved/Equation1661.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


/- Infinite models showing anti-implications 1661 → ⋯ -/

/- Equation1661_not_implies_Equation1657 -/

/-!
  op_1661_1657 is obtained by starting with
          { x - 1    if x and y have the same parity
  x # y = |
          { x + 1    if x and y have opposite parities
  on the integers. This operation satisfies 1661.
  The # operation is truncated to the nonnegatives, and
  "patched up" around zero so as to break equation 1657
  while retaining 1661.
-/
def op_1661_1657 (x : ℕ) (y : ℕ) : ℕ :=
  match x with
  | 0 => if y % 2 = 0 then 0 else 2
  | 1 => if y % 2 = 0 then 1 else 3
  | 2 => if y % 2 = 0 then 2 else 0
  | 3 => if y % 2 = 0 then 4 else 1
  | n + 4 =>
    if x % 2 = y % 2
    then n + 3 else n + 5

/-
  The bulk of the proof is verifying that the patch-up retains equation 1661.
  This has to be done by a case analysis both on the patched cases and the rest
  of the numbers modulo 2. Having the following theorems for manipulating values
  mod 2 makes the proof more readable. We write them as theorems since
  putting them inside the "have" leads to timeouts in the large case analyses.
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
  We prove lemmata about the left (x ⋄ y) and the right ((y ⋄ z) ⋄ y) of
  equation 1661's right-hand side. These will be used in rewrites to avoid simp
  creating extremely large terms in the proof below.
-/

def delta_right_even (n : ℕ) : ℕ :=
  match n with
    | 0 => 5
    | 1 => 7
    | 2 => 5
    | 3 => 7
    | 4 => 5
    | n+5 => if (n + 5) % 2 = 0 then 5 else 7

theorem op_right_even (y : ℕ) : (y + 5) % 2 = 0 → ∀ (x : ℕ), op_1661_1657 (op_1661_1657 (y + 5) x) (y + 5) = y + delta_right_even x := by
    intro y5e x
    have y4o : (y + 4) % 2 = 1 := Nat.succ_mod_two_eq_zero_iff.mp y5e
    have y6o : (y + 6) % 2 = 1 := Nat.succ_mod_two_eq_one_iff.mpr y5e
    match x with
    | 0 | 1 | 2 | 3 | 4 => simp [op_1661_1657,y5e,y4o,y6o,delta_right_even]
    | n+5 =>
      by_cases n5eo : (n + 5) % 2 = 0
      · simp [op_1661_1657, y5e, n5eo, y4o, delta_right_even]
      · simp [op_1661_1657, y5e, y6o, Nat.mod_two_ne_zero.mp n5eo, delta_right_even]

def delta_right_odd (n : ℕ) : ℕ :=
    match n with
    | 0 => 7
    | 1 => 5
    | 2 => 7
    | 3 => 5
    | 4 => 7
    | n+5 => if (n + 5) % 2 = 0 then 7 else 5

theorem op_right_odd (y : ℕ) : (y + 5) % 2 ≠ 0 → ∀ (x : ℕ), op_1661_1657 (op_1661_1657 (y + 5) x) (y + 5) = y + delta_right_odd x := by
    intro y5o x
    have y5o' : (y + 5) % 2 = 1 := by simp_all only [ne_eq, Nat.mod_two_ne_zero]
    have y4e : (y + 4) % 2 = 0 := Nat.succ_mod_two_eq_one_iff.mp y5o'
    have y6e : (y + 6) % 2 = 0 := by omega
    match x with
    | 0 | 1 | 2 | 3 | 4 =>
      simp [op_1661_1657,y5o',y4e,y6e,delta_right_odd]
    | n+5 =>
      by_cases n5eo : (n + 5) % 2 = 0
      · simp [op_1661_1657, y5o', n5eo, y4e, y6e, delta_right_odd]
      · simp [op_1661_1657, y5o', Nat.mod_two_ne_zero.mp n5eo, y4e, delta_right_odd]

theorem op_left_eq (x y : ℕ) : (x + 5) % 2 = (y + 5) % 2 → op_1661_1657 (x + 5) (y + 5) = x + 4 := by
  simp [op_1661_1657]

theorem op_left_ne (x y : ℕ) : ¬ ((x + 5) % 2 = (y + 5) % 2) → op_1661_1657 (x + 5) (y + 5) = x + 6 := by
  simp [op_1661_1657]

theorem op_right_eq (y z : ℕ) : (y + 5) % 2 = (z + 5) % 2 → op_1661_1657 (op_1661_1657 (y + 5) (z + 5)) (y + 5) = y + 5 := by
  intro yz5
  simp [op_1661_1657,yz5, mod_two_ne_down_to _ _ yz5]

theorem op_right_ne (y z : ℕ) : ¬ (y + 5) % 2 = (z + 5) % 2 → op_1661_1657 (op_1661_1657 (y + 5) (z + 5)) (y + 5) = y + 7 := by
  intro yz5
  simp [op_1661_1657, yz5]
  have r : (y + 5) % 2 = (y + 5) % 2 := by simp
  exact (mod_two_ne_up_from _ _ r)


/-
  Now we're ready to prove that 1661 holds in the magma constructed above.
  This has to be done by a case analysis both on the patched cases and the rest of
  the numbers modulo 2. Most of this is routine w/ the lemmata proven above. The cases
  that require some care are the ones that involve two non-exceptional numbers and one exceptional
  number. These are handled at the end.

  Keep in mind that the exceptional numbers are 0,1,2,3,4, not just the 0,1,2,3
  that we match on.
-/


theorem op_1661_1657_satisfies_1661 :
  ∀ x y z : ℕ, x = op_1661_1657 (op_1661_1657 x y) (op_1661_1657 (op_1661_1657 y z) y) := by
  intro xo yo zo
  match xo,yo,zo with
  | 0, 0, 0 | 0, 0, 1 | 0, 0, 2 | 0, 0, 3 | 0, 0, 4
  | 0, 1, 0 | 0, 1, 1 | 0, 1, 2 | 0, 1, 3 | 0, 1, 4
  | 0, 2, 0 | 0, 2, 1 | 0, 2, 2 | 0, 2, 3 | 0, 2, 4
  | 0, 3, 0 | 0, 3, 1 | 0, 3, 2 | 0, 3, 3 | 0, 3, 4
  | 0, 4, 0 | 0, 4, 1 | 0, 4, 2 | 0, 4, 3 | 0, 4, 4
  | 1, 0, 0 | 1, 0, 1 | 1, 0, 2 | 1, 0, 3 | 1, 0, 4
  | 1, 1, 0 | 1, 1, 1 | 1, 1, 2 | 1, 1, 3 | 1, 1, 4
  | 1, 2, 0 | 1, 2, 1 | 1, 2, 2 | 1, 2, 3 | 1, 2, 4
  | 1, 3, 0 | 1, 3, 1 | 1, 3, 2 | 1, 3, 3 | 1, 3, 4
  | 1, 4, 0 | 1, 4, 1 | 1, 4, 2 | 1, 4, 3 | 1, 4, 4
  | 2, 0, 0 | 2, 0, 1 | 2, 0, 2 | 2, 0, 3 | 2, 0, 4
  | 2, 1, 0 | 2, 1, 1 | 2, 1, 2 | 2, 1, 3 | 2, 1, 4
  | 2, 2, 0 | 2, 2, 1 | 2, 2, 2 | 2, 2, 3 | 2, 2, 4
  | 2, 3, 0 | 2, 3, 1 | 2, 3, 2 | 2, 3, 3 | 2, 3, 4
  | 2, 4, 0 | 2, 4, 1 | 2, 4, 2 | 2, 4, 3 | 2, 4, 4
  | 3, 0, 0 | 3, 0, 1 | 3, 0, 2 | 3, 0, 3 | 3, 0, 4
  | 3, 1, 0 | 3, 1, 1 | 3, 1, 2 | 3, 1, 3 | 3, 1, 4
  | 3, 2, 0 | 3, 2, 1 | 3, 2, 2 | 3, 2, 3 | 3, 2, 4
  | 3, 3, 0 | 3, 3, 1 | 3, 3, 2 | 3, 3, 3 | 3, 3, 4
  | 3, 4, 0 | 3, 4, 1 | 3, 4, 2 | 3, 4, 3 | 3, 4, 4
  | 4, 0, 0 | 4, 0, 1 | 4, 0, 2 | 4, 0, 3 | 4, 0, 4
  | 4, 1, 0 | 4, 1, 1 | 4, 1, 2 | 4, 1, 3 | 4, 1, 4
  | 4, 2, 0 | 4, 2, 1 | 4, 2, 2 | 4, 2, 3 | 4, 2, 4
  | 4, 3, 0 | 4, 3, 1 | 4, 3, 2 | 4, 3, 3 | 4, 3, 4
  | 4, 4, 0 | 4, 4, 1 | 4, 4, 2 | 4, 4, 3 | 4, 4, 4 =>
    simp [op_1661_1657]

  | x+5, 0, 0 | x+5, 0, 1 | x+5, 0, 2 | x+5, 0, 3 | x+5, 0, 4
  | x+5, 1, 0 | x+5, 1, 1 | x+5, 1, 2 | x+5, 1, 3 | x+5, 1, 4
  | x+5, 2, 0 | x+5, 2, 1 | x+5, 2, 2 | x+5, 2, 3 | x+5, 2, 4
  | x+5, 3, 0 | x+5, 3, 1 | x+5, 3, 2 | x+5, 3, 3 | x+5, 3, 4
  | x+5, 4, 0 | x+5, 4, 1 | x+5, 4, 2 | x+5, 4, 3 | x+5, 4, 4
  | 0, x+5, 0 | 0, x+5, 1 | 0, x+5, 2 | 0, x+5, 3 | 0, x+5, 4
  | 1, x+5, 0 | 1, x+5, 1 | 1, x+5, 2 | 1, x+5, 3 | 1, x+5, 4
  | 2, x+5, 0 | 2, x+5, 1 | 2, x+5, 2 | 2, x+5, 3 | 2, x+5, 4
  | 3, x+5, 0 | 3, x+5, 1 | 3, x+5, 2 | 3, x+5, 3 | 3, x+5, 4
  | 4, x+5, 0 | 4, x+5, 1 | 4, x+5, 2 | 4, x+5, 3 | 4, x+5, 4
  | 0, 0, x+5 | 0, 1, x+5 | 0, 2, x+5 | 0, 3, x+5 | 0, 4, x+5
  | 1, 0, x+5 | 1, 1, x+5 | 1, 2, x+5 | 1, 3, x+5 | 1, 4, x+5
  | 2, 0, x+5 | 2, 1, x+5 | 2, 2, x+5 | 2, 3, x+5 | 2, 4, x+5
  | 3, 0, x+5 | 3, 1, x+5 | 3, 2, x+5 | 3, 3, x+5 | 3, 4, x+5
  | 4, 0, x+5 | 4, 1, x+5 | 4, 2, x+5 | 4, 3, x+5 | 4, 4, x+5 =>
    simp [op_1661_1657]
    by_cases hx5 : (x + 5) % 2 = 0
    · have hx4 : (x + 4) % 2 = 1 := mod_two_pred_0_1_to _ hx5
      have hx6 : (x + 6) % 2 = 1 := mod_two_succ_0_1_from _ hx5
      have hx7 : (x + 7) % 2 = 0 := mod_two_succ_1_0_from _ hx6
      simp [hx4, hx5, hx6, hx7]
    · have hx5' : (x + 5) % 2 = 1 := Nat.mod_two_ne_zero.mp hx5
      have hx4' : (x + 4) % 2 = 0 := mod_two_pred_1_0_to _ hx5'
      have hx6' : (x + 6) % 2 = 0 := mod_two_succ_1_0_from _ hx5'
      have hx7' : (x + 7) % 2 = 1 := mod_two_succ_0_1_from _ hx6'
      simp [hx4', hx5', hx6', hx7']

  | x+5, y+5, z+5 =>
    by_cases hyz5 : (y + 5) % 2 = (z + 5) % 2
    · rw [op_right_eq y z hyz5]
      by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
      · rw [op_left_eq x y hxy5]
        have hxy4 : ¬ (x + 4) % 2 = (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy4]
      · rw [op_left_ne x y hxy5]
        have hxy6 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        simp [op_1661_1657,hxy6]
    · rw [op_right_ne y z hyz5]
      by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
      · rw [op_left_eq x y hxy5]
        have hxy45 : (x + 4) % 2 ≠ (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        have hxy46 : (y + 6) % 2 = (x + 4) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy45)
        have hxy43 : ¬ (x + 4) % 2 = (y + 7) % 2 := Ne.symm (mod_two_ne_up_from _ _ hxy46)
        simp [op_1661_1657,hxy43]
      · rw [op_left_ne x y hxy5]
        simp [op_1661_1657,]
        have hxy56 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        have hxy6 : (y + 6) % 2 ≠ (x + 6) % 2 := mod_two_ne_up_from _ _ hxy56.symm
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy6).symm
        simp [op_1661_1657,hxy67]

  | x+5, y+5, 0 =>  -- also 2,4
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · rw [op_left_eq x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 0]
        simp only [delta_right_even]
        have hxy45 : ¬ (x + 4) % 2 = (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy45]
      · rw [op_right_odd y h5 0]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy5.symm
        have hxy57 : (x + 5) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy56).symm
        have hxy47 : ¬ (x + 4) % 2 = (y + 7) % 2 := mod_two_ne_down_to _ _ hxy57
        simp [op_1661_1657,hxy47]
    · rw [op_left_ne x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 0]
        simp only [delta_right_even]
        have hxy65 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        rw [op_left_eq (x+1) y]
        exact hxy65
      · rw [op_right_odd y h5 0]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 = (x + 5) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy5)
        have hxy57 : (y + 7) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy56
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy57)
        simp [op_1661_1657,hxy67]

  | x+5, y+5, 2 =>  -- also 0,4
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · rw [op_left_eq x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 2]
        simp only [delta_right_even]
        have hxy45 : ¬ (x + 4) % 2 = (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy45]
      · rw [op_right_odd y h5 2]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy5.symm
        have hxy57 : (x + 5) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy56).symm
        have hxy47 : ¬ (x + 4) % 2 = (y + 7) % 2 := mod_two_ne_down_to _ _ hxy57
        simp [op_1661_1657,hxy47]
    · rw [op_left_ne x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 2]
        simp only [delta_right_even]
        have hxy65 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        rw [op_left_eq (x+1) y]
        exact hxy65
      · rw [op_right_odd y h5 2]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 = (x + 5) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy5)
        have hxy57 : (y + 7) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy56
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy57)
        simp [op_1661_1657,hxy67]

  | x+5, y+5, 4 =>  -- also 0,2
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · rw [op_left_eq x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 4]
        simp only [delta_right_even]
        have hxy45 : ¬ (x + 4) % 2 = (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy45]
      · rw [op_right_odd y h5 4]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy5.symm
        have hxy57 : (x + 5) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy56).symm
        have hxy47 : ¬ (x + 4) % 2 = (y + 7) % 2 := mod_two_ne_down_to _ _ hxy57
        simp [op_1661_1657,hxy47]
    · rw [op_left_ne x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 4]
        simp only [delta_right_even]
        have hxy65 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        rw [op_left_eq (x+1) y]
        exact hxy65
      · rw [op_right_odd y h5 4]
        simp only [delta_right_odd]
        have hxy56 : (y + 6) % 2 = (x + 5) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy5)
        have hxy57 : (y + 7) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy56
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy57)
        simp [op_1661_1657,hxy67]

  | x+5, y+5, 1 =>  -- also 3
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · rw [op_left_eq x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 1]
        simp only [delta_right_even]
        have hxy56 : (y + 6) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy5.symm
        have hxy57 : (x + 5) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy56).symm
        have hxy47 : ¬ (x + 4) % 2 = (y + 7) % 2 := mod_two_ne_down_to _ _ hxy57
        simp [op_1661_1657,hxy47]
      · rw [op_right_odd y h5 1]
        simp only [delta_right_odd]
        have hxy45 : (x + 4) % 2 ≠ (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy5,hxy45]
    · rw [op_left_ne x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 1]
        simp only [delta_right_even]
        have hxy56 : (y + 6) % 2 = (x + 5) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy5)
        have hxy57 : (y + 7) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy56
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy57)
        rw [op_left_eq (x+1) (y+2) hxy67]
      · rw [op_right_odd y h5 1]
        simp only [delta_right_odd]
        have hxy56 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        simp [op_1661_1657,hxy56]

  | x+5, y+5, 3 =>  -- also 1
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · rw [op_left_eq x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 3]
        simp only [delta_right_even]
        have hxy56 : (y + 6) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy5.symm
        have hxy57 : (x + 5) % 2 = (y + 7) % 2 := (mod_two_eq_up_from _ _ hxy56).symm
        have hxy47 : ¬ (x + 4) % 2 = (y + 7) % 2 := mod_two_ne_down_to _ _ hxy57
        simp [op_1661_1657,hxy47]
      · rw [op_right_odd y h5 3]
        simp only [delta_right_odd]
        have hxy45 : (x + 4) % 2 ≠ (y + 5) % 2 := mod_two_ne_down_to _ _ hxy5
        simp [op_1661_1657,hxy5,hxy45]
    · rw [op_left_ne x y hxy5]
      by_cases h5 : (y + 5) % 2 = 0
      · rw [op_right_even y h5 3]
        simp only [delta_right_even]
        have hxy56 : (y + 6) % 2 = (x + 5) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy5)
        have hxy57 : (y + 7) % 2 ≠ (x + 5) % 2 := mod_two_ne_up_from _ _ hxy56
        have hxy67 : (x + 6) % 2 = (y + 7) % 2 := mod_two_eq_up_from _ _ (Ne.symm hxy57)
        rw [op_left_eq (x+1) (y+2) hxy67]
      · rw [op_right_odd y h5 3]
        simp only [delta_right_odd]
        have hxy56 : (x + 6) % 2 = (y + 5) % 2 := mod_two_eq_up_from _ _ hxy5
        simp [op_1661_1657,hxy56]

  | x+5, 0, y+5 | x+5, 1, y+5 | x+5, 2, y+5 | x+5, 3, y+5 | x+5, 4, y+5 =>
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · by_cases h5y: (y + 5) % 2 = 0
      · have h5x : (x + 5) % 2 = 0 := hxy5 ▸ h5y
        have h4x : (x + 4) % 2 = 1 := mod_two_pred_0_1_to _ h5x
        have h6x : (x + 6) % 2 = 1 := mod_two_succ_0_1_from _ h5x
        simp [op_1661_1657,h5y]
        simp [h4x,h5x,h6x]
      · have h5y' : (y + 5) % 2 = 1 := Nat.mod_two_ne_zero.mp h5y
        have h5x : (x + 5) % 2 = 1 := hxy5 ▸ h5y'
        have h4x : (x + 4) % 2 = 0 := mod_two_pred_1_0_to _ h5x
        have h6x : (x + 6) % 2 = 0 := mod_two_succ_1_0_from _ h5x
        simp [op_1661_1657,h5y',h4x,h5x,h6x]
    · by_cases h5y: (y + 5) % 2 = 0
      · have h5x : (x + 5) % 2 = 1 := by simp_all only [Nat.mod_two_ne_zero]
        have h4x : (x + 4) % 2 = 0 := mod_two_pred_1_0_to _ h5x
        have h6x : (x + 6) % 2 = 0 := mod_two_succ_1_0_from _ h5x
        simp [op_1661_1657,h5y,h4x,h5x,h6x]
      · have h5y' : (y + 5) % 2 = 1 := Nat.mod_two_ne_zero.mp h5y
        have h5x : (x + 5) % 2 = 0 := by simp_all only [Nat.mod_two_ne_one]
        have h4x : (x + 4) % 2 = 1 := mod_two_pred_0_1_to _ h5x
        have h6x : (x + 6) % 2 = 1 := mod_two_succ_0_1_from _ h5x
        simp [op_1661_1657,h5y',h4x,h5x,h6x]

  | 0, x+5, y+5 | 1, x+5, y+5 | 2, x+5, y+5 | 3, x+5, y+5 | 4, x+5, y+5 =>
    by_cases hxy5 : (x + 5) % 2 = (y + 5) % 2
    · try {rw [op_left_eq x y hxy5]}
      by_cases h5y : (y + 5) % 2 = 0
      · have h5x : (x + 5) % 2 = 0 := hxy5 ▸ h5y
        have h4x : (x + 4) % 2 = 1 := mod_two_pred_0_1_to _ h5x
        simp [op_1661_1657,h4x,h5x,h5y]
      · have h5y' : (y + 5) % 2 = 1 := Nat.mod_two_ne_zero.mp h5y
        have h5x : (x + 5) % 2 = 1 := hxy5 ▸ h5y'
        have h4x : (x + 4) % 2 = 0 := mod_two_pred_1_0_to _ h5x
        simp [op_1661_1657,h5x,h5y',h4x]
    · rw [op_left_ne x y hxy5]
      by_cases h5y : (y + 5) % 2 = 0
      · have h5x : (x + 5) % 2 = 1 := by simp_all only [Nat.mod_two_ne_zero]
        have h6x : (x + 6) % 2 = 0 := mod_two_succ_1_0_from _ h5x
        have h7x : (x + 7) % 2 = 1 := mod_two_succ_0_1_from _ h6x
        simp [op_1661_1657,h5x,h6x,h7x]
      · have h5y' : (y + 5) % 2 = 1 := Nat.mod_two_ne_zero.mp h5y
        have h5x : (x + 5) % 2 = 0 := by simp_all only [Nat.mod_two_ne_one]
        have h6x : (x + 6) % 2 = 1 := mod_two_succ_0_1_from (x + 5) h5x
        have h7x : (x + 7) % 2 = 0 := mod_two_succ_1_0_from (x + 6) h6x
        simp [op_1661_1657,h5x,h6x,h7x]

end ETP
