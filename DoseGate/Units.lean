/-
Dose units, their dimensions, and conversion to an exact base amount.

Every unit belongs to one dimension. Amounts are converted to a whole number of
base sub-units (nanograms, nanolitres, thousandths of an international unit,
thousandths of a tablet), so comparing two doses is integer comparison. A dose
that cannot be represented exactly in the base is refused rather than rounded.
-/
import DoseGate.Dec

namespace DoseGate

inductive Dim where
  | mass | volume | intlUnit | count
  deriving Repr, DecidableEq, Inhabited

inductive DoseUnit where
  | mcg | mg | g
  | mL | L
  | unit
  | tablet | capsule | puff | drop
  deriving Repr, DecidableEq, Inhabited

namespace DoseUnit

def dim : DoseUnit → Dim
  | mcg | mg | g => .mass
  | mL | L => .volume
  | unit => .intlUnit
  | tablet | capsule | puff | drop => .count

def factor : DoseUnit → Nat
  | mcg => 1000
  | mg => 1000000
  | g => 1000000000
  | mL => 1000000
  | L => 1000000000
  | unit => 1000
  | tablet | capsule | puff | drop => 1000

def ofCode? : String → Option DoseUnit
  | "ug" | "mcg" => some mcg
  | "mg" => some mg
  | "g" => some g
  | "mL" | "ml" => some mL
  | "L" | "l" => some L
  | "U" | "[iU]" | "[IU]" | "unit" | "units" => some unit
  | "{tbl}" | "TAB" | "tablet" | "tablets" => some tablet
  | "{cap}" | "{capsule}" | "CAP" | "capsule" | "capsules" => some capsule
  | "{puff}" | "puff" | "puffs" => some puff
  | "[drp]" | "{drop}" | "drop" | "drops" => some drop
  | _ => none

def name (u : DoseUnit) (one : Bool) : List Char :=
  (match u, one with
    | mcg, _ => "mcg"
    | mg, _ => "mg"
    | g, _ => "g"
    | mL, _ => "mL"
    | L, _ => "L"
    | unit, true => "unit"
    | unit, false => "units"
    | tablet, true => "tablet"
    | tablet, false => "tablets"
    | capsule, true => "capsule"
    | capsule, false => "capsules"
    | puff, true => "puff"
    | puff, false => "puffs"
    | drop, true => "drop"
    | drop, false => "drops").toList

end DoseUnit

structure Qty where
  dim : Dim
  base : Nat
  deriving Repr, DecidableEq

def toQty (d : Dec) (u : DoseUnit) : Option Qty :=
  let num := d.mant * u.factor
  if num % 10 ^ d.scale = 0 then some ⟨u.dim, num / 10 ^ d.scale⟩ else none

def Qty.le? (a b : Qty) : Option Bool :=
  if a.dim = b.dim then some (decide (a.base ≤ b.base)) else none

end DoseGate
