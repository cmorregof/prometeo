import PortF5.Magma

/- Derivado de teorth/equational_theories, commit 1aec8a7 (Equations/Eqns*.lean (solo las usadas)), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP

abbrev Equation1 (G : Type _) [Magma G] := ∀ x : G, x = x
abbrev Equation2 (G : Type _) [Magma G] := ∀ x y : G, x = y
abbrev Equation4 (G : Type _) [Magma G] := ∀ x y : G, x = x ◇ y
abbrev Equation5 (G : Type _) [Magma G] := ∀ x y : G, x = y ◇ x
abbrev Equation481 (G : Type _) [Magma G] := ∀ x y z : G, x = y ◇ (x ◇ (y ◇ (z ◇ z)))
abbrev Equation883 (G : Type _) [Magma G] := ∀ x y : G, x = y ◇ ((x ◇ y) ◇ (y ◇ y))
abbrev Equation1276 (G : Type _) [Magma G] := ∀ x y : G, x = y ◇ (((x ◇ x) ◇ x) ◇ y)
abbrev Equation1437 (G : Type _) [Magma G] := ∀ x y z : G, x = (x ◇ x) ◇ (y ◇ (z ◇ x))
abbrev Equation1443 (G : Type _) [Magma G] := ∀ x y z : G, x = (x ◇ y) ◇ (x ◇ (x ◇ z))
abbrev Equation1496 (G : Type _) [Magma G] := ∀ x y z : G, x = (y ◇ x) ◇ (y ◇ (z ◇ z))
abbrev Equation1523 (G : Type _) [Magma G] := ∀ x y z : G, x = (y ◇ y) ◇ (x ◇ (z ◇ z))
abbrev Equation1633 (G : Type _) [Magma G] := ∀ x y z : G, x = (x ◇ x) ◇ ((x ◇ y) ◇ z)
abbrev Equation1655 (G : Type _) [Magma G] := ∀ x y : G, x = (x ◇ y) ◇ ((y ◇ x) ◇ y)
abbrev Equation1657 (G : Type _) [Magma G] := ∀ x y : G, x = (x ◇ y) ◇ ((y ◇ y) ◇ x)
abbrev Equation1659 (G : Type _) [Magma G] := ∀ x y z : G, x = (x ◇ y) ◇ ((y ◇ y) ◇ z)
abbrev Equation1661 (G : Type _) [Magma G] := ∀ x y z : G, x = (x ◇ y) ◇ ((y ◇ z) ◇ y)
abbrev Equation1701 (G : Type _) [Magma G] := ∀ x y z : G, x = (y ◇ x) ◇ ((z ◇ x) ◇ x)
abbrev Equation2035 (G : Type _) [Magma G] := ∀ x : G, x = ((x ◇ x) ◇ x) ◇ (x ◇ x)
abbrev Equation2101 (G : Type _) [Magma G] := ∀ x y : G, x = ((y ◇ x) ◇ y) ◇ (y ◇ y)
abbrev Equation2124 (G : Type _) [Magma G] := ∀ x y : G, x = ((y ◇ y) ◇ x) ◇ (x ◇ x)
abbrev Equation2132 (G : Type _) [Magma G] := ∀ x y z : G, x = ((y ◇ y) ◇ x) ◇ (z ◇ z)
abbrev Equation2304 (G : Type _) [Magma G] := ∀ x y : G, x = (y ◇ (x ◇ (y ◇ y))) ◇ y
abbrev Equation3050 (G : Type _) [Magma G] := ∀ x : G, x = (((x ◇ x) ◇ x) ◇ x) ◇ x
abbrev Equation3056 (G : Type _) [Magma G] := ∀ x y : G, x = (((x ◇ x) ◇ y) ◇ x) ◇ y
abbrev Equation3519 (G : Type _) [Magma G] := ∀ x y : G, x ◇ y = x ◇ ((y ◇ x) ◇ y)
abbrev Equation3588 (G : Type _) [Magma G] := ∀ x y z : G, x ◇ y = z ◇ ((x ◇ y) ◇ z)
abbrev Equation3878 (G : Type _) [Magma G] := ∀ x y : G, x ◇ x = (y ◇ (x ◇ x)) ◇ y
abbrev Equation3917 (G : Type _) [Magma G] := ∀ x y : G, x ◇ y = (x ◇ (x ◇ y)) ◇ x
abbrev Equation3955 (G : Type _) [Magma G] := ∀ x y : G, x ◇ y = (y ◇ (x ◇ y)) ◇ y
abbrev Equation3994 (G : Type _) [Magma G] := ∀ x y z : G, x ◇ y = (z ◇ (x ◇ y)) ◇ z
abbrev Equation4065 (G : Type _) [Magma G] := ∀ x : G, x ◇ x = ((x ◇ x) ◇ x) ◇ x
abbrev Equation4067 (G : Type _) [Magma G] := ∀ x y : G, x ◇ x = ((x ◇ x) ◇ y) ◇ x
abbrev Equation4268 (G : Type _) [Magma G] := ∀ x y : G, x ◇ (x ◇ x) = x ◇ (x ◇ y)
abbrev Equation4282 (G : Type _) [Magma G] := ∀ x y z : G, x ◇ (x ◇ y) = x ◇ (x ◇ z)
abbrev Equation4316 (G : Type _) [Magma G] := ∀ x y z : G, x ◇ (y ◇ x) = x ◇ (z ◇ x)
abbrev Equation4332 (G : Type _) [Magma G] := ∀ x y z : G, x ◇ (y ◇ x) = z ◇ (y ◇ z)

end ETP
