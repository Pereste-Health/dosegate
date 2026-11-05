/-
The part of a FHIR R4 MedicationRequest that the gate reads, and the patient
phrases it prints for each field. Only orders with status "active" can be
spoken. A missing field is `none`, and asking for a missing field blocks.
-/
import DoseGate.Units
import DoseGate.Tokens

namespace DoseGate

inductive Route where
  | oral | sublingual | subcutaneous | intramuscular | intravenous
  | inhaled | topical | transdermal | rectal | ophthalmic | otic | nasal
  deriving Repr, DecidableEq, Inhabited

namespace Route

def ofSnomed? : String → Option Route
  | "26643006" => some oral
  | "37839007" => some sublingual
  | "34206005" => some subcutaneous
  | "78421000" => some intramuscular
  | "47625008" => some intravenous
  | "447694001" => some inhaled
  | "6064005" => some topical
  | "45890007" => some transdermal
  | "37161004" => some rectal
  | "54485002" => some ophthalmic
  | "10547007" => some otic
  | "46713006" => some nasal
  | _ => none

def phrase : Route → List Char
  | oral => "by mouth".toList
  | sublingual => "under the tongue".toList
  | subcutaneous => "as a shot under the skin".toList
  | intramuscular => "as a shot into a muscle".toList
  | intravenous => "into a vein".toList
  | inhaled => "breathed in".toList
  | topical => "on the skin".toList
  | transdermal => "as a skin patch".toList
  | rectal => "in the rectum".toList
  | ophthalmic => "in the eye".toList
  | otic => "in the ear".toList
  | nasal => "in the nose".toList

end Route

inductive PeriodUnit where
  | h | d | wk | mo
  deriving Repr, DecidableEq, Inhabited

def PeriodUnit.ofCode? : String → Option PeriodUnit
  | "h" => some .h
  | "d" => some .d
  | "wk" => some .wk
  | "mo" => some .mo
  | _ => none

structure Timing where
  frequency : Nat
  period : Nat
  periodUnit : PeriodUnit
  deriving Repr, DecidableEq, Inhabited

structure Dose where
  amount : Dec
  unit : DoseUnit
  deriving Repr, DecidableEq, Inhabited

structure MedReq where
  id : List Char
  active : Bool
  drug : List Char
  dose : Option Dose
  timing : Option Timing
  route : Option Route
  asNeeded : Bool
  deriving Repr, DecidableEq, Inhabited

inductive Field where
  | drug | dose | frequency | route | sig | daily
  deriving Repr, DecidableEq, Inhabited

def Field.ofName? : List Char → Option Field
  | ['d', 'r', 'u', 'g'] => some .drug
  | ['d', 'o', 's', 'e'] => some .dose
  | ['f', 'r', 'e', 'q', 'u', 'e', 'n', 'c', 'y'] => some .frequency
  | ['r', 'o', 'u', 't', 'e'] => some .route
  | ['s', 'i', 'g'] => some .sig
  | ['d', 'a', 'i', 'l', 'y'] => some .daily
  | _ => none

def Field.name : Field → List Char
  | .drug => "drug".toList
  | .dose => "dose".toList
  | .frequency => "frequency".toList
  | .route => "route".toList
  | .sig => "sig".toList
  | .daily => "daily".toList

def fmtDose (d : Dose) : List Char :=
  fmtDec d.amount ++ ' ' :: d.unit.name (d.amount.normalize == ⟨1, 0⟩)

def timesWord : Nat → List Char
  | 1 => "once".toList
  | 2 => "twice".toList
  | 3 => "three times".toList
  | 4 => "four times".toList
  | n => fmtDec ⟨n, 0⟩ ++ " times".toList

def unitWord : PeriodUnit → Bool → List Char
  | .h, true => "hour".toList
  | .h, false => "hours".toList
  | .d, true => "day".toList
  | .d, false => "days".toList
  | .wk, true => "week".toList
  | .wk, false => "weeks".toList
  | .mo, true => "month".toList
  | .mo, false => "months".toList

def fmtTiming (t : Timing) : Option (List Char) :=
  if t.frequency = 0 ∨ t.period = 0 then none
  else if t.periodUnit = .h ∧ 1 < t.frequency then none
  else if t.period = 1 then
    if t.frequency = 1 ∧ t.periodUnit = .h then some ("every hour".toList)
    else some (timesWord t.frequency ++ " a ".toList ++ unitWord t.periodUnit true)
  else if t.frequency = 1 then
    some ("every ".toList ++ fmtDec ⟨t.period, 0⟩ ++ ' ' :: unitWord t.periodUnit false)
  else
    some (timesWord t.frequency ++ " every ".toList ++ fmtDec ⟨t.period, 0⟩ ++ ' ' :: unitWord t.periodUnit false)

def fmtFrequency (m : MedReq) : Option (List Char) :=
  match m.timing, m.asNeeded with
  | some t, false => fmtTiming t
  | some t, true => (fmtTiming t).map (· ++ " as needed".toList)
  | none, true => some "as needed".toList
  | none, false => none

def dosesPerDay? (t : Timing) : Option Nat :=
  match t.periodUnit with
  | .d => if t.period = 1 ∧ t.frequency ≠ 0 then some t.frequency else none
  | .h => if t.period ≠ 0 ∧ 24 % t.period = 0 ∧ t.frequency ≠ 0 then some (t.frequency * (24 / t.period)) else none
  | _ => none

def dailyDose? (m : MedReq) : Option Dose :=
  if m.asNeeded then none
  else match m.dose, m.timing with
    | some d, some t =>
      if fmtTiming t = none then none
      else (dosesPerDay? t).map fun k => ⟨⟨d.amount.mant * k, d.amount.scale⟩, d.unit⟩
    | _, _ => none

def drugNameChar (c : Char) : Bool := c.isAlpha || c == ' ' || c == '-'

def drugNameOk (cs : List Char) : Bool :=
  cs.any Char.isAlpha && cs.length ≤ 60 && (tokens cs).length ≤ 5 && cs.all drugNameChar &&
    !(tokens cs).any isForbidden && !(tokens cs).any isNameWord

def fmtField (f : Field) (m : MedReq) : Option (List Char) :=
  match f with
  | .drug => if drugNameOk m.drug then some m.drug else none
  | .daily => (dailyDose? m).map fun d => fmtDose d ++ " a day".toList
  | .dose => m.dose.map fmtDose
  | .route => m.route.map Route.phrase
  | .frequency => fmtFrequency m
  | .sig => do
      let d ← m.dose
      let r ← m.route
      let fr ← fmtFrequency m
      pure (fmtDose d ++ ' ' :: r.phrase ++ ", ".toList ++ fr)

end DoseGate
