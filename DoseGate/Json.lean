import Lean.Data.Json
import DoseGate.Fhir

namespace DoseGate

open Lean (Json)

def jField? (j : Json) (k : String) : Option Json :=
  match j.getObjVal? k with
  | .ok .null | .error _ => none
  | .ok v => some v

def jStr? (j : Json) (k : String) : Option String :=
  (jField? j k).bind (·.getStr?.toOption)

def jArr? (j : Json) (k : String) : List Json :=
  ((jField? j k).bind (·.getArr?.toOption)).getD #[] |>.toList

def jNat? : Json → Option Nat
  | .num n =>
      if n.mantissa < 0 then none
      else
        let m := n.mantissa.toNat
        if m % 10 ^ n.exponent = 0 then some (m / 10 ^ n.exponent) else none
  | _ => none

def jDec? : Json → Option Dec
  | .num n => if n.mantissa < 0 then none else some ⟨n.mantissa.toNat, n.exponent⟩
  | _ => none

def jUnit? (q : Json) : Option DoseUnit :=
  match jStr? q "code" with
  | some c => DoseUnit.ofCode? c
  | none => (jStr? q "unit").bind DoseUnit.ofCode?

def jDose? (q : Json) : Option Dose := do
  let amount ← (jField? q "value").bind jDec?
  let u ← jUnit? q
  pure ⟨amount, u⟩

def jTiming? (r : Json) : Option Timing := do
  let frequency ← (jField? r "frequency").bind jNat?
  let period ← (jField? r "period").bind jNat?
  let periodUnit ← (jStr? r "periodUnit").bind PeriodUnit.ofCode?
  pure ⟨frequency, period, periodUnit⟩

def jRoute? (d : Json) : Option Route :=
  (jArr? ((jField? d "route").getD .null) "coding").findSome? fun c =>
    if jStr? c "system" = some "http://snomed.info/sct" then (jStr? c "code").bind Route.ofSnomed?
    else none

def jDrug (mr : Json) : List Char :=
  let cc := jField? mr "medicationCodeableConcept"
  let text := cc.bind (jStr? · "text")
  let display := cc.bind fun c => (jArr? c "coding").head?.bind (jStr? · "display")
  ((text <|> display).getD "").toList

def jAsNeeded (d : Json) : Bool :=
  match jField? d "asNeededBoolean" with
  | some (.bool b) => b
  | some _ => true
  | none => (jField? d "asNeededCodeableConcept").isSome

def medReqOfJson (mr : Json) : Option MedReq := do
  let id ← jStr? mr "id"
  let active := jStr? mr "status" = some "active"
  let drug := jDrug mr
  match jArr? mr "dosageInstruction" with
  | [d] =>
      let dose := ((jArr? d "doseAndRate").head?.bind (jField? · "doseQuantity")).bind jDose?
      let timing := (jField? d "timing").bind fun t => (jField? t "repeat").bind jTiming?
      pure { id := id.toList, active, drug, dose, timing, route := jRoute? d, asNeeded := jAsNeeded d }
  | _ => pure { id := id.toList, active, drug, dose := none, timing := none, route := none, asNeeded := false }

def bundleChart (b : Json) : List MedReq :=
  (jArr? b "entry").filterMap fun e =>
    (jField? e "resource").bind fun r =>
      if jStr? r "resourceType" = some "MedicationRequest" then medReqOfJson r else none

end DoseGate
