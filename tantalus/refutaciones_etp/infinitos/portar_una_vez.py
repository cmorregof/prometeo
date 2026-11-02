"""Una sola vez: pasa las fuentes del ETP (commit 1aec8a7, Apache-2.0) a PortF5/, con namespace ETP y solo lo que usan
las 30 tareas F5. Lo que venga después de esto se corrige a mano en PortF5/ y queda en LEEME_PORT.md."""
import re,sys,pathlib
AQUI=pathlib.Path(__file__).resolve().parent
if (AQUI/"PortF5").exists(): raise SystemExit("PortF5 ya existe y tiene arreglos a mano (ver LEEME_PORT.md); no lo sobrescribo.")
F=AQUI.parent/"testigos_etp"/"fuentes_f5"; P=AQUI/"PortF5"; S=pathlib.Path(sys.argv[1])
CAB="/- Derivado de teorth/equational_theories, commit 1aec8a7 ({src}), Apache-2.0. Modificado: namespace ETP,\nrecortado a lo que usan las tareas F5 y ajustado a Lean 4.34.1. -/\n"
def cuerpo(n):
    s=(F/n).read_text()
    s=re.sub(r"^(public )?import .*\n","",s,flags=re.M)
    s=s.replace("@[equational_result]\n","").replace("_root_.","")
    return s
def escribe(nom,src,imps,txt):
    (P/f"{nom}.lean").write_text("".join(f"import {i}\n" for i in imps)+"\n"+CAB.format(src=src)+"\nnamespace ETP\n\n"+txt.rstrip()+"\n\nend ETP\n")
def corta(s,a,b=None):
    """Quita desde la línea que empieza por a hasta (sin incluir) la que empieza por b."""
    i=s.index(a); j=s.index(b,i+1) if b else len(s)
    return s[:i]+s[j:]
# Magma
escribe("Magma","Magma.lean",["Mathlib"],"class Magma (α : Type _) where\n  op : α → α → α\n\nscoped infix:65 \" ◇ \" => Magma.op\n")
# FreeMagma mínimo
escribe("FreeMagma","FreeMagma.lean",["PortF5.Magma"],'''universe u

inductive FreeMagma (α : Type u)
  | Leaf : α → FreeMagma α
  | Fork : FreeMagma α → FreeMagma α → FreeMagma α
  deriving DecidableEq

instance (α : Type u) [Inhabited α] : Inhabited (FreeMagma α) where
  default := .Leaf default

instance (α : Type u) : Magma (FreeMagma α) where
  op := FreeMagma.Fork

scoped infixl:65 " ⋆ " => FreeMagma.Fork

@[simp]
theorem FreeMagma_op_eq_fork (α : Type u) (a b : FreeMagma α) : a ◇ b = a ⋆ b := rfl

namespace FreeMagma

@[simp] def length {α} : FreeMagma α → Nat
  | .Leaf _ => 1
  | .Fork m1 m2 => FreeMagma.length m1 + FreeMagma.length m2

end FreeMagma
''')
# Facts
fs=cuerpo("FactsSyntax.lean"); fs=fs[:fs.index("open Lean Meta Elab Term Tactic Parser.Term in\n/--\nA relatively crude")]
fs=fs.replace('.mkSimple s!"Equation{s.toNat}"','Name.mkStr `ETP s!"Equation{s.toNat}"')
escribe("FactsSyntax","FactsSyntax.lean",["PortF5.Magma"],fs)
# Facts recortados y ecuaciones
quitar_c2=[("namespace rw115","namespace rw1276"),("namespace rw1431","namespace rw1523"),("namespace rw1630","namespace rw3588")]
c2=cuerpo("Confluence2.lean")
for a,b in quitar_c2: c2=corta(c2,a,b)
c4=corta(cuerpo("Confluence4.lean"),"namespace rw2126")
c3=cuerpo("Confluence3.lean")
def facts(s,de,nuevo):
    assert f"Facts G [{de}] [" in s,de
    return re.sub(r"Facts G \[%s\] \[[^\]]*\]"%de,f"Facts G [{de}] [{nuevo}]",s)
c2=facts(facts(facts(c2,"1276","4332"),"1523","2035, 2124, 2132"),"3588","3878, 3917, 3955")
c3=facts(c3,"481","1496, 2035, 3050, 3056")
c4=facts(facts(c4,"1443","4065, 4067"),"1633","4268, 4282")
base=["PortF5.Confluence","PortF5.ConfluenceSystem"]
cf=cuerpo("Confluence.lean")
escribe("Confluence","Confluence.lean",["PortF5.FreeMagma","PortF5.FactsSyntax","PortF5.Ecuaciones"],cf)
escribe("ConfluenceSystem","ConfluenceSystem.lean",["PortF5.Confluence"],cuerpo("ConfluenceSystem.lean"))
for n,t in (("Confluence2",c2),("Confluence3",c3),("Confluence4",c4)):
    escribe(n,n+".lean",["PortF5.ConfluenceSystem"],t)
# Modelos sobre ℕ
escribe("Eq1437","ManuallyProved/Equation1437.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones"],cuerpo("Equation1437.lean").replace("Equation4269","Equation4316"))
e59=cuerpo("Equation1659.lean").replace("private ","")
e59=re.sub(r"Facts G \[1659\]\s*\[[^\]]*\]","Facts G [1659] [1655, 3519]",e59)
escribe("Eq1659","ManuallyProved/Equation1659.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones"],e59)
e61=cuerpo("Equation1661.lean").replace("private ","")
e61=e61[:e61.index("/-- Dual of the previous result -/")]
e61=e61[:e61.index("theorem Equation1661_not_implies_Equation1657")]
escribe("Eq1661","ManuallyProved/Equation1661.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones"],e61)
e01=cuerpo("Equation1701.lean").replace("private ","")
e01=e01[:e01.index("theorem Equation1701_facts :")]
escribe("Eq1701","ManuallyProved/Equation1701.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones"],e01)
inf=cuerpo("InfModel.lean"); i=inf.index("theorem Equation3994_not_implies_Equation3588"); j=inf.index("/--\nDual of the above.")
escribe("Inf3994","InfModel.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones"],inf[i:j])
escribe("OrLemmas","Generated/Greedy/OrLemmas.lean",["Mathlib"],cuerpo("OrLemmas.lean"))
sp=(F/"Superposition.lean").read_text(); sp=re.sub(r"^import .*\n","",sp,flags=re.M)
(P/"Superposition.lean").write_text("import Mathlib\n\n"+CAB.format(src="Superposition.lean").replace("Modificado: namespace ETP,\nrecortado a lo que usan las tareas F5 y ajustado","Ajustado")+sp)
g=cuerpo("Eq883.lean")
for quita in ("counter2238",):
    i=g.index(f"set_option maxRecDepth 1000 in\nnoncomputable def PartialSolution.{quita}"); j=g.index("set_option maxRecDepth 1000 in\nnoncomputable def PartialSolution.counter2304")
    g=g[:i]+g[j:]
escribe("Eq883","Generated/Greedy/Eq883.lean",["PortF5.FactsSyntax","PortF5.Ecuaciones","PortF5.Superposition","PortF5.OrLemmas"],g)
# Ecuaciones que aparecen en cualquier archivo portado
nums=set()
for f in P.glob("*.lean"):
    t=f.read_text()
    nums|=set(map(int,re.findall(r"Equation(\d+)",t)))
    for m in re.findall(r"Facts G \[([^\]]*)\]\s*\[([^\]]*)\]",t):
        for g_ in m: nums|=set(map(int,re.findall(r"\d+",g_)))
nums|={481,1276,1443,1633,1661,1659,1701,1437,883,3588,3994,1523,4332}
leyes={}
for f in S.glob("Equations/*.lean"):
    for m in re.finditer(r"^(?:-- )?equation (\d+)\s*:=\s*(.+)$",f.read_text(),re.M): leyes[int(m[1])]=m[2].strip()
sal=[]
for n in sorted(nums):
    izq,der=leyes[n].split(" = "); vs=[]
    for v in re.findall(r"[a-z]\w*",leyes[n]):
        if v not in vs: vs.append(v)
    sal.append(f"abbrev Equation{n} (G : Type _) [Magma G] := ∀ {' '.join(vs)} : G, {leyes[n]}\n")
escribe("Ecuaciones","Equations/Eqns*.lean (solo las usadas)",["PortF5.Magma"],"".join(sal))
print(sorted(nums))
