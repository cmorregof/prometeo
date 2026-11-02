import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = ((x ◇ y) ◇ y) ◇ z

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ y = y ◇ (x ◇ (y ◇ z))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:265_3347: tabla de operación sobre `Fin 2`. -/
def tabla_265_3347 : Fin 2 → Fin 2 → Fin 2 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_265_3347 : Magma (Fin 2) := ⟨tabla_265_3347⟩

theorem cumple_A_265_3347 : LeyA (Fin 2) := by
  unfold LeyA
  decide

theorem no_cumple_B_265_3347 : ¬ LeyB (Fin 2) := by
  unfold LeyB
  decide

theorem refuta_265_3347 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_265_3347 (h (Fin 2) cumple_A_265_3347)

#print axioms refuta_265_3347
