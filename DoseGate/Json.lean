import Lean.Data.Json
import Std.Data.HashSet
import DoseGate.Fhir

namespace DoseGate

open Lean (Json)

inductive Frame where
  | arr
  | obj (keys : Std.HashSet String)

def maxLiteral : Nat := 1000
def maxExponentDigits : Nat := 2
def maxNumbers : Nat := 20000
def maxDepth : Nat := 64
def maxCount : Nat := 1000
def maxOrders : Nat := 5000
def maxOutput : Nat := 65536
def maxSlots : Nat := 400
def maxRequestBytes : Nat := 2000000
def reservedKeys : List String := ["allow", "extraWords"]
def orderIntents : List String :=
  ["order", "original-order", "reflex-order", "filler-order", "instance-order"]

def decodeKey (raw : List Char) : String :=
  match Lean.Json.parse ("\"" ++ String.ofList raw ++ "\"") with
  | .ok (.str s) => s
  | _ => String.ofList raw

def lexString (acc : List Char) : List Char → Option (List Char × List Char)
  | [] => none
  | '"' :: rest => some (acc.reverse, rest)
  | '\\' :: c :: rest => lexString (c :: '\\' :: acc) rest
  | ['\\'] => none
  | c :: rest => lexString (c :: acc) rest

def numChar (c : Char) : Bool :=
  c.isDigit || c == '-' || c == '+' || c == '.' || c == 'e' || c == 'E'

def numberTooBig (lit : List Char) : Bool :=
  lit.length > maxLiteral ||
    ((lit.dropWhile (fun c => c != 'e' && c != 'E')).drop 1
      |>.dropWhile (fun c => c == '+' || c == '-')).length > maxExponentDigits

def scanAux : Nat → Nat → List Char → List Frame → Char → Option String
  | 0, _, _, _, _ => none
  | _ + 1, _, [], _, _ => none
  | fuel + 1, nums, '"' :: rest, stack, prev =>
      match lexString [] rest with
      | none => none
      | some (raw, after) =>
          match stack with
          | .obj keys :: frames =>
              if prev == '{' || prev == ',' then
                let key := decodeKey raw
                if reservedKeys.contains key then
                  some ("request key " ++ key ++ " is not accepted")
                else if keys.contains key then
                  some ("a JSON object repeats the key " ++ key)
                else scanAux fuel nums after (.obj (keys.insert key) :: frames) '"'
              else scanAux fuel nums after stack '"'
          | _ => scanAux fuel nums after stack '"'
  | fuel + 1, nums, '{' :: rest, stack, _ =>
      if stack.length ≥ maxDepth then some "the JSON nests more than 64 levels deep"
      else scanAux fuel nums rest (.obj (∅ : Std.HashSet String) :: stack) '{'
  | fuel + 1, nums, '[' :: rest, stack, _ =>
      if stack.length ≥ maxDepth then some "the JSON nests more than 64 levels deep"
      else scanAux fuel nums rest (.arr :: stack) '['
  | fuel + 1, nums, '}' :: rest, stack, _ => scanAux fuel nums rest stack.tail '}'
  | fuel + 1, nums, ']' :: rest, stack, _ => scanAux fuel nums rest stack.tail ']'
  | fuel + 1, nums, c :: rest, stack, prev =>
      if c.isDigit || c == '-' then
        if nums ≥ maxNumbers then
          some "the request has more than 20000 numeric literals"
        else
          let lit := ((c :: rest).take (maxLiteral + 1)).takeWhile numChar
          if numberTooBig lit then
            some "a number is longer than 1000 characters or has an exponent of 3 or more digits"
          else scanAux fuel (nums + 1) ((c :: rest).drop lit.length) stack '0'
      else scanAux fuel nums rest stack (if c.isWhitespace then prev else c)

def requestProblem (text : String) : Option String :=
  let cs := text.toList
  scanAux (cs.length + 1) 0 cs [] ' '

def jField? (j : Json) (k : String) : Option Json :=
  match j.getObjVal? k with
  | .ok .null | .error _ => none
  | .ok v => some v

def jStr? (j : Json) (k : String) : Option String :=
  (jField? j k).bind (·.getStr?.toOption)

def jArr? (j : Json) (k : String) : List Json :=
  ((jField? j k).bind (·.getArr?.toOption)).getD #[] |>.toList

def hasAny (j : Option Json) (ks : List String) : Bool :=
  match j with
  | some v => ks.any fun k => (jField? v k).isSome
  | none => false

def jCount? : Json → Option Nat
  | .num n =>
      if n.mantissa < 0 then none
      else
        let m := n.mantissa.toNat
        let v := m / 10 ^ n.exponent
        if m % 10 ^ n.exponent = 0 ∧ v ≤ maxCount then some v else none
  | _ => none

def jDec? : Json → Option Dec
  | .num n =>
      if n.mantissa < 0 ∨ n.exponent > 9 ∨ 10 ^ 15 ≤ n.mantissa.toNat then none
      else some ⟨n.mantissa.toNat, n.exponent⟩
  | _ => none

def jUnit? (q : Json) : Option DoseUnit :=
  match jField? q "code" with
  | some (.str c) => DoseUnit.ofCode? c
  | some _ => none
  | none => (jStr? q "unit").bind DoseUnit.ofCode?

def jDose? (q : Json) : Option Dose := do
  let amount ← (jField? q "value").bind jDec?
  let u ← jUnit? q
  pure ⟨amount, u⟩

def jTiming? (r : Json) : Option Timing := do
  let frequency ← (jField? r "frequency").bind jCount?
  let period ← (jField? r "period").bind jCount?
  let periodUnit ← (jStr? r "periodUnit").bind PeriodUnit.ofCode?
  pure ⟨frequency, period, periodUnit⟩

def snomedSystem : String := "http://snomed.info/sct"

def jRoute? (d : Json) : Option Route :=
  let codings := jArr? ((jField? d "route").getD .null) "coding"
  let routes := codings.map fun c =>
    if jStr? c "system" = some snomedSystem then (jStr? c "code").bind Route.ofSnomed?
    else none
  if routes.all Option.isSome then
    match (routes.filterMap id).eraseDups with
    | [r] => some r
    | _ => none
  else none

def jDrug (mr : Json) : List Char :=
  let cc := jField? mr "medicationCodeableConcept"
  let text := cc.bind (jStr? · "text")
  let display := cc.bind fun c => (jArr? c "coding").head?.bind (jStr? · "display")
  ((text <|> display).getD "").toList

def jAsNeeded (d : Json) : Bool :=
  match jField? d "asNeededBoolean" with
  | some (.bool b) => b
  | _ => false

def failsClosed (d : Json) : Bool :=
  let timing := jField? d "timing"
  let repeatOf := timing.bind (jField? · "repeat")
  let doseRates := jArr? d "doseAndRate"
  let first := doseRates.head?
  hasAny timing ["code"]
  || hasAny repeatOf ["frequencyMax", "periodMax", "duration", "durationMax", "durationUnit",
      "countMax", "boundsDuration", "boundsRange", "boundsPeriod", "count", "offset",
      "dayOfWeek", "timeOfDay", "when"]
  || hasAny (some d) ["maxDosePerPeriod", "maxDosePerAdministration", "maxDosePerLifetime",
      "asNeededCodeableConcept"]
  || hasAny first ["doseRange"]
  || hasAny (first.bind (jField? · "doseQuantity")) ["comparator"]
  || (match jField? d "asNeededBoolean" with
      | some (.bool _) | none => false
      | some _ => true)
  || doseRates.length > 1

def doNotPerform (mr : Json) : Bool :=
  match jField? mr "doNotPerform" with
  | some (.bool false) | none => false
  | some _ => true

def subjectMatches (patient : Option String) (mr : Json) : Bool :=
  match patient with
  | none => true
  | some p =>
      match (jField? mr "subject").bind (fun s => jStr? s "reference") with
      | some r => r == "Patient/" ++ p || r == "urn:uuid:" ++ p
      | none => false

def isActive (patient : Option String) (mr : Json) : Bool :=
  jStr? mr "status" == some "active" &&
    (match jStr? mr "intent" with
      | some i => orderIntents.contains i
      | none => false) &&
    !doNotPerform mr && subjectMatches patient mr

def hasValidityEnd (mr : Json) : Bool :=
  hasAny ((jField? mr "dispenseRequest").bind (jField? · "validityPeriod")) ["end"]

def medReqOfJson (patient : Option String) (mr : Json) : Option MedReq := do
  let id ← jStr? mr "id"
  let active := isActive patient mr
  let drug := jDrug mr
  match jArr? mr "dosageInstruction" with
  | [d] =>
      if failsClosed d || hasValidityEnd mr then
        pure { id := id.toList, active, drug, dose := none, timing := none, route := none, asNeeded := false }
      else
        let dose := ((jArr? d "doseAndRate").head?.bind (jField? · "doseQuantity")).bind jDose?
        let timing := (jField? d "timing").bind fun t => (jField? t "repeat").bind jTiming?
        pure { id := id.toList, active, drug, dose, timing, route := jRoute? d, asNeeded := jAsNeeded d }
  | _ => pure { id := id.toList, active, drug, dose := none, timing := none, route := none, asNeeded := false }

def bundleResources (b : Json) : List Json :=
  (jArr? b "entry").filterMap fun e =>
    (jField? e "resource").bind fun r =>
      if jStr? r "resourceType" = some "MedicationRequest" then some r else none

def bundleChart (patient : Option String) (b : Json) : List MedReq :=
  (bundleResources b).filterMap (medReqOfJson patient)

def orderResources (req : Json) : List Json :=
  match jField? req "bundle" with
  | some b => bundleResources b
  | none => jArr? req "medicationRequests"

def subjectRef (mr : Json) : Option String :=
  ((jField? mr "subject").bind (jStr? · "reference")).filter fun r => !r.isEmpty

def subjectProblem (patient : Option String) (req : Json) : Option String :=
  if patient.isSome then none
  else
    let refs := (orderResources req).map subjectRef
    if refs.any Option.isNone then
      some "every MedicationRequest needs a subject.reference string when the request has no patient field"
    else if (refs.filterMap id).eraseDups.length > 1 then
      some "the orders reference more than one subject, so the request needs a patient field"
    else none

def patientOf (req : Json) : Except String (Option String) :=
  match jField? req "patient" with
  | none => .ok none
  | some (.str p) => if p.isEmpty then .error "patient must be a non-empty string" else .ok (some p)
  | some _ => .error "patient must be a string"

def chartOf (patient : Option String) (req : Json) : Option (List MedReq) :=
  match jField? req "bundle", jField? req "medicationRequests" with
  | some b, _ => some (bundleChart patient b)
  | none, some _ => some ((jArr? req "medicationRequests").filterMap (medReqOfJson patient))
  | none, none => none

end DoseGate
