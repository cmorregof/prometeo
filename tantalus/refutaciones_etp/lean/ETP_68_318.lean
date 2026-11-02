import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = y ◇ (x ◇ (z ◇ x))

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x ◇ x = y ◇ (z ◇ x)

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:68_318: tabla de operación sobre `Fin 3`. -/
def tabla_68_318 : Fin 3 → Fin 3 → Fin 3 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨1, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 0, 2 => ⟨0, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨2, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 2, 0 => ⟨1, by decide⟩
  | 2, 1 => ⟨2, by decide⟩
  | 2, 2 => ⟨0, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_68_318 : Magma (Fin 3) := ⟨tabla_68_318⟩

theorem cumple_A_68_318 : LeyA (Fin 3) := by
  unfold LeyA
  decide

theorem no_cumple_B_68_318 : ¬ LeyB (Fin 3) := by
  unfold LeyB
  decide

theorem refuta_68_318 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_68_318 (h (Fin 3) cumple_A_68_318)

#print axioms refuta_68_318
