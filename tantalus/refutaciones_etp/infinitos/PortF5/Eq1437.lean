import PortF5.FactsSyntax
import PortF5.Ecuaciones

/- Derivado de teorth/equational_theories, commit 1aec8a7 (ManuallyProved/Equation1437.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP


namespace Eq1437

def op (a b : ℕ × Fin 3) : ℕ × Fin 3 :=
  (if a.2 = b.2 + 2 then
      (if a.1 = 0 then b.1 else a.1 - 1)
    else a.1 + 1,
    b.2 + 1)

theorem satisface1437 : ∀ x y z : ℕ × Fin 3, x = op (op x x) (op y (op z x)) := by
  intro x y z
  simp [op, add_assoc]

end Eq1437

end ETP
