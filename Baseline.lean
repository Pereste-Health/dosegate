import Lean.Data.Json
import DoseGate.Json
import DoseGate.Render

/-
A comparison filter for the evaluation, not part of the layer. It reads the
request with the same FHIR reader and fills slots with the same field
formatting, but its only check on model text is a blocklist of digits and
unit words. It has no sentence shapes, vocabulary, drug-name rule, repeated
value rule, separation rule, or daily-total ambiguity rule.
-/

open DoseGate

def baseField (f : Field) (m : MedReq) : Option (List Char) :=
  if f == .drug then some m.drug else fmtField f m

def baseText (t : List Char) : Bool :=
  !(tokens t).any fun tok => tok.any Char.isDigit || wordIn unitWords tok

def baseSeg (chart : List MedReq) : Seg → Except String (List Char)
  | .text t => if baseText t then pure t else throw "numberOrUnitWord"
  | .slot f id =>
      match chart.find? (·.id == id) with
      | none => throw "unknownRef"
      | some m =>
          if !m.active then throw "inactiveOrder"
          else match baseField f m with
            | none => throw "missingField"
            | some p => pure p

def baseline (chart : List MedReq) (out : List Char) : Except String (List Char) := do
  let some segs := parseTemplate out | throw "malformed"
  let pieces ← segs.mapM (baseSeg chart)
  pure pieces.flatten

def respond (line : String) : Lean.Json :=
  let err (m : String) := Lean.Json.mkObj [("status", "error"), ("message", Lean.Json.str m)]
  if line.utf8ByteSize > maxRequestBytes then err "request too large" else
  match requestProblem line with
  | some p => err p
  | none =>
      match Lean.Json.parse line with
      | .error e => err e
      | .ok req =>
          match jStr? req "output", patientOf req with
          | none, _ => err "request has no output string"
          | _, .error e => err e
          | some out, .ok patient =>
              if out.length > maxOutput || (out.splitOn "{{").length - 1 > maxSlots then err "output too long"
              else match shapeProblem req, subjectProblem patient req with
              | some e, _ | none, some e => err e
              | none, none =>
              match chartOf false patient req with
              | none => err "request has neither bundle nor medicationRequests"
              | some chart =>
                  if chart.length > maxOrders then err "too many orders" else
                  match baseline chart out.toList with
                  | .ok t => Lean.Json.mkObj [("status", "ok"), ("text", Lean.Json.str (String.ofList t))]
                  | .error r => Lean.Json.mkObj [("status", "blocked"), ("reason", Lean.Json.str r)]

partial def loop (stdin stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then return
  let text := line.trimAscii.toString
  if !text.isEmpty then
    stdout.putStrLn (respond text).compress
    stdout.flush
  loop stdin stdout

def main : IO Unit := do
  loop (← IO.getStdin) (← IO.getStdout)
