import DoseGate.Json

open DoseGate Lean

def main : IO Unit := do
  match Json.parse "{\"value\":1e300000,\"code\":\"mg\"}" with
  | .ok j =>
      IO.println s!"parsed, jDose? some: {(jDose? j).isSome}"
  | .error e => IO.println s!"error {e}"
