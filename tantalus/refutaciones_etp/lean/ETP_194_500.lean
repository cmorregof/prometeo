import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = (y ◇ z) ◇ (z ◇ x)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = y ◇ (y ◇ (x ◇ (x ◇ x)))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:194_500: tabla de operación sobre `Fin 6`. -/
def tabla_194_500 : Fin 6 → Fin 6 → Fin 6 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨1, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 0, 2 => ⟨3, by decide⟩
  | 0, 3 => ⟨4, by decide⟩
  | 0, 4 => ⟨5, by decide⟩
  | 0, 5 => ⟨0, by decide⟩
  | 1, 0 => ⟨5, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | 1, 2 => ⟨1, by decide⟩
  | 1, 3 => ⟨2, by decide⟩
  | 1, 4 => ⟨3, by decide⟩
  | 1, 5 => ⟨4, by decide⟩
  | 2, 0 => ⟨1, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨3, by decide⟩
  | 2, 3 => ⟨4, by decide⟩
  | 2, 4 => ⟨5, by decide⟩
  | 2, 5 => ⟨0, by decide⟩
  | 3, 0 => ⟨5, by decide⟩
  | 3, 1 => ⟨0, by decide⟩
  | 3, 2 => ⟨1, by decide⟩
  | 3, 3 => ⟨2, by decide⟩
  | 3, 4 => ⟨3, by decide⟩
  | 3, 5 => ⟨4, by decide⟩
  | 4, 0 => ⟨1, by decide⟩
  | 4, 1 => ⟨2, by decide⟩
  | 4, 2 => ⟨3, by decide⟩
  | 4, 3 => ⟨4, by decide⟩
  | 4, 4 => ⟨5, by decide⟩
  | 4, 5 => ⟨0, by decide⟩
  | 5, 0 => ⟨5, by decide⟩
  | 5, 1 => ⟨0, by decide⟩
  | 5, 2 => ⟨1, by decide⟩
  | 5, 3 => ⟨2, by decide⟩
  | 5, 4 => ⟨3, by decide⟩
  | 5, 5 => ⟨4, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_194_500 : Magma (Fin 6) := ⟨tabla_194_500⟩

theorem cumple_A_194_500 : LeyA (Fin 6) := by
  unfold LeyA
  decide

theorem no_cumple_B_194_500 : ¬ LeyB (Fin 6) := by
  unfold LeyB
  decide

theorem refuta_194_500 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_194_500 (h (Fin 6) cumple_A_194_500)

#print axioms refuta_194_500
