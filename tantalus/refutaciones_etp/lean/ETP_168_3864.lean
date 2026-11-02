import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y z : G, x = (y ◇ x) ◇ (x ◇ z)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x ◇ x = (x ◇ (x ◇ y)) ◇ x

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:168_3864: tabla de operación sobre `Fin 9`. -/
def tabla_168_3864 : Fin 9 → Fin 9 → Fin 9 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨2, by decide⟩
  | 0, 1 => ⟨8, by decide⟩
  | 0, 2 => ⟨7, by decide⟩
  | 0, 3 => ⟨2, by decide⟩
  | 0, 4 => ⟨8, by decide⟩
  | 0, 5 => ⟨8, by decide⟩
  | 0, 6 => ⟨2, by decide⟩
  | 0, 7 => ⟨7, by decide⟩
  | 0, 8 => ⟨7, by decide⟩
  | 1, 0 => ⟨1, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨0, by decide⟩
  | 1, 3 => ⟨6, by decide⟩
  | 1, 4 => ⟨6, by decide⟩
  | 1, 5 => ⟨6, by decide⟩
  | 1, 6 => ⟨1, by decide⟩
  | 1, 7 => ⟨0, by decide⟩
  | 1, 8 => ⟨0, by decide⟩
  | 2, 0 => ⟨3, by decide⟩
  | 2, 1 => ⟨3, by decide⟩
  | 2, 2 => ⟨0, by decide⟩
  | 2, 3 => ⟨6, by decide⟩
  | 2, 4 => ⟨6, by decide⟩
  | 2, 5 => ⟨6, by decide⟩
  | 2, 6 => ⟨3, by decide⟩
  | 2, 7 => ⟨0, by decide⟩
  | 2, 8 => ⟨0, by decide⟩
  | 3, 0 => ⟨1, by decide⟩
  | 3, 1 => ⟨1, by decide⟩
  | 3, 2 => ⟨0, by decide⟩
  | 3, 3 => ⟨6, by decide⟩
  | 3, 4 => ⟨6, by decide⟩
  | 3, 5 => ⟨6, by decide⟩
  | 3, 6 => ⟨1, by decide⟩
  | 3, 7 => ⟨0, by decide⟩
  | 3, 8 => ⟨0, by decide⟩
  | 4, 0 => ⟨3, by decide⟩
  | 4, 1 => ⟨3, by decide⟩
  | 4, 2 => ⟨5, by decide⟩
  | 4, 3 => ⟨4, by decide⟩
  | 4, 4 => ⟨4, by decide⟩
  | 4, 5 => ⟨4, by decide⟩
  | 4, 6 => ⟨3, by decide⟩
  | 4, 7 => ⟨5, by decide⟩
  | 4, 8 => ⟨5, by decide⟩
  | 5, 0 => ⟨2, by decide⟩
  | 5, 1 => ⟨8, by decide⟩
  | 5, 2 => ⟨7, by decide⟩
  | 5, 3 => ⟨2, by decide⟩
  | 5, 4 => ⟨8, by decide⟩
  | 5, 5 => ⟨8, by decide⟩
  | 5, 6 => ⟨2, by decide⟩
  | 5, 7 => ⟨7, by decide⟩
  | 5, 8 => ⟨7, by decide⟩
  | 6, 0 => ⟨3, by decide⟩
  | 6, 1 => ⟨3, by decide⟩
  | 6, 2 => ⟨5, by decide⟩
  | 6, 3 => ⟨4, by decide⟩
  | 6, 4 => ⟨4, by decide⟩
  | 6, 5 => ⟨4, by decide⟩
  | 6, 6 => ⟨3, by decide⟩
  | 6, 7 => ⟨5, by decide⟩
  | 6, 8 => ⟨5, by decide⟩
  | 7, 0 => ⟨2, by decide⟩
  | 7, 1 => ⟨8, by decide⟩
  | 7, 2 => ⟨7, by decide⟩
  | 7, 3 => ⟨2, by decide⟩
  | 7, 4 => ⟨8, by decide⟩
  | 7, 5 => ⟨8, by decide⟩
  | 7, 6 => ⟨2, by decide⟩
  | 7, 7 => ⟨7, by decide⟩
  | 7, 8 => ⟨7, by decide⟩
  | 8, 0 => ⟨1, by decide⟩
  | 8, 1 => ⟨1, by decide⟩
  | 8, 2 => ⟨5, by decide⟩
  | 8, 3 => ⟨4, by decide⟩
  | 8, 4 => ⟨4, by decide⟩
  | 8, 5 => ⟨4, by decide⟩
  | 8, 6 => ⟨1, by decide⟩
  | 8, 7 => ⟨5, by decide⟩
  | 8, 8 => ⟨5, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_168_3864 : Magma (Fin 9) := ⟨tabla_168_3864⟩

theorem cumple_A_168_3864 : LeyA (Fin 9) := by
  unfold LeyA
  decide

theorem no_cumple_B_168_3864 : ¬ LeyB (Fin 9) := by
  unfold LeyB
  decide

theorem refuta_168_3864 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_168_3864 (h (Fin 9) cumple_A_168_3864)

#print axioms refuta_168_3864
