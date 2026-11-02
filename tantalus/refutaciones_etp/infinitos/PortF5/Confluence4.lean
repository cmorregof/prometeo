import PortF5.ConfluenceSystem

/- Derivado de teorth/equational_theories, commit 1aec8a7 (Confluence4.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


open FreeMagma Confluence
variable {α: Type} [DecidableEq α]

namespace rw1443

rule_system rules {x y z: FreeMagma α}
| ((x ⋆ y) ⋆ (x ⋆ (x ⋆ z))) => x
| (x ⋆ ((x ⋆ y) ⋆ x)) => (x ⋆ y)
| (x ⋆ ((x ⋆ y) ⋆ ((x ⋆ y) ⋆ z))) => (x ⋆ y)
| (((x ⋆ y) ⋆ z) ⋆ ((x ⋆ y) ⋆ x)) => (x ⋆ y)

theorem comp1_2 {x y z : FreeMagma α}:
    rules (rules (x ⋆ y) ⋆ (x ⋆ (x ⋆ z))) = x := by
  generalize h: rules (x ⋆ y) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq3
  · apply rules.eq1
  · apply rules.eq1
  · apply rules.eq3
  · apply rules.eq1

theorem comp1_3 {x y z : FreeMagma α}:
    rules (rules (x ⋆ y) ⋆ rules (x ⋆ (x ⋆ z))) = x := by
  generalize h: rules (x ⋆ (x ⋆ z)) = e
  simp only [rules.elim] at h
  separate
  · apply comp1_2

theorem comp4_2 {x y z : FreeMagma α}:
    rules (rules (x ⋆ y ⋆ z) ⋆ (x ⋆ y ⋆ x)) = x ⋆ y := by
  generalize h: rules (x ⋆ y ⋆ z) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq2
  · apply rules.eq4
  · apply rules.eq4
  · apply rules.eq2
  · apply rules.eq4

theorem comp4_3 {x y z : FreeMagma α}:
    rules (rules (x ⋆ y ⋆ z) ⋆ rules (x ⋆ y ⋆ x)) = x ⋆ y := by
  generalize h: rules (x ⋆ y ⋆ x) = e
  simp only [rules.elim] at h
  separate
  apply comp4_2

theorem comp1_4 {x y z : FreeMagma α}:
    rules (rules (x ⋆ y) ⋆ rules (x ⋆ rules (x ⋆ z))) = x := by
  generalize h: rules (x ⋆ z) = e
  simp only [rules.elim] at h
  separate
  · apply comp4_3
  · apply comp1_3
  · apply comp1_3
  · apply comp4_3
  · apply comp1_3

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [1443] [4065, 4067] := by
  use ConfMagma (@rules Nat _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩ ⟨z, hz⟩
    simp (disch := bufixed) only [Magma.op, bu, hx, hy, hz, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp1_4
  all_goals refute

end rw1443

namespace rw1633

rule_system rules {x y z: FreeMagma α}
| ((x ⋆ x) ⋆ ((x ⋆ y) ⋆ z)) => x
| ((x ⋆ x) ⋆ x) => x
| (((x ⋆ x) ⋆ (x ⋆ x)) ⋆ (x ⋆ y)) => (x ⋆ x)
| ((((x ⋆ x) ⋆ (x ⋆ x)) ⋆ ((x ⋆ x) ⋆ (x ⋆ x))) ⋆ x) => ((x ⋆ x) ⋆ (x ⋆ x))

theorem comp1_2 {x y z : FreeMagma α}:
    rules (x ⋆ x ⋆ rules (x ⋆ y ⋆ z)) = x := by
  generalize h: rules (x ⋆ y ⋆ z) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq2
  · apply rules.eq2
  · apply rules.eq2
  · apply rules.eq2
  · apply rules.eq1

theorem comp3_2 {x y : FreeMagma α}:
    rules (x ⋆ x ⋆ (x ⋆ x) ⋆ rules (x ⋆ y)) = x ⋆ x := by
  generalize h: rules (x ⋆ y) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq4
  · apply rules.eq4
  · apply rules.eq4
  · apply rules.eq4
  · apply rules.eq3

theorem comp1_3 {x y z : FreeMagma α}:
    rules (x ⋆ x ⋆ rules (rules (x ⋆ y) ⋆ z)) = x := by
  generalize h: rules (x ⋆ y) = e
  simp only [rules.elim] at h
  separate
  · apply comp3_2
  · apply comp3_2
  · apply comp3_2
  · apply comp3_2
  · apply comp1_2

theorem comp1_4 {x y z : FreeMagma α}:
    rules (rules (x ⋆ x) ⋆ rules (rules (x ⋆ y) ⋆ z)) = x := by
  generalize h: rules (x ⋆ x) = e
  simp only [rules.elim] at h
  separate
  apply comp1_3

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [1633] [4268, 4282] := by
  use ConfMagma (@rules Nat _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩ ⟨z, hz⟩
    simp (disch := bufixed) only [Magma.op, bu, hx, hy, hz, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp1_4
  all_goals refute

end rw1633

end ETP
