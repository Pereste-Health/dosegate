import Lean.Data.Json
import Std.Data.HashSet
import DoseGate.Fhir
import DoseGate.Lexicon

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
def statusCodes : List String :=
  ["active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"]
def intentCodes : List String :=
  ["proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"]
def priorityCodes : List String := ["routine", "urgent", "asap", "stat"]
def periodUnitCodes : List String := ["s", "min", "h", "d", "wk", "mo", "a"]
def requestKeys : List String := ["output", "bundle", "medicationRequests", "patient"]
def bundleKeys : List String := ["resourceType", "id", "meta", "type", "timestamp", "total", "link", "entry"]
def entryKeys : List String := ["fullUrl", "resource", "search"]
def linkRelations : List String := ["self", "next", "previous", "prev", "first", "last"]
def searchModes : List String := ["match", "include", "outcome"]
def eventResourceTypes : List String := ["MedicationStatement", "MedicationDispense", "MedicationAdministration"]

def snomedSystem : String := "http://snomed.info/sct"
def rxnormSystem : String := "http://www.nlm.nih.gov/research/umls/rxnorm"
def ndcSystem : String := "http://hl7.org/fhir/sid/ndc"
def icd10cmSystem : String := "http://hl7.org/fhir/sid/icd-10-cm"
def icd10System : String := "http://hl7.org/fhir/sid/icd-10"
def categorySystem : String := "http://terminology.hl7.org/CodeSystem/medicationrequest-category"
def courseSystem : String := "http://terminology.hl7.org/CodeSystem/medicationrequest-course-of-therapy"
def unitsOfMeasure : String := "http://unitsofmeasure.org"
def reasonSystems : List String := [snomedSystem, icd10cmSystem, icd10System]
def medicationSystems : List String := [rxnormSystem, ndcSystem, snomedSystem]
def categoryTerms : List (String × String) :=
  [("inpatient", "Inpatient"), ("outpatient", "Outpatient"), ("community", "Community"), ("discharge", "Discharge")]
def courseTerms : List (String × String) :=
  [("continuous", "Continuous long term therapy"), ("acute", "Short course (acute) therapy"), ("seasonal", "Seasonal")]
def profileAllowlist : List String :=
  ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest",
   "http://hl7.org/fhir/StructureDefinition/MedicationRequest"]

def strengthUnits : List String := ["mg", "mcg", "ug", "g", "ml", "l", "u", "iu", "unit", "units", "unt"]
def strengthDenominators : List String := ["ml", "l", "g", "mg", "hr", "actuat"]
def formWords : List String :=
  ["oral", "orally", "tablet", "tablets", "capsule", "capsules", "solution", "suspension", "injectable",
   "injection", "extended", "release", "delayed", "chewable", "disintegrating", "film", "coated", "prefilled",
   "syringe", "pen", "injector", "auto", "cartridge", "inhaler", "inhalant", "metered", "powder", "topical",
   "cream", "ointment", "gel", "lotion", "patch", "transdermal", "system", "nasal", "spray", "ophthalmic",
   "otic", "rectal", "suppository", "sublingual", "lozenge", "granules", "packet", "liquid", "elixir", "syrup",
   "vaginal", "buccal", "enteric", "effervescent", "aerosol", "dry", "vial", "ampule", "implant"]

def fhirResourceTypes : List String :=
  ["Account", "ActivityDefinition", "AdverseEvent", "AllergyIntolerance", "Appointment",
   "AppointmentResponse", "AuditEvent", "Basic", "Binary", "BiologicallyDerivedProduct",
   "BodyStructure", "Bundle", "CapabilityStatement", "CarePlan", "CareTeam", "CatalogEntry",
   "ChargeItem", "ChargeItemDefinition", "Claim", "ClaimResponse", "ClinicalImpression", "CodeSystem",
   "Communication", "CommunicationRequest", "CompartmentDefinition", "Composition", "ConceptMap",
   "Condition", "Consent", "Contract", "Coverage", "CoverageEligibilityRequest",
   "CoverageEligibilityResponse", "DetectedIssue", "Device", "DeviceDefinition", "DeviceMetric",
   "DeviceRequest", "DeviceUseStatement", "DiagnosticReport", "DocumentManifest", "DocumentReference",
   "EffectEvidenceSynthesis", "Encounter", "Endpoint", "EnrollmentRequest", "EnrollmentResponse",
   "EpisodeOfCare", "EventDefinition", "Evidence", "EvidenceVariable", "ExampleScenario",
   "ExplanationOfBenefit", "FamilyMemberHistory", "Flag", "Goal", "GraphDefinition", "Group",
   "GuidanceResponse", "HealthcareService", "ImagingStudy", "Immunization", "ImmunizationEvaluation",
   "ImmunizationRecommendation", "ImplementationGuide", "InsurancePlan", "Invoice", "Library",
   "Linkage", "List", "Location", "Measure", "MeasureReport", "Media", "Medication",
   "MedicationAdministration", "MedicationDispense", "MedicationKnowledge", "MedicationRequest",
   "MedicationStatement", "MedicinalProduct", "MedicinalProductAuthorization",
   "MedicinalProductContraindication", "MedicinalProductIndication", "MedicinalProductIngredient",
   "MedicinalProductInteraction", "MedicinalProductManufactured", "MedicinalProductPackaged",
   "MedicinalProductPharmaceutical", "MedicinalProductUndesirableEffect", "MessageDefinition",
   "MessageHeader", "MolecularSequence", "NamingSystem", "NutritionOrder", "Observation",
   "ObservationDefinition", "OperationDefinition", "OperationOutcome", "Organization",
   "OrganizationAffiliation", "Parameters", "Patient", "PaymentNotice", "PaymentReconciliation",
   "Person", "PlanDefinition", "Practitioner", "PractitionerRole", "Procedure", "Provenance",
   "Questionnaire", "QuestionnaireResponse", "RelatedPerson", "RequestGroup", "ResearchDefinition",
   "ResearchElementDefinition", "ResearchStudy", "ResearchSubject", "RiskAssessment",
   "RiskEvidenceSynthesis", "Schedule", "SearchParameter", "ServiceRequest", "Slot", "Specimen",
   "SpecimenDefinition", "StructureDefinition", "StructureMap", "Subscription", "Substance",
   "SubstancePolymer", "SubstanceProtein", "SubstanceReferenceInformation", "SubstanceSpecification",
   "SubstanceSourceMaterial", "SupplyDelivery", "SupplyRequest", "Task", "TerminologyCapabilities",
   "TestReport", "TestScript", "ValueSet", "VerificationResult", "VisionPrescription"]

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

def trimmed (s : String) : String := s.trimAscii.toString

def sameName (a b : String) : Bool := (trimmed a).toLower == (trimmed b).toLower

def nonEmptyJson : Json → Bool
  | .null => false
  | .arr a => !a.isEmpty
  | .obj kvs => !kvs.isEmpty
  | .str s => !s.isEmpty
  | _ => true

def isObj : Json → Bool
  | .obj _ => true
  | _ => false

def isStr : Json → Bool
  | .str s => !(trimmed s).isEmpty
  | _ => false

def isBool : Json → Bool
  | .bool _ => true
  | _ => false

def isNum : Json → Bool
  | .num _ => true
  | _ => false

def isWhole : Json → Bool
  | .num n => if n.mantissa < 0 then false else decide (n.mantissa.toNat % 10 ^ n.exponent = 0)
  | _ => false

def fieldOk (j : Json) (k : String) (ok : Json → Bool) : Bool :=
  match jField? j k with
  | none => true
  | some v => ok v

def arrOk (ok : Json → Bool) : Json → Bool
  | .arr a => a.all ok
  | _ => false

def strOk (ok : String → Bool) : Json → Bool
  | .str s => ok s
  | _ => false

def keysWithin (ks : List String) : Json → Bool
  | .obj kvs => kvs.all fun k _ => ks.contains k
  | _ => false

def allowedIfPresent (ks : List String) (j : Option Json) : Bool :=
  match j with
  | some v => keysWithin ks v
  | none => true

def failsCheck (o : Option Json) (ok : Json → Bool) : Bool :=
  match o with
  | some v => !ok v
  | none => false

/-! Shapes: the JSON types the reader requires of the fields it reads. -/

def codingOk (c : Json) : Bool :=
  isObj c && fieldOk c "system" isStr && fieldOk c "code" isStr && fieldOk c "display" isStr

def conceptOk (cc : Json) : Bool :=
  isObj cc && fieldOk cc "text" isStr && fieldOk cc "coding" (arrOk codingOk)

def isMedicationRequest : Json → Bool
  | .str s => s == "MedicationRequest"
  | _ => false

def isBundle : Json → Bool
  | .str s => s == "Bundle"
  | _ => false

def isPeriodUnit : Json → Bool
  | .str s => periodUnitCodes.contains s
  | _ => false

def repeatOk (r : Json) : Bool :=
  isObj r && fieldOk r "frequency" isWhole && fieldOk r "period" isWhole && fieldOk r "periodUnit" isPeriodUnit

def timingOk (t : Json) : Bool :=
  isObj t && fieldOk t "repeat" repeatOk

def quantityOk (q : Json) : Bool :=
  isObj q && fieldOk q "value" isNum && fieldOk q "unit" isStr && fieldOk q "code" isStr
    && fieldOk q "system" isStr

def rateOk (r : Json) : Bool :=
  isObj r && fieldOk r "doseQuantity" quantityOk

def dosageOk (d : Json) : Bool :=
  isObj d && fieldOk d "timing" timingOk && fieldOk d "route" conceptOk
    && fieldOk d "doseAndRate" (arrOk rateOk) && fieldOk d "asNeededBoolean" isBool
    && fieldOk d "sequence" isWhole

/-! Grammars for the strings the reader keeps: ids, dates, language tags, references, and codes. -/

def fhirIdOk (s : String) : Bool :=
  !s.isEmpty && s.length ≤ 64 && s.toList.all fun c => c.isAlphanum || c == '-' || c == '.'

def digitsOnly (cs : List Char) : Bool := !cs.isEmpty && cs.all Char.isDigit

def tzOk : List Char → Bool
  | ['Z'] => true
  | [s, h1, h2, ':', m1, m2] => (s == '+' || s == '-') && [h1, h2, m1, m2].all Char.isDigit
  | _ => false

def timeOk : List Char → Bool
  | h1 :: h2 :: ':' :: m1 :: m2 :: ':' :: s1 :: s2 :: rest =>
      [h1, h2, m1, m2, s1, s2].all Char.isDigit &&
        (match rest with
          | '.' :: more =>
              let frac := more.takeWhile Char.isDigit
              !frac.isEmpty && tzOk (more.drop frac.length)
          | _ => tzOk rest)
  | _ => false

def dayOk : List Char → Bool
  | [] => true
  | '-' :: d1 :: d2 :: rest =>
      [d1, d2].all Char.isDigit && (match rest with | [] => true | 'T' :: t => timeOk t | _ => false)
  | _ => false

def monthOk : List Char → Bool
  | [] => true
  | '-' :: m1 :: m2 :: rest => [m1, m2].all Char.isDigit && dayOk rest
  | _ => false

def dateTimeOk (s : String) : Bool :=
  match s.toList with
  | y1 :: y2 :: y3 :: y4 :: rest => [y1, y2, y3, y4].all Char.isDigit && monthOk rest
  | _ => false

def subtagOk (p : String) (lo hi : Nat) (ok : Char → Bool) : Bool :=
  lo ≤ p.length && p.length ≤ hi && p.toList.all ok

def languageOk (s : String) : Bool :=
  match s.splitOn "-" with
  | [p] => subtagOk p 2 3 Char.isLower
  | [p, r] => subtagOk p 2 3 Char.isLower && subtagOk r 2 2 Char.isUpper
  | _ => false

def referenceOk (r : String) : Bool :=
  if r.startsWith "urn:uuid:" then fhirIdOk (r.drop 9).toString
  else match r.splitOn "/" with
    | [t, id] => fhirResourceTypes.contains t && fhirIdOk id
    | _ => false

def refObjOk (j : Json) : Bool :=
  keysWithin ["reference"] j && (match jStr? j "reference" with | some r => referenceOk r | none => false)

def icdHeadOk (a : String) : Bool :=
  match a.toList with
  | [c1, c2, c3] => c1.isUpper && c2.isDigit && (c3.isDigit || c3.isUpper)
  | _ => false

def icdOk (code : String) : Bool :=
  match code.splitOn "." with
  | [a] => icdHeadOk a
  | [a, b] => icdHeadOk a && 1 ≤ b.length && b.length ≤ 4 && b.toList.all fun c => c.isDigit || c.isUpper
  | _ => false

def codeShapeOk (system code : String) : Bool :=
  if system == snomedSystem then 6 ≤ code.length && code.length ≤ 18 && digitsOnly code.toList
  else if system == rxnormSystem then code.length ≤ 8 && digitsOnly code.toList
  else if system == ndcSystem then
    10 ≤ code.length && code.length ≤ 13 && code.toList.all fun c => c.isDigit || c == '-'
  else if system == icd10cmSystem || system == icd10System then icdOk code
  else if system == categorySystem then (categoryTerms.map (·.1)).contains code
  else if system == courseSystem then (courseTerms.map (·.1)).contains code
  else false

def displaysFor (system code : String) : List String :=
  if system == categorySystem then (categoryTerms.filter (·.1 == code)).map (·.2)
  else if system == courseSystem then (courseTerms.filter (·.1 == code)).map (·.2)
  else []

def codedCodingOk (systems : List String) (c : Json) : Bool :=
  keysWithin ["system", "code", "display", "userSelected"] c
  && (match jStr? c "system", jStr? c "code" with
      | some s, some k =>
          systems.contains s && codeShapeOk s k
          && (match jField? c "display" with
              | none => true
              | some (.str d) => (displaysFor s k).any (sameName · d)
              | some _ => false)
      | _, _ => false)
  && fieldOk c "userSelected" isBool

def codedConceptOk (systems : List String) (cc : Json) : Bool :=
  keysWithin ["coding"] cc && fieldOk cc "coding" (arrOk (codedCodingOk systems))

def profileOk : Json → Bool
  | .str s => profileAllowlist.any fun a =>
      s == a || (s.startsWith (a ++ "|") &&
        (let v := (s.drop (a.length + 1)).toString
         !v.isEmpty && v.toList.all fun c => c.isDigit || c == '.'))
  | _ => false

def metaOk (m : Json) : Bool :=
  keysWithin ["versionId", "lastUpdated", "profile", "security"] m
  && fieldOk m "versionId" (strOk fhirIdOk)
  && fieldOk m "lastUpdated" (strOk dateTimeOk)
  && fieldOk m "profile" (arrOk profileOk)
  && !(jField? m "security").any nonEmptyJson

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

def dispenseQuantityOk (q : Json) : Bool :=
  quantityOk q
  && keysWithin ["value", "unit", "code", "system"] q
  && doseQuantityOk q
  && (match jStr? q "code", jStr? q "unit" with
      | some c, _ => (DoseUnit.ofCode? c).isSome
      | none, some u => (DoseUnit.ofCode? u).isSome
      | none, none => true)

def dispenseOk (d : Json) : Bool :=
  keysWithin ["numberOfRepeatsAllowed", "quantity"] d
  && fieldOk d "numberOfRepeatsAllowed" isWhole
  && fieldOk d "quantity" dispenseQuantityOk

def substitutionOk (s : Json) : Bool :=
  keysWithin ["allowedBoolean"] s && fieldOk s "allowedBoolean" isBool

/-! The medication: its name, its coding displays, and the lexicon. -/

def numberTok (t : String) : Bool :=
  let cs := t.toList
  !cs.isEmpty && cs.all (fun c => c.isDigit || c == '.') && cs.head?.all Char.isDigit
    && cs.getLast?.all Char.isDigit && (cs.filter (· == '.')).length ≤ 1

def unitTok (t : String) : Bool :=
  match t.splitOn "/" with
  | [u] => strengthUnits.contains u.toLower
  | [u, d] => strengthUnits.contains u.toLower && strengthDenominators.contains d.toLower
  | _ => false

def formTok (t : String) : Bool :=
  (t.splitOn "-").all fun w => formWords.contains w.toLower

def remainderTok (t : String) : Bool := numberTok t || unitTok t || formTok t

def bracketOk (b : String) : Bool :=
  b.startsWith "[" && b.endsWith "]" && inLexicon (String.ofList (b.toList.drop 1).dropLast)

def remainderOk (r : String) : Bool :=
  let (body, brand) : String × Option String :=
    match r.splitOn "[" with
    | [b] => (b, none)
    | [b, br] => (b, some ("[" ++ br))
    | _ => ("", some "")
  ((body.splitOn " ").filter (!·.isEmpty)).all remainderTok
    && (match brand with | none => true | some b => bracketOk b)

def displayMatches (t d : String) : Bool :=
  let tl := (trimmed t).toLower.toList
  let dl := (trimmed d).toLower.toList
  let rest := dl.drop tl.length
  tl.isPrefixOf dl && rest.head?.all (fun c => !c.isAlpha) && remainderOk (String.ofList rest)

def displaysOf (cc : Json) : List String :=
  ((jArr? cc "coding").filterMap fun c => (jStr? c "display").map trimmed).filter (!·.isEmpty)

def medCodingOk (c : Json) : Bool :=
  keysWithin ["system", "code", "display", "userSelected"] c
  && (match jField? c "system", jField? c "code" with
      | none, none => true
      | some (.str s), some (.str k) => medicationSystems.contains s && codeShapeOk s k
      | _, _ => false)
  && fieldOk c "userSelected" isBool

structure Named where
  name : String
  ok : Bool

def conceptNamed (cc : Json) : Named :=
  if !keysWithin ["text", "coding"] cc then ⟨"", false⟩ else
  let codings := jArr? cc "coding"
  let codingsOk := codings.all medCodingOk
  match (jStr? cc "text").map trimmed with
  | some t =>
      if t.isEmpty then ⟨"", false⟩
      else
        let ok := codingsOk && codings.all fun c =>
          match jStr? c "display" with
          | some d => displayMatches t d
          | none => true
        ⟨if ok && inLexicon t then t else "", ok⟩
  | none =>
      match displaysOf cc with
      | [] => ⟨"", false⟩
      | d :: ds =>
          let ok := codingsOk && ds.all (sameName · d) && (d :: ds).all inLexicon
          ⟨if ok then d else "", ok⟩

def medicationEntries (req : Json) : List (Option String × Json) :=
  match jField? req "bundle" with
  | none => []
  | some b =>
      (jArr? b "entry").filterMap fun e =>
        (jField? e "resource").bind fun r =>
          if jStr? r "resourceType" = some "Medication" then some (jStr? e "fullUrl", r) else none

def medicationResourceOk (r : Json) : Bool :=
  keysWithin ["resourceType", "id", "meta", "code", "status"] r
  && fieldOk r "status" (strOk (· == "active"))
  && fieldOk r "meta" metaOk
  && (jField? r "code").any isObj

def resolveMedication (meds : List (Option String × Json)) (ref : String) : Option Json :=
  let hits :=
    if ref.startsWith "Medication/" then
      let id := (ref.drop 11).toString
      meds.filter fun m => jStr? m.2 "id" == some id
    else meds.filter fun m => m.1 == some ref
  match hits with
  | [m] => if medicationResourceOk m.2 then jField? m.2 "code" else none
  | _ => none

def orderConcept (meds : List (Option String × Json)) (mr : Json) : Option Json :=
  match jField? mr "medicationCodeableConcept", jField? mr "medicationReference" with
  | some cc, none => some cc
  | none, some ref => if refObjOk ref then (jStr? ref "reference").bind (resolveMedication meds) else none
  | _, _ => none

def medicationNamed (meds : List (Option String × Json)) (mr : Json) : Named :=
  match orderConcept meds mr with
  | some cc => if conceptOk cc then conceptNamed cc else ⟨"", false⟩
  | none => ⟨"", false⟩

/-! The dosage. -/

def jUnit? (q : Json) : Option DoseUnit :=
  match jField? q "code" with
  | some (.str c) => DoseUnit.ofCode? c
  | some _ => none
  | none => (jStr? q "unit").bind DoseUnit.ofCode?

def jDose? (q : Json) : Option Dose :=
  match (jField? q "value").bind jDec? with
  | some amount =>
      if amount.mant = 0 then none
      else (jUnit? q).bind fun u => if u.dim = .count then none else some ⟨amount, u⟩
  | none => none

def jTiming? (r : Json) : Option Timing := do
  let frequency ← (jField? r "frequency").bind jCount?
  let period ← (jField? r "period").bind jCount?
  let periodUnit ← (jStr? r "periodUnit").bind PeriodUnit.ofCode?
  pure ⟨frequency, period, periodUnit⟩

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

def routeCodingsKnown (route : Json) : Bool :=
  (jArr? route "coding").all fun c =>
    jStr? c "system" == some snomedSystem && ((jStr? c "code").bind Route.ofSnomed?).isSome
    && fieldOk c "userSelected" isBool

partial def hasExtensionKey : Json → Bool
  | .obj kvs => kvs.any fun k v => k == "extension" || k == "modifierExtension" || hasExtensionKey v
  | .arr a => a.any hasExtensionKey
  | _ => false

def dosageKeys : List String :=
  ["timing", "route", "doseAndRate", "asNeededBoolean", "sequence", "text", "additionalInstruction",
   "patientInstruction"]

def dosageAllowed (d : Json) : Bool :=
  keysWithin dosageKeys d
  && allowedIfPresent ["repeat", "code"] (jField? d "timing")
  && allowedIfPresent ["frequency", "period", "periodUnit"] ((jField? d "timing").bind (jField? · "repeat"))
  && allowedIfPresent ["coding", "text"] (jField? d "route")
  && (((jField? d "route").map fun r => jArr? r "coding").getD []).all
      (keysWithin ["system", "code", "display", "userSelected"])
  && (jArr? d "doseAndRate").all fun r =>
      keysWithin ["doseQuantity"] r
      && allowedIfPresent ["value", "unit", "code", "system"] (jField? r "doseQuantity")

def closedDosage (d : Json) : Bool :=
  let rate := (jArr? d "doseAndRate").head?
  hasAny (some d) ["site", "method"]
  || failsCheck (jField? d "route") routeTextsOk
  || failsCheck (jField? d "route") routeCodingsKnown
  || hasAny rate ["rateQuantity", "rateRatio", "rateRange", "type"]
  || failsCheck (rate.bind (jField? · "doseQuantity")) doseQuantityOk
  || !dosageAllowed d

/-! The order. -/

def courseOfTherapyOk (mr : Json) : Bool :=
  match jField? mr "courseOfTherapyType" with
  | none => true
  | some cc =>
      let codings := jArr? cc "coding"
      codedConceptOk [courseSystem] cc && !codings.isEmpty
        && codings.all fun c => jStr? c "code" == some "continuous"

def orderKeys : List String :=
  ["resourceType", "id", "meta", "implicitRules", "language", "identifier", "status", "intent", "category",
   "priority", "doNotPerform", "reportedBoolean", "reportedReference", "medicationCodeableConcept",
   "medicationReference", "subject", "encounter", "supportingInformation", "authoredOn", "requester",
   "performer", "performerType", "recorder", "reasonCode", "reasonReference", "instantiatesCanonical",
   "instantiatesUri", "basedOn", "groupIdentifier", "insurance", "dispenseRequest", "substitution",
   "eventHistory", "dosageInstruction", "note", "courseOfTherapyType", "priorPrescription"]

def referenceKeys : List String := ["subject", "encounter", "requester", "performer", "recorder"]
def referenceListKeys : List String :=
  ["reasonReference", "supportingInformation", "basedOn", "insurance", "eventHistory"]

def reportedByOther (mr : Json) : Bool :=
  (match jField? mr "reportedBoolean" with
    | some (.bool b) => b
    | _ => false)
  || (mr.getObjVal? "reportedReference").toOption.isSome

def closedFields (mr : Json) : Bool :=
  hasAny (some mr) ["statusReason", "identifier", "groupIdentifier", "instantiatesUri", "instantiatesCanonical",
    "implicitRules"]
  || !fieldOk mr "reasonCode" (arrOk (codedConceptOk reasonSystems))
  || !fieldOk mr "category" (arrOk (codedConceptOk [categorySystem]))
  || !fieldOk mr "performerType" (codedConceptOk [snomedSystem])
  || !fieldOk mr "priority" (strOk priorityCodes.contains)
  || !fieldOk mr "language" (strOk languageOk)
  || !fieldOk mr "authoredOn" (strOk dateTimeOk)
  || !fieldOk mr "meta" metaOk
  || !fieldOk mr "dispenseRequest" dispenseOk
  || !fieldOk mr "substitution" substitutionOk
  || !referenceKeys.all (fun k => fieldOk mr k refObjOk)
  || !referenceListKeys.all (fun k => fieldOk mr k (arrOk refObjOk))

def closedOrder (mr : Json) (id : String) (refs : List String) : Bool :=
  hasExtensionKey mr
  || !keysWithin orderKeys mr
  || hasAny (some mr) ["priorPrescription"]
  || reportedByOther mr
  || !courseOfTherapyOk mr
  || refs.contains ("MedicationRequest/" ++ id)
  || closedFields mr

def hasFreeText (mr d : Json) : Bool :=
  hasAny (some d) ["text", "additionalInstruction", "patientInstruction"] || hasAny (some mr) ["note"]

def subjectRef (mr : Json) : Option String :=
  ((jField? mr "subject").bind (jStr? · "reference")).filter fun r => !r.isEmpty

def patientIdOf? (r : String) : Option String :=
  let id? :=
    if r.startsWith "urn:uuid:" then some (r.drop 9).toString
    else match r.splitOn "/" with
      | ["Patient", id] => some id
      | _ => none
  id?.filter fhirIdOk

def subjectMatches (patient : Option String) (mr : Json) : Bool :=
  match patient with
  | none => true
  | some p => (subjectRef mr).bind patientIdOf? == some p

def doNotPerform (mr : Json) : Bool :=
  match jField? mr "doNotPerform" with
  | some (.bool false) | none => false
  | some _ => true

def isActive (patient : Option String) (mr : Json) : Bool :=
  jStr? mr "status" == some "active" &&
    (match jStr? mr "intent" with
      | some i => orderIntents.contains i
      | none => false) &&
    !doNotPerform mr && subjectMatches patient mr

def priorRefs (orders : List Json) : List String :=
  orders.filterMap fun mr => (jField? mr "priorPrescription").bind (jStr? · "reference")

def medReqOfJson (ignoreFreeText : Bool) (patient : Option String) (refs : List String)
    (meds : List (Option String × Json)) (mr : Json) : Option MedReq := do
  let id ← jStr? mr "id"
  let active := isActive patient mr
  let named := medicationNamed meds mr
  let drug := named.name.toList
  match jArr? mr "dosageInstruction" with
  | [d] =>
      if failsClosed d || closedOrder mr id refs || closedDosage d || !named.ok
          || (!ignoreFreeText && hasFreeText mr d) then
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

def chartFrom (ignoreFreeText : Bool) (patient : Option String) (meds : List (Option String × Json))
    (orders : List Json) : List MedReq :=
  orders.filterMap (medReqOfJson ignoreFreeText patient (priorRefs orders) meds)

def orderResources (req : Json) : List Json :=
  match jField? req "bundle" with
  | some b => bundleResources b
  | none => jArr? req "medicationRequests"

/-! Request shape: the errors that refuse the whole request. -/

def orderShapeProblem (id : String) (mr : Json) : Option String :=
  let checks : List (Bool × String) :=
    [(fieldOk mr "resourceType" isMedicationRequest, "needs resourceType to be MedicationRequest when present"),
     (fieldOk mr "doNotPerform" isBool, "needs doNotPerform to be true or false when present"),
     (fieldOk mr "reportedBoolean" isBool, "needs reportedBoolean to be true or false when present"),
     ((jField? mr "medicationCodeableConcept").isSome || (jField? mr "medicationReference").isSome,
      "needs a medicationCodeableConcept or medicationReference"),
     (fieldOk mr "medicationCodeableConcept" conceptOk, "needs a valid medicationCodeableConcept"),
     (fieldOk mr "dosageInstruction" (arrOk dosageOk), "needs a valid dosageInstruction"),
     (fieldOk mr "dispenseRequest" isObj, "needs dispenseRequest to be an object"),
     (fieldOk mr "meta" isObj, "needs meta to be an object")]
  (checks.find? (fun c => !c.1)).map fun c => "MedicationRequest " ++ id ++ " " ++ c.2

def keyError (allowed : List String) (what k : String) (v : Json) : Option String :=
  match v with
  | .null => none
  | _ => if allowed.contains k then none else some (what ++ " key " ++ k ++ " is not accepted")

def keyProblem (allowed : List String) (what : String) (j : Json) : Option String :=
  match j with
  | .obj kvs => kvs.toList.findSome? fun kv => keyError allowed what kv.1 kv.2
  | _ => none

def resourceProblem (e : Json) : Option String :=
  match jField? e "resource" with
  | none => some "a bundle entry has no resource"
  | some r =>
      let who := match jStr? r "id" with
        | some id => "a bundle entry resource with id " ++ id
        | none => "a bundle entry resource"
      if !(jField? r "resourceType").any isStr then
        some "a bundle entry resource has no string resourceType"
      else
        let t := (jStr? r "resourceType").getD ""
        if t == "Bundle" then
          some (who ++ " is itself a Bundle, which the gate does not accept; send one flat Bundle of MedicationRequests")
        else if eventResourceTypes.contains t then
          some (who ++ " has resourceType " ++ t
            ++ ", which the gate cannot represent as an instruction; send only MedicationRequests")
        else if fhirResourceTypes.contains t then none
        else some (who ++ " has resourceType " ++ t ++ ", which is not a FHIR R4 resource type")

def urlChar (c : Char) : Bool := !c.isWhitespace && c != '"' && c != '<' && c != '>'

def fullUrlOk (s : String) : Bool :=
  !s.isEmpty && s.length ≤ 512 && s.toList.all urlChar
    && (s.startsWith "urn:uuid:" || s.startsWith "http://" || s.startsWith "https://")

def searchOk (s : Json) : Bool :=
  isObj s && keysWithin ["mode", "score"] s
    && fieldOk s "mode" (strOk searchModes.contains) && fieldOk s "score" isNum

def entryProblem (e : Json) : Option String :=
  if !isObj e then some "a bundle entry is not an object"
  else keyProblem entryKeys "bundle entry" e
    <|> (if !fieldOk e "fullUrl" (strOk fullUrlOk) then
          some "a bundle entry fullUrl must be a urn:uuid: or http or https URL without spaces" else none)
    <|> (if !fieldOk e "search" searchOk then
          some "a bundle entry search may carry only a mode of match, include, or outcome and a numeric score"
         else none)
    <|> resourceProblem e

def linkOk (l : Json) : Bool :=
  isObj l && keysWithin ["relation", "url"] l
    && (match jStr? l "relation" with | some r => linkRelations.contains r | none => false)
    && (match jStr? l "url" with
        | some u => (u.startsWith "http://" || u.startsWith "https://") && u.toList.all urlChar
        | none => false)

def bundleMetaOk (m : Json) : Bool :=
  isObj m && keysWithin ["versionId", "lastUpdated"] m
    && fieldOk m "versionId" (strOk fhirIdOk) && fieldOk m "lastUpdated" (strOk dateTimeOk)

def bundleFieldsProblem (b : Json) : Option String :=
  if !fieldOk b "id" (strOk fhirIdOk) then some "bundle id must be 1 to 64 letters, digits, hyphens, or periods"
  else if !fieldOk b "meta" bundleMetaOk then some "bundle meta may carry only versionId and lastUpdated"
  else if !fieldOk b "timestamp" (strOk dateTimeOk) then some "bundle timestamp must be a FHIR dateTime"
  else if !fieldOk b "total" isWhole then some "bundle total must be a whole number"
  else if !fieldOk b "link" (arrOk linkOk) then
    some "bundle link entries may carry only a relation of self, next, previous, first, or last and an http or https url"
  else none

def bundleEntriesProblem (req : Json) : Option String :=
  match jField? req "bundle" with
  | none => none
  | some b => keyProblem bundleKeys "bundle" b <|> bundleFieldsProblem b <|> (jArr? b "entry").findSome? entryProblem

def orderProblem (mr : Json) : Option String :=
  let id := (jStr? mr "id").getD ""
  if !((jStr? mr "status").any statusCodes.contains) then
    some ("MedicationRequest " ++ id ++ " needs a status string that is one of " ++ ", ".intercalate statusCodes)
  else if !((jStr? mr "intent").any intentCodes.contains) then
    some ("MedicationRequest " ++ id ++ " needs an intent string that is one of " ++ ", ".intercalate intentCodes)
  else orderShapeProblem id mr

def orderProblems (req : Json) : Option String :=
  (orderResources req).findSome? orderProblem

def subjectProblem (patient : Option String) (req : Json) : Option String :=
  let refs := (orderResources req).map subjectRef
  if refs.any Option.isNone then some "every MedicationRequest needs a subject.reference string"
  else
    let rs := refs.filterMap id
    if rs.any (fun r => r.startsWith "http://" || r.startsWith "https://") then
      some "a MedicationRequest subject.reference is an absolute URL; the gate accepts only Patient/id or urn:uuid:id"
    else if rs.any (fun r => (patientIdOf? r).isNone) then
      some "every MedicationRequest subject.reference must be Patient/id or urn:uuid:id"
    else if rs.eraseDups.length > 1 then
      some "the MedicationRequests reference more than one subject; send one patient's orders"
    else match patient, rs.head? with
      | some p, some r =>
          if patientIdOf? r == some p then none
          else some ("the MedicationRequests are for subject " ++ r ++ ", not the patient " ++ p
            ++ " named by the patient field")
      | _, _ => none

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

def bundleResourceTypeBad (req : Json) : Bool :=
  match jField? req "bundle" with
  | some b => !fieldOk b "resourceType" isBundle
  | none => false

def shapeProblem (req : Json) : Option String :=
  if (jField? req "bundle").isSome && (jField? req "medicationRequests").isSome then
    some "the request has both bundle and medicationRequests, so it is ambiguous; send only one of them"
  else if let some e := keyProblem requestKeys "request" req then some e
  else if bundleShapeBad req then some "bundle must be an object with an entry array"
  else if bundleTypeBad req then some "bundle type must be searchset or collection"
  else if bundleResourceTypeBad req then some "bundle resourceType must be Bundle when present"
  else if bundleRequestBad req then some "a bundle entry has a request key, which the gate does not accept"
  else if let some e := bundleEntriesProblem req then some e
  else if medicationRequestsShapeBad req then some "medicationRequests must be an array"
  else if (orderResources req).any (fun mr => (jStr? mr "id").isNone) then
    some "every MedicationRequest needs an id string"
  else if (orderResources req).any (fun mr => (jStr? mr "id").any fun s => (trimmed s).isEmpty) then
    some "every MedicationRequest needs an id that is not empty"
  else if (orderResources req).any (fun mr => (jStr? mr "id").any fun s => !fhirIdOk s) then
    some "every MedicationRequest needs an id of 1 to 64 letters, digits, hyphens, or periods"
  else none

def patientOf (req : Json) : Except String (Option String) :=
  match jField? req "patient" with
  | none => .ok none
  | some (.str p) => if p.isEmpty then .error "patient must be a non-empty string" else .ok (some p)
  | some _ => .error "patient must be a string"

def chartOf (ignoreFreeText : Bool) (patient : Option String) (req : Json) : Option (List MedReq) :=
  match jField? req "bundle", jField? req "medicationRequests" with
  | some b, _ => some (chartFrom ignoreFreeText patient (medicationEntries req) (bundleResources b))
  | none, some _ => some (chartFrom ignoreFreeText patient [] (jArr? req "medicationRequests"))
  | none, none => none

end DoseGate
