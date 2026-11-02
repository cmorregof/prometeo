import PortF5.ConfluenceSystem

/- Derivado de teorth/equational_theories, commit 1aec8a7 (Confluence3.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


open FreeMagma Confluence
variable {α: Type} [DecidableEq α]

namespace rw481
variable [Inhabited α]

rule_system rules {x y z: FreeMagma α} -IsProj
| y ⋆ (x ⋆ (y ⋆ (z ⋆ z))) => x
| (z ⋆ z) ⋆ (x ⋆ (z ⋆ z)) => x
| x ⋆ x => default ⋆ default

instance: IsProjOrNF (rules : FreeMagma α → _) where
  proj_or_nf := by
    intro x
    generalize h: rules x = e
    simp only [rules.elim] at h
    separate
    · left
      subterm
    · left
      subterm
    · right
      simp only [NF, Everywhere, and_self_left]
      constructor
      · exact (rfl : rules (FreeMagma.Leaf (default : α)) = FreeMagma.Leaf default)
      · apply rules.eq3
    · left
      rfl

theorem comp1_2 {x y : FreeMagma α} (hx: NF rules x):
    rules (y ⋆ rules (x ⋆ (y ⋆ (default ⋆ default)))) = x := by
  generalize h: rules (x ⋆ (y ⋆ (default ⋆ default))) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq3
  · apply hx.top
  · apply rules.eq1

theorem comp2_2 {x : FreeMagma α} (hx: NF rules x):
    rules (default ⋆ default ⋆ rules (x ⋆ (default ⋆ default))) = x := by
  generalize h: rules (x ⋆ (default ⋆ default)) = e
  simp only [rules.elim] at h
  separate
  · apply rules.eq3
  · apply rules.eq2

theorem comp1_3 {x y : FreeMagma α} (hx: NF rules x):
    rules (y ⋆ rules (x ⋆ rules (y ⋆ (default ⋆ default)))) = x := by
  generalize h: rules (y ⋆ (default ⋆ default)) = e
  simp only [rules.elim] at h
  separate
  · apply comp2_2 hx
  · apply comp1_2 hx

theorem comp1_4 {x y z : FreeMagma α} (hx: NF rules x):
    rules (y ⋆ rules (x ⋆ rules (y ⋆ rules (z ⋆ z)))) = x := by
  generalize h: rules (z ⋆ z) = e
  simp only [rules.elim] at h
  separate
  · apply comp1_3 hx
  · exfalso
    simp_all only [Fork.injEq, not_exists, not_and, exists_eq', not_true_eq_false]

theorem «Facts» :
  ∃ (G : Type) (_ : Magma G), Facts G [481] [1496, 2035, 3050, 3056] := by
  use ConfMagma (@rules Nat _ _), inferInstance
  repeat' apply And.intro
  · rintro ⟨x, hx⟩ ⟨y, hy⟩ ⟨z, hz⟩
    simp (disch := bufixed) only [Magma.op, bu, hx, hy, hz, buFixed_rw_op]
    symm
    apply Subtype.ext
    apply comp1_4 ((NF_iff_buFixed rules).mpr hx)
  all_goals refute

end rw481

end ETP
