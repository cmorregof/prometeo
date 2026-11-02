import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ y = (x ◇ z) ◇ y

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = (y ◇ ((x ◇ y) ◇ y)) ◇ (x ◇ (z ◇ y))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:381_345169: tabla de operación sobre `Fin 2`. -/
def tabla_381_345169 : Fin 2 → Fin 2 → Fin 2 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨0, by decide⟩
  | 1, 0 => ⟨0, by decide⟩
  | 1, 1 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_381_345169 : Magma (Fin 2) := ⟨tabla_381_345169⟩

theorem cumple_A_381_345169 : LeyA (Fin 2) := by
  unfold LeyA
  decide

theorem no_cumple_B_381_345169 : ¬ LeyB (Fin 2) := by
  unfold LeyB
  decide

theorem refuta_381_345169 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_381_345169 (h (Fin 2) cumple_A_381_345169)

#print axioms refuta_381_345169
