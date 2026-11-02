import PortF5.ConfluenceSystem

/- Derivado de teorth/equational_theories, commit 1aec8a7 (Confluence2.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


open FreeMagma Confluence
variable {α: Type} [DecidableEq α]

namespace rw1276

rule_system rules {x y: FreeMagma α}
| (x ⋆ (((y ⋆ y) ⋆ y) ⋆ x)) => y
| ((((x ⋆ x) ⋆ x) ⋆ ((y ⋆ y) ⋆ y)) ⋆ x) => y

theorem comp1_2 {x y : FreeMagma α}:
    rules (y ⋆ rules (x ⋆ x ⋆ x ⋆ y)) = x := by
  generalize h: rules (x ⋆ x ⋆ x ⋆ y) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq2
  · apply rules.eq1

theorem comp1_3 {x y : FreeMagma α}:
    rules (y ⋆ rules (rules (x ⋆ x ⋆ x) ⋆ y)) = x := by
  generalize h: rules (x ⋆ x ⋆ x) = e
  simp only [rules.elim] at h
  separate
  apply comp1_2

theorem comp1_4 {x y : FreeMagma α}:
    rules (y ⋆ rules (rules (rules (x ⋆ x) ⋆ x) ⋆ y)) = x := by
  generalize h: rules (x ⋆ x) = e
  simp only [rules.elim] at h
  separate
  apply comp1_3

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [1276] [4332] := by
  use ConfMagma (@rules Nat _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩
    simp (disch := bufixed) only [Magma.op, bu, hx, hy, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp1_4
  all_goals refute

end rw1276

namespace rw1523
variable [Inhabited α]

rule_system rules {x y z: FreeMagma α} -IsProj
| (y ⋆ y) ⋆ (x ⋆ (y ⋆ y)) => x
| x ⋆ x => default ⋆ default

instance: IsProjOrNF (rules : FreeMagma α → _) where
  proj_or_nf := by
    intro x
    generalize h: rules x = e
    simp only [rules.elim] at h
    separate
    · left
      subterm
    · right
      simp only [NF, Everywhere, and_self_left]
      constructor
      · exact (rfl : rules (FreeMagma.Leaf (default : α)) = FreeMagma.Leaf default)
      · apply rules.eq2
    · left
      rfl

theorem comp1_2 {x : FreeMagma α}:
    rules (default ⋆ default ⋆ rules (x ⋆ (default ⋆ default))) = x := by
  generalize h: rules (x ⋆ (default ⋆ default)) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq2
  · apply rules.eq1

theorem comp1_4 {x y z : FreeMagma α}:
    rules (rules (y ⋆ y) ⋆ rules (x ⋆ rules (z ⋆ z))) = x := by
  simp [rules.eq2]
  apply comp1_2

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [1523] [2035, 2124, 2132] := by
  use ConfMagma (@rules Nat _ _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩ ⟨z, hz⟩
    simp (disch := bufixed) only [Magma.op, bu, hx, hy, hz, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp1_4
  all_goals refute

end rw1523

namespace rw3588

rule_system rules {x y z w: FreeMagma α}
| z ⋆ ((x ⋆ y) ⋆ z) => x ⋆ y
| ((z ⋆ w) ⋆ (x ⋆ y)) ⋆ (z ⋆ w) => x ⋆ y

theorem comp2 {x y z : FreeMagma α} (hxy: NF rules (x ⋆ y)):
    rules (z ⋆ rules (x ⋆ y ⋆ z)) = x ⋆ y := by
  generalize h: rules (x ⋆ y ⋆ z) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq2
  · apply rw_eq_self_of_NF rules hxy
  · apply rules.eq1

theorem comp3 {x y z : FreeMagma α} (hx: NF rules x) (hy: NF rules y):
    rules (z ⋆ rules (rules (x ⋆ y) ⋆ z)) = rules (x ⋆ y) := by
  generalize h: rules (x ⋆ y) = e
  simp only [rules.elim] at h
  separate
  all_goals apply comp2
  · apply Everywhere.left hy
  · apply Everywhere.right hx
  · rw [NF, Everywhere]
    refine ⟨hx, hy, ?_⟩
    simp only [rules.elim]
    right
    constructorm* _ ∧ _
    all_goals trivial

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [3588] [3878, 3917, 3955] := by
  use ConfMagma (@rules Nat _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩ ⟨z, hz⟩
    simp only [Magma.op, bu, hx, hy, hz, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp3 ((NF_iff_buFixed rules).mpr hx) ((NF_iff_buFixed rules).mpr hy)
  all_goals refute

end rw3588

end ETP
