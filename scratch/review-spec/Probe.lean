import DoseGate
import DoseGate.Json

open DoseGate Lean

def showRes : Except Block (List Char) → String
  | .ok t => "OK      " ++ String.ofList t
  | .error b => s!"BLOCKED {repr b}"

def mrOrder : MedReq :=
  { id := "m1".toList, active := true, drug := "Lisinopril".toList,
    dose := some ⟨⟨10, 0⟩, .mg⟩, timing := some ⟨1, 1, .d⟩, route := some .oral, asNeeded := false }

def chartOf (s : String) : List MedReq :=
  match Json.parse s with
  | .ok j => bundleChart j
  | .error _ => []

def entry (res : String) : String :=
  "{\"resourceType\":\"Bundle\",\"entry\":[{\"resource\":" ++ res ++ "}]}"

def mr (extra dosage : String) : String :=
  "{\"resourceType\":\"MedicationRequest\",\"id\":\"m1\",\"status\":\"active\"" ++ extra ++
  ",\"medicationCodeableConcept\":{\"text\":\"Lisinopril\"},\"dosageInstruction\":[" ++ dosage ++ "]}"

def dosageFull (timing : String) : String :=
  "{\"route\":{\"coding\":[{\"system\":\"http://snomed.info/sct\",\"code\":\"26643006\"}]}," ++
  "\"doseAndRate\":[{\"doseQuantity\":{\"value\":10,\"code\":\"mg\"}}]," ++
  "\"timing\":{\"repeat\":" ++ timing ++ "}}"

def run (label : String) (chart : List MedReq) (out : String) (allow : List String := []) : IO Unit :=
  IO.println s!"{label}: {showRes (render ⟨allow.map String.toList⟩ chart out.toList)}"

def main : IO Unit := do
  run "A free-text route IV" [mrOrder] "{{drug:m1}} is given intravenously."
  run "B free-text frequency daily" [mrOrder] "{{drug:m1}} is taken daily."
  run "C free-text every other day" [mrOrder] "{{drug:m1}} is taken every other day."
  run "D free-text as needed" [mrOrder] "{{drug:m1}} as needed for pain."
  run "E gm unit word" [mrOrder] "Give X gm of {{drug:m1}}."
  run "F pair of ampoules" [mrOrder] "Give a pair of ampoules of {{drug:m1}}."
  run "G tenfold" [mrOrder] "Give a tenfold amount of {{drug:m1}}."
  run "H roman X" [mrOrder] "Give X of {{drug:m1}}."
  run "I allow list digits" [mrOrder] "Take 10 mg of {{drug:m1}}." ["10", "mg"]
  let drugDisplay := { mrOrder with drug := "Lisinopril 10 MG Oral Tablet".toList, dose := some ⟨⟨20, 0⟩, .mg⟩ }
  run "J drug display carries strength, dose 20 mg" [drugDisplay] "{{drug:m1}} {{dose:m1}}."
  run "K other drug named in same sentence" [mrOrder] "Aspirin and {{drug:m1}} {{dose:m1}}."
  let freqMax := chartOf (entry (mr "" (dosageFull "{\"frequency\":1,\"frequencyMax\":2,\"period\":1,\"periodUnit\":\"d\"}")))
  run "L frequencyMax 1 to 2 daily as sig" freqMax "{{drug:m1}} {{sig:m1}}."
  let perMax := chartOf (entry (mr "" (dosageFull "{\"frequency\":1,\"period\":6,\"periodMax\":8,\"periodUnit\":\"h\"}")))
  run "M periodMax 6 to 8 hours as frequency" perMax "{{drug:m1}} {{frequency:m1}}."
  let intentProp := chartOf (entry (mr ",\"intent\":\"proposal\"" (dosageFull "{\"frequency\":1,\"period\":1,\"periodUnit\":\"d\"}")))
  run "N intent proposal treated as active" intentProp "{{drug:m1}} {{frequency:m1}}."
  let subj := chartOf (entry (mr ",\"subject\":{\"reference\":\"Patient/OTHER\"}" (dosageFull "{\"frequency\":1,\"period\":1,\"periodUnit\":\"d\"}")))
  run "O subject other patient accepted" subj "{{drug:m1}} {{frequency:m1}}."
  let codeNum := chartOf (entry "{\"resourceType\":\"MedicationRequest\",\"id\":\"m1\",\"status\":\"active\",\"medicationCodeableConcept\":{\"text\":\"Lisinopril\"},\"dosageInstruction\":[{\"doseAndRate\":[{\"doseQuantity\":{\"value\":10,\"code\":5,\"unit\":\"mg\"}}],\"timing\":{\"repeat\":{\"frequency\":1,\"period\":1,\"periodUnit\":\"d\"}}}]}")
  run "P non-string code falls back to unit" codeNum "{{drug:m1}} {{dose:m1}}."
  let twoDosage := chartOf (entry "{\"resourceType\":\"MedicationRequest\",\"id\":\"m1\",\"status\":\"active\",\"medicationCodeableConcept\":{\"text\":\"Lisinopril\"},\"dosageInstruction\":[{\"doseAndRate\":[{\"doseQuantity\":{\"value\":10,\"code\":\"mg\"}}]},{\"doseAndRate\":[{\"doseQuantity\":{\"value\":20,\"code\":\"mg\"}}]}]}")
  run "Q two dosageInstructions blocked" twoDosage "{{drug:m1}} {{dose:m1}}."
  run "R BID in text" [mrOrder] "{{drug:m1}} BID."
  run "S tomorrow daily in text" [mrOrder] "{{drug:m1}} {{frequency:m1}} and then tomorrow daily."
