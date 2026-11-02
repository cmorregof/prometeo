import Mathlib
import PortF5.Tareas
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = ((y ◇ y) ◇ (y ◇ x)) ◇ y

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = (y ◇ y) ◇ (y ◇ (x ◇ y))

/-- Refutación con un magma infinito: etp:2744_1526 es un par de Austin, así que no hay contramodelo finito. -/
theorem refuta_2744_1526 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) := by
  intro h
  obtain ⟨G, o, hA, hB⟩ := ETP.t_2744_1526
  letI : Magma G := ⟨o⟩
  exact hB (h G hA)

#print axioms refuta_2744_1526
