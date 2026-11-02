import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = x ◇ (x ◇ ((x ◇ x) ◇ y))

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ y = (x ◇ z) ◇ (x ◇ z)

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:615_3733: tabla de operación sobre `Fin 3`. -/
def tabla_615_3733 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 2, 0 => ⟨1, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_615_3733 : Magma (Fin 3) := ⟨tabla_615_3733⟩

theorem cumple_A_615_3733 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_615_3733 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_615_3733 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_615_3733 (h (Fin 3) cumple_A_615_3733)

#print axioms refuta_615_3733
