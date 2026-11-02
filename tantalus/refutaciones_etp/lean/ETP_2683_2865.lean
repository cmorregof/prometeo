import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = ((x ◇ y) ◇ (z ◇ y)) ◇ x

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = ((x ◇ (y ◇ x)) ◇ y) ◇ x

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:2683_2865: tabla de operación sobre `Fin 6`. -/
def tabla_2683_2865 : Fin 6 → Fin 6 → Fin 6 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨1, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 0, 3 => ⟨3, by decide⟩
  | 0, 4 => ⟨4, by decide⟩
  | 0, 5 => ⟨5, by decide⟩
  | 1, 0 => ⟨2, by decide⟩
  | 1, 1 => ⟨5, by decide⟩
  | 1, 2 => ⟨2, by decide⟩
  | 1, 3 => ⟨5, by decide⟩
  | 1, 4 => ⟨5, by decide⟩
  | 1, 5 => ⟨5, by decide⟩
  | 2, 0 => ⟨2, by decide⟩
  | 2, 1 => ⟨1, by decide⟩
  | 2, 2 => ⟨2, by decide⟩
  | 2, 3 => ⟨3, by decide⟩
  | 2, 4 => ⟨4, by decide⟩
  | 2, 5 => ⟨5, by decide⟩
  | 3, 0 => ⟨0, by decide⟩
  | 3, 1 => ⟨1, by decide⟩
  | 3, 2 => ⟨2, by decide⟩
  | 3, 3 => ⟨4, by decide⟩
  | 3, 4 => ⟨4, by decide⟩
  | 3, 5 => ⟨4, by decide⟩
  | 4, 0 => ⟨0, by decide⟩
  | 4, 1 => ⟨5, by decide⟩
  | 4, 2 => ⟨2, by decide⟩
  | 4, 3 => ⟨5, by decide⟩
  | 4, 4 => ⟨5, by decide⟩
  | 4, 5 => ⟨5, by decide⟩
  | 5, 0 => ⟨0, by decide⟩
  | 5, 1 => ⟨3, by decide⟩
  | 5, 2 => ⟨2, by decide⟩
  | 5, 3 => ⟨3, by decide⟩
  | 5, 4 => ⟨3, by decide⟩
  | 5, 5 => ⟨3, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_2683_2865 : Magma (Fin 6) := ⟨tabla_2683_2865⟩

theorem cumple_A_2683_2865 : LeyA (Fin 6) := by
  unfold LeyA
  decide

theorem no_cumple_B_2683_2865 : ¬ LeyB (Fin 6) := by
  unfold LeyB
  decide

theorem refuta_2683_2865 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_2683_2865 (h (Fin 6) cumple_A_2683_2865)

#print axioms refuta_2683_2865
