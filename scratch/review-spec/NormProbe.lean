import DoseGate
import DoseGate.Json

open DoseGate Lean

def main : IO Unit := do
  let mk (v : String) : Option String :=
    match Json.parse ("{\"value\":" ++ v ++ ",\"code\":\"mg\"}") with
    | .ok j => (jDose? j).map fun d => String.ofList (fmtDose d)
    | .error _ => none
  IO.println s!"value 1.50 prints: {mk "1.50"}"
  IO.println s!"value 1.0 prints: {mk "1.0"}"
  IO.println s!"value 0.125 prints: {mk "0.125"}"
  IO.println s!"value 10 prints: {mk "10"}"
