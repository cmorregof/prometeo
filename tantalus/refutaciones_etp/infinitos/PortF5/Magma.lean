import Mathlib

/- Derivado de teorth/equational_theories, commit 1aec8a7 (Magma.lean), Apache-2.0. Modificado: namespace ETP,
recortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/

namespace ETP

class Magma (α : Type _) where
  op : α → α → α

scoped infix:65 " ◇ " => Magma.op

end ETP
