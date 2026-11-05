/-
Exact decimal numbers and their canonical text form.

A dose is never stored as a float. `Dec` holds `mant / 10 ^ scale` exactly,
so 0.1 + 0.2 is 0.3 and 0.125 mg is 0.125 mg.

The printed form follows the ISMP and Joint Commission rules for doses:
a leading zero before a decimal point ("0.5", never ".5") and no trailing
zero after it ("1", never "1.0").
-/
namespace DoseGate

structure Dec where
  mant : Nat
  scale : Nat
  deriving Repr, DecidableEq, Inhabited

namespace Dec

def Eqv (a b : Dec) : Prop := a.mant * 10 ^ b.scale = b.mant * 10 ^ a.scale

instance (a b : Dec) : Decidable (Eqv a b) := by unfold Eqv; infer_instance

def normalize : Dec → Dec
  | ⟨m, 0⟩ => ⟨m, 0⟩
  | ⟨m, s + 1⟩ => if m % 10 = 0 then normalize ⟨m / 10, s⟩ else ⟨m, s + 1⟩

def IsNormal (d : Dec) : Prop := d.scale = 0 ∨ d.mant % 10 ≠ 0

end Dec

def digitsOf (n : Nat) : List Nat :=
  if n < 10 then [n] else digitsOf (n / 10) ++ [n % 10]
termination_by n
decreasing_by omega

def digitChar (k : Nat) : Char := Char.ofNat (48 + k)

def charDigit? (c : Char) : Option Nat :=
  if c.isDigit then some (c.toNat - 48) else none

def readNat? (cs : List Char) : Option Nat :=
  if cs.isEmpty then none
  else cs.foldlM (fun acc c => (charDigit? c).map (fun k => acc * 10 + k)) 0

def fmtDec (d : Dec) : List Char :=
  let n := d.normalize
  let ds := (digitsOf n.mant).map digitChar
  let padded := List.replicate (n.scale + 1 - ds.length) '0' ++ ds
  let intLen := padded.length - n.scale
  if n.scale = 0 then padded
  else padded.take intLen ++ '.' :: padded.drop intLen

def parseDec? (cs : List Char) : Option Dec :=
  match cs.span (· != '.') with
  | (intPart, []) => (readNat? intPart).map fun m => ⟨m, 0⟩
  | (intPart, _ :: frac) => do
      let i ← readNat? intPart
      let f ← readNat? frac
      pure ⟨i * 10 ^ frac.length + f, frac.length⟩

end DoseGate
