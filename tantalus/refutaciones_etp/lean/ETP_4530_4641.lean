import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, x ◇ (y ◇ z) = (y ◇ y) ◇ w

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, (x ◇ y) ◇ x = (y ◇ z) ◇ w

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:4530_4641: tabla de operación sobre `Fin 3`. -/
def tabla_4530_4641 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 1, 0 => ⟨0, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 2, 0 => ⟨0, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_4530_4641 : Magma (Fin 3) := ⟨tabla_4530_4641⟩

theorem cumple_A_4530_4641 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_4530_4641 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_4530_4641 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_4530_4641 (h (Fin 3) cumple_A_4530_4641)

#print axioms refuta_4530_4641
