import PortF5.Magma

/- Derivado de teorth/equational_theories, commit 1aec8a7 (FactsSyntax.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


/-!
This defines a compact way of saying “Magma G satisfies this list of equations, but refutes these
others”.
-/

/--
Concise syntax for stating that a given magma satisfies resp. refutes multiple of the equations:

```
Facts G [1, 2] [4, 5] ↔ Equation1 G ∧ Equation2 G ∧ ¬ Equation4 G ∧ ¬ Equation5 G
```
-/
syntax "Facts " term:max " [" num,* "] " " [" num,* "]" : term

-- Many ways to skin the cat here.
-- Using a macro that iterative expands the list was too slow,
-- so here we elaborate to a `Expr` directly.

open Lean Meta Elab Term Tactic Parser.Term in
elab_rules : term | `(Facts $G [ $sats,* ] [ $refs,*]) => do
  let G ← elabTerm G none
  let some u := (← getLevel G).dec | throwError "expected G to be a type"
  let inst ← synthInstance (mkApp (mkConst ``Magma [u]) G)
  let s := sats.getElems.map fun ⟨s⟩ =>
    let n := Name.mkStr `ETP s!"Equation{s.toNat}"
    mkApp2 (mkConst n [u]) G inst
  let r := refs.getElems.map fun ⟨s⟩ =>
    let n := Name.mkStr `ETP s!"Equation{s.toNat}"
    mkApp (mkConst ``Not) (mkApp2 (mkConst n [u]) G inst)
  let e := mkAndN (s ++ r).toList
  return e

end ETP
