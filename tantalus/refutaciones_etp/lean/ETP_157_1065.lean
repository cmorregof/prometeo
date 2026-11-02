import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = (x ◇ y) ◇ (x ◇ y)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = x ◇ ((y ◇ (z ◇ z)) ◇ z)

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:157_1065: tabla de operación sobre `Fin 2`. -/
def tabla_157_1065 : Fin 2 → Fin 2 → Fin 2 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨1, by decide⟩
  | 0, 1 => ⟨1, by decide⟩
  | 1, 0 => ⟨0, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_157_1065 : Magma (Fin 2) := ⟨tabla_157_1065⟩

theorem cumple_A_157_1065 : LeyA (Fin 2) := by
  unfold LeyA
  decide

theorem no_cumple_B_157_1065 : ¬ LeyB (Fin 2) := by
  unfold LeyB
  decide

theorem refuta_157_1065 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_157_1065 (h (Fin 2) cumple_A_157_1065)

#print axioms refuta_157_1065
