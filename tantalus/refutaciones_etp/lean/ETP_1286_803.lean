import Mathlib
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = y ◇ (((x ◇ y) ◇ x) ◇ y)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y z w : G, x = y ◇ (z ◇ ((w ◇ z) ◇ z))

set_option maxHeartbeats 40000000
set_option maxRecDepth 200000

/-- Contramodelo de etp:1286_803: tabla de operación sobre `Fin 7`. -/
def tabla_1286_803 : Fin 7 → Fin 7 → Fin 7 := fun a b =>
  match a.val, b.val with
  | 0, 0 => ⟨0, by decide⟩
  | 0, 1 => ⟨2, by decide⟩
  | 0, 2 => ⟨1, by decide⟩
  | 0, 3 => ⟨4, by decide⟩
  | 0, 4 => ⟨3, by decide⟩
  | 0, 5 => ⟨6, by decide⟩
  | 0, 6 => ⟨5, by decide⟩
  | 1, 0 => ⟨3, by decide⟩
  | 1, 1 => ⟨1, by decide⟩
  | 1, 2 => ⟨5, by decide⟩
  | 1, 3 => ⟨0, by decide⟩
  | 1, 4 => ⟨6, by decide⟩
  | 1, 5 => ⟨2, by decide⟩
  | 1, 6 => ⟨4, by decide⟩
  | 2, 0 => ⟨4, by decide⟩
  | 2, 1 => ⟨6, by decide⟩
  | 2, 2 => ⟨2, by decide⟩
  | 2, 3 => ⟨5, by decide⟩
  | 2, 4 => ⟨0, by decide⟩
  | 2, 5 => ⟨3, by decide⟩
  | 2, 6 => ⟨1, by decide⟩
  | 3, 0 => ⟨6, by decide⟩
  | 3, 1 => ⟨5, by decide⟩
  | 3, 2 => ⟨4, by decide⟩
  | 3, 3 => ⟨3, by decide⟩
  | 3, 4 => ⟨2, by decide⟩
  | 3, 5 => ⟨1, by decide⟩
  | 3, 6 => ⟨0, by decide⟩
  | 4, 0 => ⟨5, by decide⟩
  | 4, 1 => ⟨3, by decide⟩
  | 4, 2 => ⟨6, by decide⟩
  | 4, 3 => ⟨1, by decide⟩
  | 4, 4 => ⟨4, by decide⟩
  | 4, 5 => ⟨0, by decide⟩
  | 4, 6 => ⟨2, by decide⟩
  | 5, 0 => ⟨2, by decide⟩
  | 5, 1 => ⟨4, by decide⟩
  | 5, 2 => ⟨0, by decide⟩
  | 5, 3 => ⟨6, by decide⟩
  | 5, 4 => ⟨1, by decide⟩
  | 5, 5 => ⟨5, by decide⟩
  | 5, 6 => ⟨3, by decide⟩
  | 6, 0 => ⟨1, by decide⟩
  | 6, 1 => ⟨0, by decide⟩
  | 6, 2 => ⟨3, by decide⟩
  | 6, 3 => ⟨2, by decide⟩
  | 6, 4 => ⟨5, by decide⟩
  | 6, 5 => ⟨4, by decide⟩
  | 6, 6 => ⟨6, by decide⟩
  | _, _ => ⟨0, by decide⟩

instance magma_1286_803 : Magma (Fin 7) := ⟨tabla_1286_803⟩

theorem cumple_A_1286_803 : LeyA (Fin 7) := by
  unfold LeyA
  decide

theorem no_cumple_B_1286_803 : ¬ LeyB (Fin 7) := by
  unfold LeyB
  decide

theorem refuta_1286_803 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) :=
  fun h => no_cumple_B_1286_803 (h (Fin 7) cumple_A_1286_803)

#print axioms refuta_1286_803
