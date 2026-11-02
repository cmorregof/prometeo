import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, x ◇ (y ◇ z) = (y ◇ w) ◇ w

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, x ◇ (y ◇ z) = (w ◇ z) ◇ w

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:4538_4570: tabla de operación sobre `Fin 5`. -/
def tabla_4538_4570 : Fin 5 → Fin 5 → Fin 5 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨4, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 0, 2 => ⟨3, by decide⟩
  | 0, 3 => ⟨3, by decide⟩
  | 0, 4 => ⟨3, by decide⟩
  | 1, 0 => ⟨4, by decide⟩
  | 1, 1 => ⟨3, by decide⟩
  | 1, 2 => ⟨3, by decide⟩
  | 1, 3 => ⟨3, by decide⟩
  | 1, 4 => ⟨3, by decide⟩
  | 2, 0 => ⟨4, by decide⟩
  | 2, 1 => ⟨3, by decide⟩
  | 2, 2 => ⟨3, by decide⟩
  | 2, 3 => ⟨3, by decide⟩
  | 2, 4 => ⟨3, by decide⟩
  | 3, 0 => ⟨3, by decide⟩
  | 3, 1 => ⟨3, by decide⟩
  | 3, 2 => ⟨3, by decide⟩
  | 3, 3 => ⟨3, by decide⟩
  | 3, 4 => ⟨3, by decide⟩
  | 4, 0 => ⟨3, by decide⟩
  | 4, 1 => ⟨2, by decide⟩
  | 4, 2 => ⟨3, by decide⟩
  | 4, 3 => ⟨3, by decide⟩
  | 4, 4 => ⟨3, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_4538_4570 : Magma (Fin 5) := ⟨tabla_4538_4570⟩

theorem cumple_A_4538_4570 : LeyA (Fin 5) := by
  unfold LeyA
  decide

theorem no_cumple_B_4538_4570 : ¬ LeyB (Fin 5) := by
  unfold LeyB
  decide

theorem refuta_4538_4570 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_4538_4570 (h (Fin 5) cumple_A_4538_4570)

#print axioms refuta_4538_4570
