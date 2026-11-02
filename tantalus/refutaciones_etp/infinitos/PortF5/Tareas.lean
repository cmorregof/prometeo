import PortF5.Confluence2
import PortF5.Confluence3
import PortF5.Confluence4
import PortF5.Eq1437
import PortF5.Eq1659
import PortF5.Eq1661
import PortF5.Eq1701
import PortF5.Inf3994
import PortF5.Eq883

/- Los 30 enunciados F5 en forma plana, sin clase Magma. -/

namespace ETP

open FreeMagma Confluence

theorem t_3161_473 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o (o (o y y) z) x) z)) ∧ ¬ (∀ x y : G, x = (o y (o x (o y (o x x))))) := by
  obtain ⟨G, _, hA, hB⟩ := rw481.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA x z y)
  · intro h
    exact hB.2.2.2 (fun x y => (h x y))

theorem t_1661_4314 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o x y) (o (o y z) y))) ∧ ¬ (∀ x y : G, (o x (o y x)) = (o x (o y y))) := by
  refine ⟨ℕ, fun a b => op_1661_1657 a b, ?_, ?_⟩
  · intro x y z
    exact (op_1661_1657_satisfies_1661 x y z)
  · intro h
    have h' := h 0 3
    revert h'
    decide

theorem t_1659_1852 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o x y) (o (o y y) z))) ∧ ¬ (∀ x y z : G, x = (o (o x (o y x)) (o y z))) := by
  refine ⟨ℕ, fun a b => op_1659_4315 a b, ?_, ?_⟩
  · intro x y z
    exact (op_1659_4315_satisfies_1659 x y z)
  · intro h
    have h' := h 0 0 1
    revert h'
    decide

theorem t_1659_3519 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o x y) (o (o y y) z))) ∧ ¬ (∀ x y : G, (o x y) = (o x (o (o y x) y))) := by
  refine ⟨ℕ, fun a b => op_1659_4315 a b, ?_, ?_⟩
  · intro x y z
    exact (op_1659_4315_satisfies_1659 x y z)
  · intro h
    have h' := h 0 1
    revert h'
    decide

theorem t_1979_1681 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y (o z y)) (o y x))) ∧ ¬ (∀ x y : G, x = (o (o y x) (o (o x x) x))) := by
  refine ⟨ℕ, fun a b => op_1661_1657 b a, ?_, ?_⟩
  · intro x y z
    exact (op_1661_1657_satisfies_1661 x y z)
  · intro h
    have h' := h 3 0
    revert h'
    decide

theorem t_2000_1897 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y (o z z)) (o z x))) ∧ ¬ (∀ x y : G, x = (o (o y (o x y)) (o y x))) := by
  refine ⟨ℕ, fun a b => op_1659_4315 b a, ?_, ?_⟩
  · intro x y z
    exact (op_1659_4315_satisfies_1659 x z y)
  · intro h
    have h' := h 0 1
    revert h'
    decide

theorem t_1441_4067 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o (o x y) (o x (o x x)))) ∧ ¬ (∀ x y : G, (o x x) = (o (o (o x x) y) x)) := by
  obtain ⟨G, _, hA, hB⟩ := rw1443.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y
    exact (hA x y x)
  · intro h
    exact hB.2 (fun x y => (h x y))

theorem t_2132_1523 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o (o y y) x) (o z z))) ∧ ¬ (∀ x y z : G, x = (o (o y y) (o x (o z z)))) := by
  obtain ⟨G, _, hA, hB⟩ := rw1523.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA x z y)
  · intro h
    exact hB.2.2 (fun x y z => (h x z y))

theorem t_3917_3511 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, (o x y) = (o (o x (o x y)) x)) ∧ ¬ (∀ x y : G, (o x y) = (o x (o (o x y) x))) := by
  obtain ⟨G, _, hA, hB⟩ := rw3588.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y
    exact (hA y x x)
  · intro h
    exact hB.2.2 (fun x y => (h y x))

theorem t_3588_3955 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, (o x y) = (o z (o (o x y) z))) ∧ ¬ (∀ x y : G, (o x y) = (o (o y (o x y)) y)) := by
  obtain ⟨G, _, hA, hB⟩ := rw3588.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.2.2 (fun x y => (h x y))

theorem t_3161_411 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o (o (o y y) z) x) z)) ∧ ¬ (∀ x : G, x = (o x (o x (o x (o x x))))) := by
  obtain ⟨G, _, hA, hB⟩ := rw481.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA x z y)
  · intro h
    exact hB.2.2.1 (fun x => (h x))

theorem t_1979_1742 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y (o z y)) (o y x))) ∧ ¬ (∀ x y z : G, x = (o (o y y) (o (o z y) x))) := by
  refine ⟨ℕ, fun a b => op_1661_1657 b a, ?_, ?_⟩
  · intro x y z
    exact (op_1661_1657_satisfies_1661 x y z)
  · intro h
    have h' := h 0 3 0
    revert h'
    decide

theorem t_1661_4282 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o x y) (o (o y z) y))) ∧ ¬ (∀ x y z : G, (o x (o x y)) = (o x (o x z))) := by
  refine ⟨ℕ, fun a b => op_1661_1657 a b, ?_, ?_⟩
  · intro x y z
    exact (op_1661_1657_satisfies_1661 x y z)
  · intro h
    have h' := h 3 0 1
    revert h'
    decide

theorem t_1633_4282 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o x x) (o (o x y) z))) ∧ ¬ (∀ x y z : G, (o x (o x y)) = (o x (o x z))) := by
  obtain ⟨G, _, hA, hB⟩ := rw1633.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.2 (fun x y z => (h x y z))

theorem t_2000_4615 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y (o z z)) (o z x))) ∧ ¬ (∀ x y z : G, (o (o x x) y) = (o (o z x) y)) := by
  refine ⟨ℕ, fun a b => op_1659_4315 b a, ?_, ?_⟩
  · intro x y z
    exact (op_1659_4315_satisfies_1659 x z y)
  · intro h
    have h' := h 0 0 1
    revert h'
    decide

theorem t_2070_4631 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o (o x y) z) (o x x))) ∧ ¬ (∀ x y z : G, (o (o x y) x) = (o (o x z) x)) := by
  refine ⟨ℕ × Fin 3, fun a b => Eq1437.op b a, ?_, ?_⟩
  · intro x y z
    exact (Eq1437.satisface1437 x z y)
  · intro h
    have h' := h (0, 0) (0, 0) (0, 2)
    revert h'
    decide

theorem t_2037_3253 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o (o (o x x) x) (o y x))) ∧ ¬ (∀ x : G, (o x x) = (o x (o x (o x x)))) := by
  obtain ⟨G, _, hA, hB⟩ := rw1443.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y
    exact (hA x y x)
  · intro h
    exact hB.1 (fun x => (h x))

theorem t_2132_1426 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o (o y y) x) (o z z))) ∧ ¬ (∀ x : G, x = (o (o x x) (o x (o x x)))) := by
  obtain ⟨G, _, hA, hB⟩ := rw1523.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA x z y)
  · intro h
    exact hB.1 (fun x => (h x))

theorem t_3994_3549 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, (o x y) = (o (o z (o x y)) z)) ∧ ¬ (∀ x y : G, (o x y) = (o y (o (o x y) y))) := by
  obtain ⟨G, _, hA, hB⟩ := rw3588.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA y x z)
  · intro h
    exact hB.2.1 (fun x y => (h y x))

theorem t_481_2035 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o y (o x (o y (o z z))))) ∧ ¬ (∀ x : G, x = (o (o (o x x) x) (o x x))) := by
  obtain ⟨G, _, hA, hB⟩ := rw481.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.2.1 (fun x => (h x))

theorem t_481_1496 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o y (o x (o y (o z z))))) ∧ ¬ (∀ x y z : G, x = (o (o y x) (o y (o z z)))) := by
  obtain ⟨G, _, hA, hB⟩ := rw481.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.1 (fun x y z => (h x y z))

theorem t_3994_3588 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, (o x y) = (o (o z (o x y)) z)) ∧ ¬ (∀ x y z : G, (o x y) = (o z (o (o x y) z))) := by
  obtain ⟨G, _, hA, hB⟩ := Equation3994_not_implies_Equation3588
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB (fun x y z => (h x y z))

theorem t_883_2035 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o y (o (o x y) (o y y)))) ∧ ¬ (∀ x : G, x = (o (o (o x x) x) (o x x))) := by
  obtain ⟨G, _, hA, hB⟩ := Eq883.Equation883_not_implies_Equation2035
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y
    exact (hA x y)
  · intro h
    exact hB (fun x => (h x))

theorem t_883_2304 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o y (o (o x y) (o y y)))) ∧ ¬ (∀ x y : G, x = (o (o y (o x (o y y))) y)) := by
  obtain ⟨G, _, hA, hB⟩ := Eq883.Equation883_not_implies_Equation2304
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y
    exact (hA x y)
  · intro h
    exact hB (fun x y => (h x y))

theorem t_1958_4587 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y (o z x)) (o x x))) ∧ ¬ (∀ x y : G, (o (o x x) x) = (o (o y x) x)) := by
  obtain ⟨G, _, hA, hB⟩ := rw1633.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y z
    exact (hA x z y)
  · intro h
    exact hB.1 (fun x y => (h x y))

theorem t_1681_3877 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o (o y x) (o (o x x) x))) ∧ ¬ (∀ x y : G, (o x x) = (o (o y (o x x)) x)) := by
  refine ⟨ℕ, fun a b => op_1701_8 a b, ?_, ?_⟩
  · intro x y
    exact (op_1701_8_satisfies_1701 x y x)
  · intro h
    have h' := h 1 0
    revert h'
    decide

theorem t_2291_4647 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o (o y (o x (o x x))) y)) ∧ ¬ (∀ x y z : G, (o (o x y) x) = (o (o z y) z)) := by
  obtain ⟨G, _, hA, hB⟩ := rw1276.«Facts»
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y
    exact (hA x y)
  · intro h
    exact hB (fun x y z => (h x y z))

theorem t_2744_1526 : ∃ (G : Type) (o : G → G → G),
    (∀ x y : G, x = (o (o (o y y) (o y x)) y)) ∧ ¬ (∀ x y : G, x = (o (o y y) (o y (o x y)))) := by
  obtain ⟨G, _, hA, hB⟩ := Eq883.Equation883_not_implies_Equation2101
  refine ⟨G, fun a b => Magma.op b a, ?_, ?_⟩
  · intro x y
    exact (hA x y)
  · intro h
    exact hB (fun x y => (h x y))

theorem t_1523_2124 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, x = (o (o y y) (o x (o z z)))) ∧ ¬ (∀ x y : G, x = (o (o (o y y) x) (o x x))) := by
  obtain ⟨G, _, hA, hB⟩ := rw1523.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.2.1 (fun x y => (h x y))

theorem t_3588_3878 : ∃ (G : Type) (o : G → G → G),
    (∀ x y z : G, (o x y) = (o z (o (o x y) z))) ∧ ¬ (∀ x y : G, (o x x) = (o (o y (o x x)) y)) := by
  obtain ⟨G, _, hA, hB⟩ := rw3588.«Facts»
  refine ⟨G, fun a b => Magma.op a b, ?_, ?_⟩
  · intro x y z
    exact (hA x y z)
  · intro h
    exact hB.1 (fun x y => (h x y))

end ETP
