import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = x ◇ (x ◇ y)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = x ◇ ((x ◇ (y ◇ x)) ◇ y)

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:9_1026: tabla de operación sobre `Fin 4`. -/
def tabla_9_1026 : Fin 4 → Fin 4 → Fin 4 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 0, 3 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 1, 3 => ⟨0, by decide⟩
  | 2, 0 => ⟨1, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨2, by decide⟩
  | 2, 3 => ⟨1, by decide⟩
  | 3, 0 => ⟨1, by decide⟩
  | 3, 1 => ⟨3, by decide⟩
  | 3, 2 => ⟨3, by decide⟩
  | 3, 3 => ⟨3, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_9_1026 : Magma (Fin 4) := ⟨tabla_9_1026⟩

theorem cumple_A_9_1026 : LeyA (Fin 4) := by
  unfold LeyA
  decide

theorem no_cumple_B_9_1026 : ¬ LeyB (Fin 4) := by
  unfold LeyB
  decide

theorem refuta_9_1026 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_9_1026 (h (Fin 4) cumple_A_9_1026)

#print axioms refuta_9_1026
