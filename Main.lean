import Lean.Data.Json
import DoseGate.Json
import DoseGate.Render

open DoseGate

def blockName : Block → String
  | .malformed => "malformed"
  | .duplicateIds => "duplicateIds"
  | .nonAscii => "nonAscii"
  | .forbiddenWord _ => "forbiddenWord"
  | .unknownWord _ => "unknownWord"
  | .unknownRef _ => "unknownRef"
  | .inactiveOrder _ => "inactiveOrder"
  | .missingField _ _ => "missingField"
  | .unseparated => "unseparated"
  | .unbound => "unbound"

def blockDetail : Block → String
  | .malformed => "output has an unclosed, stray, or unrecognized brace"
  | .duplicateIds => "two MedicationRequests share one id"
  | .nonAscii => "output contains a non-ASCII character"
  | .forbiddenWord tok => "free text contains the forbidden word " ++ String.ofList tok
  | .unknownWord tok => "free text contains the word " ++ String.ofList tok ++ ", which is not in the vocabulary"
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

def handle (policy : Policy) (req : Lean.Json) : Lean.Json × UInt8 :=
  match jStr? req "output" with
  | none => (errorJson "request has no output string", 1)
  | some out =>
      if out.length > maxOutput then
        (errorJson s!"the output is longer than {maxOutput} characters", 1)
      else
        match patientOf req with
        | .error e => (errorJson e, 1)
        | .ok patient =>
            match chartOf patient req with
            | none => (errorJson "request has neither bundle nor medicationRequests", 1)
            | some chart =>
                if chart.length > maxOrders then
                  (errorJson s!"the request has more than {maxOrders} MedicationRequests", 1)
                else
                  match render policy chart out.toList with
                  | .ok text => (okJson (String.ofList text), 0)
                  | .error b => (blockedJson b, 2)

def respondLine (policy : Policy) (line : String) : Lean.Json × UInt8 :=
  match requestProblem line with
  | some problem => (errorJson problem, 1)
  | none =>
      match Lean.Json.parse line with
      | .error e => (errorJson ("invalid JSON: " ++ e), 1)
      | .ok req => handle policy req

partial def readAll (h : IO.FS.Stream) (acc : String := "") : IO String := do
  let line ← h.getLine
  if line.isEmpty then pure acc else readAll h (acc ++ line)

partial def serveLoop (policy : Policy) (stdin stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then return
  let text := line.trimAscii.toString
  if !text.isEmpty then
    stdout.putStrLn (respondLine policy text).1.compress
    stdout.flush
  serveLoop policy stdin stdout

def parseOptions : List String → Option (Option String)
  | [] => some none
  | ["--extra-words", path] => some (some path)
  | _ => none

def loadExtraWords (path : String) : IO (List String) := do
  let words := ((← IO.FS.readFile path).splitOn "\n").map (·.trimAscii.toString) |>.filter (fun w => !w.isEmpty)
  match words.find? (fun w => !w.toList.all Char.isLower) with
  | some w => throw (IO.userError s!"extra word '{w}' in {path} is not lowercase letters")
  | none => pure words

def policyOf : Option String → IO Policy
  | none => pure {}
  | some path => do
      let words ← loadExtraWords path
      pure { extraWords := words }

def usage : IO UInt32 := do
  IO.eprintln "usage: dosegate render | dosegate serve [--extra-words FILE]"
  pure 1

def main (args : List String) : IO UInt32 := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  let (cmd, rest) := match args with
    | c :: r => (c, r)
    | [] => ("", [])
  match cmd, parseOptions rest with
  | "render", some file? =>
      let policy ← policyOf file?
      let (resp, code) := respondLine policy (← readAll stdin)
      stdout.putStrLn resp.compress
      stdout.flush
      pure code.toUInt32
  | "serve", some file? =>
      let policy ← policyOf file?
      serveLoop policy stdin stdout
      pure 0
  | _, _ => usage
