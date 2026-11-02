import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = (x ◇ x) ◇ (y ◇ y)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = (y ◇ ((y ◇ x) ◇ x)) ◇ x

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:154_2530: tabla de operación sobre `Fin 2`. -/
def tabla_154_2530 : Fin 2 → Fin 2 → Fin 2 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_154_2530 : Magma (Fin 2) := ⟨tabla_154_2530⟩

theorem cumple_A_154_2530 : LeyA (Fin 2) := by
  unfold LeyA
  decide

theorem no_cumple_B_154_2530 : ¬ LeyB (Fin 2) := by
  unfold LeyB
  decide

theorem refuta_154_2530 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_154_2530 (h (Fin 2) cumple_A_154_2530)

#print axioms refuta_154_2530
