import Mathlib
import PortF5.Tareas
set_option relaxedAutoImplicit false
set_option maxSynthPendingDepth 3

class Magma (α : Type _) where
  op : α → α → α

infix:65 " ◇ " => Magma.op

def LeyA (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x = (y ◇ x) ◇ ((x ◇ x) ◇ x)

def LeyB (G : Type _) [Magma G] : Prop :=
  ∀ x y : G, x ◇ x = (y ◇ (x ◇ x)) ◇ x

/-- Refutación con un magma infinito: etp:1681_3877 es un par de Austin, así que no hay contramodelo finito. -/
theorem refuta_1681_3877 : ¬ (∀ (G : Type) [Magma G], LeyA G → LeyB G) := by
  intro h
  obtain ⟨G, o, hA, hB⟩ := ETP.t_1681_3877
  letI : Magma G := ⟨o⟩
  exact hB (h G hA)

#print axioms refuta_1681_3877
