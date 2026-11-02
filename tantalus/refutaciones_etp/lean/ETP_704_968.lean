import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = y ◇ (y ◇ ((x ◇ x) ◇ y))

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = y ◇ ((z ◇ y) ◇ (z ◇ x))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:704_968: tabla de operación sobre `Fin 5`. -/
def tabla_704_968 : Fin 5 → Fin 5 → Fin 5 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨1, by decide⟩
  | 0, 2 => ⟨2, by decide⟩
  | 0, 3 => ⟨3, by decide⟩
  | 0, 4 => ⟨4, by decide⟩
  | 1, 0 => ⟨2, by decide⟩
  | 1, 1 => ⟨3, by decide⟩
  | 1, 2 => ⟨4, by decide⟩
  | 1, 3 => ⟨0, by decide⟩
  | 1, 4 => ⟨1, by decide⟩
  | 2, 0 => ⟨4, by decide⟩
  | 2, 1 => ⟨0, by decide⟩
  | 2, 2 => ⟨1, by decide⟩
  | 2, 3 => ⟨2, by decide⟩
  | 2, 4 => ⟨3, by decide⟩
  | 3, 0 => ⟨1, by decide⟩
  | 3, 1 => ⟨2, by decide⟩
  | 3, 2 => ⟨3, by decide⟩
  | 3, 3 => ⟨4, by decide⟩
  | 3, 4 => ⟨0, by decide⟩
  | 4, 0 => ⟨3, by decide⟩
  | 4, 1 => ⟨4, by decide⟩
  | 4, 2 => ⟨0, by decide⟩
  | 4, 3 => ⟨1, by decide⟩
  | 4, 4 => ⟨2, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_704_968 : Magma (Fin 5) := ⟨tabla_704_968⟩

theorem cumple_A_704_968 : LeyA (Fin 5) := by
  unfold LeyA
  decide

theorem no_cumple_B_704_968 : ¬ LeyB (Fin 5) := by
  unfold LeyB
  decide

theorem refuta_704_968 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_704_968 (h (Fin 5) cumple_A_704_968)

#print axioms refuta_704_968
