import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, x = (((x ◇ y) ◇ z) ◇ x) ◇ w

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x : G, x = (x ◇ (x ◇ x)) ◇ (x ◇ x)

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:3088_1832: tabla de operación sobre `Fin 4`. -/
def tabla_3088_1832 : Fin 4 → Fin 4 → Fin 4 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨1, by decide⟩
  | 0, 1 => ⟨1, by decide⟩
  | 0, 2 => ⟨1, by decide⟩
  | 0, 3 => ⟨1, by decide⟩
  | 1, 0 => ⟨2, by decide⟩
  | 1, 1 => ⟨2, by decide⟩
  | 1, 2 => ⟨2, by decide⟩
  | 1, 3 => ⟨2, by decide⟩
  | 2, 0 => ⟨3, by decide⟩
  | 2, 1 => ⟨3, by decide⟩
  | 2, 2 => ⟨3, by decide⟩
  | 2, 3 => ⟨3, by decide⟩
  | 3, 0 => ⟨0, by decide⟩
  | 3, 1 => ⟨0, by decide⟩
  | 3, 2 => ⟨0, by decide⟩
  | 3, 3 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_3088_1832 : Magma (Fin 4) := ⟨tabla_3088_1832⟩

theorem cumple_A_3088_1832 : LeyA (Fin 4) := by
  unfold LeyA
  decide

theorem no_cumple_B_3088_1832 : ¬ LeyB (Fin 4) := by
  unfold LeyB
  decide

theorem refuta_3088_1832 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_3088_1832 (h (Fin 4) cumple_A_3088_1832)

#print axioms refuta_3088_1832
