import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = (x ◇ y) ◇ (z ◇ y)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = ((y ◇ y) ◇ (z ◇ x)) ◇ z

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:163_2755: tabla de operación sobre `Fin 2`. -/
def tabla_163_2755 : Fin 2 → Fin 2 → Fin 2 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_163_2755 : Magma (Fin 2) := ⟨tabla_163_2755⟩

theorem cumple_A_163_2755 : LeyA (Fin 2) := by
  unfold LeyA
  decide

theorem no_cumple_B_163_2755 : ¬ LeyB (Fin 2) := by
  unfold LeyB
  decide

theorem refuta_163_2755 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_163_2755 (h (Fin 2) cumple_A_163_2755)

#print axioms refuta_163_2755
