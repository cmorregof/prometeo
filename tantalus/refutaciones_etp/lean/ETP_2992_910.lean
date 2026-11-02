import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = ((y ◇ (z ◇ y)) ◇ x) ◇ z

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = y ◇ ((y ◇ x) ◇ (y ◇ y))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:2992_910: tabla de operación sobre `Fin 3`. -/
def tabla_2992_910 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 0, 2 => ⟨1, by decide⟩
  | 1, 0 => ⟨2, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 2, 0 => ⟨1, by decide⟩
  | 2, 1 => ⟨0, by decide⟩
  | 2, 2 => ⟨2, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_2992_910 : Magma (Fin 3) := ⟨tabla_2992_910⟩

theorem cumple_A_2992_910 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_2992_910 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_2992_910 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_2992_910 (h (Fin 3) cumple_A_2992_910)

#print axioms refuta_2992_910
