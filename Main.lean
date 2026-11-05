import Lean.Data.Json
import DoseGate
import DoseGate.Json

open DoseGate

def blockName : Block → String
  | .malformed => "malformed"
  | .duplicateIds => "duplicateIds"
  | .nonAscii => "nonAscii"
  | .doseTokenInText _ => "doseTokenInText"
  | .unknownRef _ => "unknownRef"
  | .inactiveOrder _ => "inactiveOrder"
  | .missingField _ _ => "missingField"
  | .unseparated => "unseparated"
  | .unbound => "unbound"

def blockDetail : Block → String
  | .malformed => "output has an unclosed, stray, or unrecognized brace"
  | .duplicateIds => "two MedicationRequests share one id"
  | .nonAscii => "output contains a non-ASCII character"
  | .doseTokenInText tok => "free text contains the dose token " ++ String.ofList tok
  | .unknownRef id => "no MedicationRequest has id " ++ String.ofList id
  | .inactiveOrder id => "MedicationRequest " ++ String.ofList id ++ " is not active"
  | .missingField id f => "MedicationRequest " ++ String.ofList id ++ " has no usable " ++ String.ofList f.name
  | .unseparated => "two filled slots touch without a space or punctuation between them"
  | .unbound => "a sentence mixes orders, repeats a field, combines sig with other dose fields, or lacks its drug"

def okJson (text : String) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "ok"), ("text", Lean.Json.str text)]

def blockedJson (b : Block) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "blocked"), ("reason", Lean.Json.str (blockName b)),
    ("detail", Lean.Json.str (blockDetail b))]

def errorJson (message : String) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "error"), ("message", Lean.Json.str message)]

def chartOf (req : Lean.Json) : Option (List MedReq) :=
  match jField? req "bundle", jField? req "medicationRequests" with
  | some b, _ => some (bundleChart b)
  | none, some _ => some ((jArr? req "medicationRequests").filterMap medReqOfJson)
  | none, none => none

def allowOf (req : Lean.Json) : List (List Char) :=
  (jArr? req "allow").filterMap fun a => a.getStr?.toOption.map (·.toLower.toList)

def handle (req : Lean.Json) : Lean.Json × UInt8 :=
  match jStr? req "output", chartOf req with
  | none, _ => (errorJson "request has no output string", 1)
  | some _, none => (errorJson "request has neither bundle nor medicationRequests", 1)
  | some out, some chart =>
      match render ⟨allowOf req⟩ chart out.toList with
      | .ok text => (okJson (String.ofList text), 0)
      | .error b => (blockedJson b, 2)

def respondLine (line : String) : Lean.Json × UInt8 :=
  match Lean.Json.parse line with
  | .error e => (errorJson ("invalid JSON: " ++ e), 1)
  | .ok req => handle req

partial def readAll (h : IO.FS.Stream) (acc : String := "") : IO String := do
  let line ← h.getLine
  if line.isEmpty then pure acc else readAll h (acc ++ line)

partial def serveLoop (stdin stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then return
  let text := line.trimAscii.toString
  if !text.isEmpty then
    stdout.putStrLn (respondLine text).1.compress
    stdout.flush
  serveLoop stdin stdout

def main (args : List String) : IO UInt32 := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  match args with
  | ["render"] =>
      let (resp, code) := respondLine (← readAll stdin)
      stdout.putStrLn resp.compress
      stdout.flush
      pure code.toUInt32
  | ["serve"] =>
      serveLoop stdin stdout
      pure 0
  | _ =>
      IO.eprintln "usage: dosegate render | dosegate serve"
      pure 1
