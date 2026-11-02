import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = x ◇ ((y ◇ x) ◇ z)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x ◇ y = (x ◇ (y ◇ y)) ◇ y

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:106_3928: tabla de operación sobre `Fin 4`. -/
def tabla_106_3928 : Fin 4 → Fin 4 → Fin 4 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 0, 3 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 1, 3 => ⟨2, by decide⟩
  | 2, 0 => ⟨2, by decide⟩
  | 2, 1 => ⟨0, by decide⟩
  | 2, 2 => ⟨2, by decide⟩
  | 2, 3 => ⟨2, by decide⟩
  | 3, 0 => ⟨3, by decide⟩
  | 3, 1 => ⟨0, by decide⟩
  | 3, 2 => ⟨3, by decide⟩
  | 3, 3 => ⟨2, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_106_3928 : Magma (Fin 4) := ⟨tabla_106_3928⟩

theorem cumple_A_106_3928 : LeyA (Fin 4) := by
  unfold LeyA
  decide

theorem no_cumple_B_106_3928 : ¬ LeyB (Fin 4) := by
  unfold LeyB
  decide

theorem refuta_106_3928 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_106_3928 (h (Fin 4) cumple_A_106_3928)

#print axioms refuta_106_3928
