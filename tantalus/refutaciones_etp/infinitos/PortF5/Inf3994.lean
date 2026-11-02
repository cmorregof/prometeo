import PortF5.FactsSyntax
import PortF5.Ecuaciones

/- Derivado de teorth/equational_theories, commit 1aec8a7 (InfModel.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP

theorem Equation3994_not_implies_Equation3588 : ∃ (G : Type) (_ : Magma G), Equation3994 G ∧ ¬Equation3588 G := by
  let magN : Magma ℕ := ⟨fun x y ↦ if Even x ∧ Even y then x ^^^ y else if Even y then y + 2
    else if Even x then x - 2 else 0⟩
  use ℕ, magN
  have range : ∀ x y : ℕ, Even (x ◇ y : ℕ) := by
    intro x y
    unfold magN
    simp
    split_ifs
    · simp_all
    · simpa [Nat.even_add]
    · by_cases x < 2
      · rw [Nat.sub_eq_zero_of_le]
        simp
        omega
      rw [Nat.even_sub]
      · simp_all
      · omega
    · exact .zero
  constructor
  · intro x y z
    generalize h : x ◇ y = v
    have : Even v := by rw [← h]; apply range
    unfold magN
    by_cases hz : Even z
    · simp [this, hz, Nat.xor_comm]
    · simp [hz, this, Nat.even_add]
  simp only [not_forall]
  use 1, 1, 1
  unfold magN
  simp

end ETP
