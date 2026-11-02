import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = ((x ◇ y) ◇ y) ◇ y

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = x ◇ (y ◇ ((z ◇ y) ◇ z))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:264_655: tabla de operación sobre `Fin 3`. -/
def tabla_264_655 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 0, 2 => ⟨1, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨2, by decide⟩
  | 2, 0 => ⟨2, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_264_655 : Magma (Fin 3) := ⟨tabla_264_655⟩

theorem cumple_A_264_655 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_264_655 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_264_655 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_264_655 (h (Fin 3) cumple_A_264_655)

#print axioms refuta_264_655
