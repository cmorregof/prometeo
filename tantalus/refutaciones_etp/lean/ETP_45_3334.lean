import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ y = z ◇ y

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ y = x ◇ (z ◇ (z ◇ y))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:45_3334: tabla de operación sobre `Fin 3`. -/
def tabla_45_3334 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨1, by decide⟩
  | 1, 0 => ⟨0, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | 1, 2 => ⟨1, by decide⟩
  | 2, 0 => ⟨0, by decide⟩
  | 2, 1 => ⟨0, by decide⟩
  | 2, 2 => ⟨1, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_45_3334 : Magma (Fin 3) := ⟨tabla_45_3334⟩

theorem cumple_A_45_3334 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_45_3334 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_45_3334 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_45_3334 (h (Fin 3) cumple_A_45_3334)

#print axioms refuta_45_3334
