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

def jDose? (q : Json) : Option Dose :=
  match (jField? q "value").bind jDec? with
  | some amount => if amount.mant = 0 then none else (jUnit? q).map fun u => ⟨amount, u⟩
  | none => none

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

def trimmed (s : String) : String := s.trimAscii.toString

def sameName (a b : String) : Bool := (trimmed a).toLower == (trimmed b).toLower

def namePrefixOf (t d : String) : Bool :=
  let tl := (trimmed t).toLower.toList
  let dl := (trimmed d).toLower.toList
  tl.isPrefixOf dl && ((dl.drop tl.length).head?.map (fun c => !c.isAlpha)).getD true

def displaysOf (cc : Json) : List String :=
  ((jArr? cc "coding").filterMap fun c => (jStr? c "display").map trimmed).filter (!·.isEmpty)

def jDrug (mr : Json) : List Char :=
  let name : String :=
    match jField? mr "medicationCodeableConcept" with
    | none => ""
    | some cc =>
        let displays := displaysOf cc
        let common := match displays with
          | d :: ds => if ds.all (sameName · d) then d else ""
          | [] => ""
        match (jStr? cc "text").map trimmed with
        | some t => if t.isEmpty then common else if displays.all (namePrefixOf t ·) then t else ""
        | none => common
  name.toList

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

def nonEmptyJson : Json → Bool
  | .null => false
  | .arr a => !a.isEmpty
  | .obj kvs => !kvs.isEmpty
  | .str s => !s.isEmpty
  | _ => true

def routeTerms : List (String × String) :=
  [("26643006", "Oral route"), ("26643006", "Oral use"), ("37839007", "Sublingual route"),
   ("34206005", "Subcutaneous route"), ("78421000", "Intramuscular route"),
   ("47625008", "Intravenous route"), ("447694001", "Inhalation route"), ("6064005", "Topical route"),
   ("45890007", "Transdermal route"), ("37161004", "Rectal route"), ("54485002", "Ophthalmic route"),
   ("10547007", "Otic route"), ("46713006", "Nasal route")]

def routeNames (code : String) : List String :=
  (routeTerms.filter (·.1 == code)).map (·.2) ++
    ((Route.ofSnomed? code).map fun r => String.ofList r.phrase).toList

def routeTextsOk (route : Json) : Bool :=
  let codings := jArr? route "coding"
  let codes := codings.filterMap fun c => if jStr? c "system" = some snomedSystem then jStr? c "code" else none
  let accepted := codes.flatMap routeNames
  let texts := (jField? route "text").toList ++ codings.filterMap (jField? · "display")
  texts.all fun t =>
    match t with
    | .str s => accepted.any (sameName · s)
    | _ => false

def unitsOfMeasure : String := "http://unitsofmeasure.org"

def standardAbbreviations : DoseUnit → List String
  | .mcg => ["ug"]
  | .unit => ["u", "iu"]
  | .tablet => ["tab", "tabs"]
  | .capsule => ["cap", "caps"]
  | .drop => ["gtt", "gtts"]
  | _ => []

def unitAccepted (code unit : String) : Bool :=
  let u := (trimmed unit).toLower
  match DoseUnit.ofCode? code with
  | none => u == code.toLower
  | some d =>
      u == code.toLower || u == (String.ofList (d.name true)).toLower
        || u == (String.ofList (d.name false)).toLower || (standardAbbreviations d).contains u

def doseQuantityOk (q : Json) : Bool :=
  (match jField? q "system" with
    | none => true
    | some (.str s) => s == unitsOfMeasure
    | some _ => false) &&
  (match jField? q "unit", jField? q "code" with
    | some (.str u), some (.str c) => unitAccepted c u
    | some _, some _ => false
    | _, _ => true)

def failsCheck (o : Option Json) (ok : Json → Bool) : Bool :=
  match o with
  | some v => !ok v
  | none => false

def priorRefs (orders : List Json) : List String :=
  orders.filterMap fun mr => (jField? mr "priorPrescription").bind (jStr? · "reference")

partial def hasExtensionKey : Json → Bool
  | .obj kvs => kvs.any fun k v => k == "extension" || k == "modifierExtension" || hasExtensionKey v
  | .arr a => a.any hasExtensionKey
  | _ => false

def keysWithin (ks : List String) : Json → Bool
  | .obj kvs => kvs.all fun k _ => ks.contains k
  | _ => false

def allowedIfPresent (ks : List String) (j : Option Json) : Bool :=
  match j with
  | some v => keysWithin ks v
  | none => true

def dosageKeys : List String :=
  ["timing", "route", "doseAndRate", "asNeededBoolean", "sequence", "text", "additionalInstruction",
   "patientInstruction"]

def dosageAllowed (d : Json) : Bool :=
  keysWithin dosageKeys d
  && allowedIfPresent ["repeat", "code"] (jField? d "timing")
  && allowedIfPresent ["frequency", "period", "periodUnit"] ((jField? d "timing").bind (jField? · "repeat"))
  && allowedIfPresent ["coding", "text"] (jField? d "route")
  && (((jField? d "route").map fun r => jArr? r "coding").getD []).all
      (keysWithin ["system", "code", "display", "version", "userSelected"])
  && (jArr? d "doseAndRate").all fun r =>
      keysWithin ["doseQuantity"] r
      && allowedIfPresent ["value", "unit", "code", "system"] (jField? r "doseQuantity")

def courseOfTherapyOk (mr : Json) : Bool :=
  match jField? mr "courseOfTherapyType" with
  | none => true
  | some cc =>
      let codings := jArr? cc "coding"
      !codings.isEmpty && codings.all fun c => jStr? c "code" == some "continuous"

def orderKeys : List String :=
  ["resourceType", "id", "meta", "implicitRules", "language", "identifier", "status", "intent", "category",
   "priority", "doNotPerform", "reportedBoolean", "reportedReference", "medicationCodeableConcept",
   "medicationReference", "subject", "encounter", "supportingInformation", "authoredOn", "requester",
   "performer", "performerType", "recorder", "reasonCode", "reasonReference", "instantiatesCanonical",
   "instantiatesUri", "basedOn", "groupIdentifier", "insurance", "dispenseRequest", "substitution",
   "eventHistory", "dosageInstruction", "note", "courseOfTherapyType", "priorPrescription"]

def closedOrder (mr : Json) (id : String) (refs : List String) : Bool :=
  hasExtensionKey mr
  || !keysWithin orderKeys mr
  || hasAny (some mr) ["priorPrescription"]
  || !courseOfTherapyOk mr
  || refs.contains ("MedicationRequest/" ++ id)
  || ((jField? mr "meta").bind (jField? · "security")).any nonEmptyJson
  || ((jField? mr "dispenseRequest").bind (jField? · "validityPeriod")).isSome

def closedDosage (d : Json) : Bool :=
  let rate := (jArr? d "doseAndRate").head?
  hasAny (some d) ["site", "method"]
  || failsCheck (jField? d "route") routeTextsOk
  || hasAny rate ["rateQuantity", "rateRatio", "rateRange", "type"]
  || failsCheck (rate.bind (jField? · "doseQuantity")) doseQuantityOk
  || !dosageAllowed d

def hasFreeText (mr d : Json) : Bool :=
  hasAny (some d) ["text", "additionalInstruction", "patientInstruction"] || hasAny (some mr) ["note"]

def medReqOfJson (ignoreFreeText : Bool) (patient : Option String) (refs : List String) (mr : Json) : Option MedReq := do
  let id ← jStr? mr "id"
  let active := isActive patient mr
  let drug := jDrug mr
  match jArr? mr "dosageInstruction" with
  | [d] =>
      if failsClosed d || closedOrder mr id refs || closedDosage d || (!ignoreFreeText && hasFreeText mr d) then
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

def chartFrom (ignoreFreeText : Bool) (patient : Option String) (orders : List Json) : List MedReq :=
  orders.filterMap (medReqOfJson ignoreFreeText patient (priorRefs orders))

def bundleChart (ignoreFreeText : Bool) (patient : Option String) (b : Json) : List MedReq :=
  chartFrom ignoreFreeText patient (bundleResources b)

def orderResources (req : Json) : List Json :=
  match jField? req "bundle" with
  | some b => bundleResources b
  | none => jArr? req "medicationRequests"

def subjectRef (mr : Json) : Option String :=
  ((jField? mr "subject").bind (jStr? · "reference")).filter fun r => !r.isEmpty

def subjectProblem (patient : Option String) (req : Json) : Option String :=
  let refs := (orderResources req).map subjectRef
  if refs.any Option.isNone then
    if patient.isSome then some "every MedicationRequest needs a subject.reference string"
    else some "every MedicationRequest needs a subject.reference string when the request has no patient field"
  else if patient.isNone && (refs.filterMap id).eraseDups.length > 1 then
    some "the orders reference more than one subject, so the request needs a patient field"
  else none

def bundleShapeBad (req : Json) : Bool :=
  match req.getObjVal? "bundle" with
  | .error _ => false
  | .ok b =>
      match b.getObjVal? "entry" with
      | .ok (.arr _) => false
      | _ => true

def medicationRequestsShapeBad (req : Json) : Bool :=
  match req.getObjVal? "medicationRequests" with
  | .error _ => false
  | .ok (.arr _) => false
  | .ok _ => true

def bundleTypeBad (req : Json) : Bool :=
  match (jField? req "bundle").bind (jField? · "type") with
  | none => false
  | some (.str "searchset") => false
  | some (.str "collection") => false
  | some _ => true

def bundleRequestBad (req : Json) : Bool :=
  (((jField? req "bundle").map fun b => jArr? b "entry").getD []).any fun e => (jField? e "request").isSome

def shapeProblem (req : Json) : Option String :=
  if (jField? req "bundle").isSome && (jField? req "medicationRequests").isSome then
    some "the request has both bundle and medicationRequests, so it is ambiguous; send only one of them"
  else if bundleShapeBad req then some "bundle must be an object with an entry array"
  else if bundleTypeBad req then some "bundle type must be searchset or collection"
  else if bundleRequestBad req then some "a bundle entry has a request key, which the gate does not accept"
  else if medicationRequestsShapeBad req then some "medicationRequests must be an array"
  else if (orderResources req).any (fun mr => (jStr? mr "id").isNone) then
    some "every MedicationRequest needs an id string"
  else none

def patientOf (req : Json) : Except String (Option String) :=
  match jField? req "patient" with
  | none => .ok none
  | some (.str p) => if p.isEmpty then .error "patient must be a non-empty string" else .ok (some p)
  | some _ => .error "patient must be a string"

def chartOf (ignoreFreeText : Bool) (patient : Option String) (req : Json) : Option (List MedReq) :=
  match jField? req "bundle", jField? req "medicationRequests" with
  | some b, _ => some (bundleChart ignoreFreeText patient b)
  | none, some _ => some (chartFrom ignoreFreeText patient (jArr? req "medicationRequests"))
  | none, none => none

end DoseGate
