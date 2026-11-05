import Lean.Data.Json
import DoseGate.Json
import DoseGate.Render

open DoseGate

def blockName : Block → String
  | .malformed => "malformed"
  | .duplicateIds => "duplicateIds"
  | .disallowedCharacter => "disallowedCharacter"
  | .forbiddenWord _ => "forbiddenWord"
  | .unknownWord _ => "unknownWord"
  | .unknownRef _ => "unknownRef"
  | .inactiveOrder _ => "inactiveOrder"
  | .missingField _ _ => "missingField"
  | .unseparated => "unseparated"
  | .unbound => "unbound"
  | .repeatedValue => "repeatedValue"
  | .ambiguousDrug _ => "ambiguousDrug"
  | .signBeforeSlot => "signBeforeSlot"
  | .omittedOrder _ => "omittedOrder"

def slotText (f : Field) (id : List Char) : String :=
  "{{" ++ String.ofList f.name ++ ":" ++ String.ofList id ++ "}}"

def shapeOf (g : List Seg) : String :=
  let sl := slotsOf g
  let fs := sl.map (·.1)
  let id := (sl.head?.map (·.2)).getD []
  if fs.any isValueField then
    "A sentence with a dose, route, frequency, sig, or daily slot must take one of these shapes, with no other words and each field once: Take "
      ++ slotText .drug id ++ " " ++ slotText .dose id ++ " " ++ slotText .route id ++ " "
      ++ slotText .frequency id ++ ". Or: Take " ++ slotText .drug id ++ " " ++ slotText .sig id
      ++ ". A daily total may only end either shape, as: which is " ++ slotText .daily id ++ "."
  else
    "A sentence with no dose, route, frequency, sig, or daily slot must use only common words and no slot, so a drug name needs a sentence with its dose, route, and frequency or its sig."

def sentenceDetail (i : Nat) (g : List Seg) (problem : String) : String :=
  let text := (String.ofList (unparse g)).trimAscii.toString
  "sentence " ++ toString i ++ ", \"" ++ text ++ "\", " ++ problem ++ ". " ++ shapeOf g

def firstSentence (pred : List Seg → Bool) : Nat → List (List Seg) → Option (Nat × List Seg)
  | _, [] => none
  | i, g :: gs => if pred g then some (i, g) else firstSentence pred (i + 1) gs

def locateDetail (out : String) (pred : List Seg → Bool) (problem fallback : String) : String :=
  match parseTemplate out.toList with
  | none => fallback
  | some segs =>
      match firstSentence pred 1 (sentences segs) with
      | some (i, g) => sentenceDetail i g problem
      | none => fallback

def blockDetail (p : Policy) (out : String) : Block → String
  | .malformed => "output has an unclosed, stray, or unrecognized brace"
  | .duplicateIds => "two MedicationRequests share one id"
  | .disallowedCharacter => "output contains a character that model text may not use: only letters, digits, spaces, line breaks, and . , ; : ( ) ' \" - /"
  | .forbiddenWord tok => "free text contains the forbidden word " ++ String.ofList tok
  | .unknownWord tok =>
      locateDetail out (fun g => (wordsOf g).contains tok)
        ("uses the word " ++ String.ofList tok ++ ", which is not in the vocabulary")
        ("free text contains the word " ++ String.ofList tok ++ ", which is not in the vocabulary")
  | .unknownRef id => "no MedicationRequest has id " ++ String.ofList id
  | .inactiveOrder id => "MedicationRequest " ++ String.ofList id ++ " is not active"
  | .missingField id f => "MedicationRequest " ++ String.ofList id ++ " has no usable " ++ String.ofList f.name
  | .unseparated => "two filled slots touch without a space or punctuation between them"
  | .unbound =>
      locateDetail out (fun g => !sentenceOk p g) "does not match a valid sentence shape"
        "a sentence does not match a valid sentence shape"
  | .repeatedValue =>
      "a value slot (dose, route, frequency, sig, or daily) appears twice for one order, or sig appears with dose, route, or frequency for one order"
  | .ambiguousDrug _ =>
      "another active order has the same or a related drug name, so the instructions could be confused"
  | .signBeforeSlot =>
      "a text segment directly before a slot ends with a run of non-letter, non-digit characters that contains - or +, which would put a sign in front of a filled value"
  | .omittedOrder id =>
      "MedicationRequest " ++ String.ofList id ++ " is active but no dose, route, frequency, sig, or daily slot names it"

def okJson (text : String) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "ok"), ("text", Lean.Json.str text)]

def blockedJson (b : Block) (detail : String) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "blocked"), ("reason", Lean.Json.str (blockName b)),
    ("detail", Lean.Json.str detail)]

def errorJson (message : String) : Lean.Json :=
  Lean.Json.mkObj [("status", Lean.Json.str "error"), ("message", Lean.Json.str message)]

structure Opts where
  policy : Policy
  ignoreFreeText : Bool

def outputProblem (out : String) : Option String :=
  if out.length > maxOutput then some s!"the output is longer than {maxOutput} characters"
  else if (out.splitOn "{{").length - 1 > maxSlots then some s!"the output has more than {maxSlots} slots"
  else none

def requestChart (ignoreFreeText : Bool) (req : Lean.Json) : Except (Lean.Json × UInt8) (List MedReq) :=
  match shapeProblem req with
  | some e => .error (errorJson e, 1)
  | none =>
      match patientOf req with
      | .error e => .error (errorJson e, 1)
      | .ok patient =>
          match subjectProblem patient req with
          | some e => .error (errorJson e, 1)
          | none =>
              match orderProblems patient req with
              | some e => .error (errorJson e, 1)
              | none =>
                  match chartOf ignoreFreeText patient req with
                  | none => .error (errorJson "request has neither bundle nor medicationRequests", 1)
                  | some chart =>
                      if chart.length > maxOrders then
                        .error (errorJson s!"the request has more than {maxOrders} MedicationRequests", 1)
                      else .ok chart

def renderChart (o : Opts) (chart : List MedReq) (out : String) : Lean.Json × UInt8 :=
  match render o.policy chart out.toList with
  | .ok text =>
      if text.length > maxOutput then
        (errorJson s!"the rendered text is longer than {maxOutput} characters", 1)
      else (okJson (String.ofList text), 0)
  | .error b => (blockedJson b (blockDetail o.policy out b), 2)

def handleRender (o : Opts) (req : Lean.Json) : Lean.Json × UInt8 :=
  match jStr? req "output" with
  | none => (errorJson "request has no output string", 1)
  | some out =>
      match outputProblem out with
      | some e => (errorJson e, 1)
      | none =>
          match requestChart o.ignoreFreeText req with
          | .error r => r
          | .ok chart => renderChart o chart out

def fallbackTemplate (chart : List MedReq) : String :=
  String.intercalate "\n" ((chart.filter (·.active)).map fun m =>
    "Take {{drug:" ++ String.ofList m.id ++ "}} {{sig:" ++ String.ofList m.id ++ "}}.")

def handleFallback (o : Opts) (req : Lean.Json) : Lean.Json × UInt8 :=
  match requestChart o.ignoreFreeText req with
  | .error r => r
  | .ok chart =>
      let out := fallbackTemplate chart
      if out.isEmpty then (errorJson "the request has no active MedicationRequest", 1) else
      match outputProblem out with
      | some e => (errorJson e, 1)
      | none => renderChart o chart out

def respondLine (handler : Lean.Json → Lean.Json × UInt8) (line : String) : Lean.Json × UInt8 :=
  if line.utf8ByteSize > maxRequestBytes then
    (errorJson s!"the request is larger than {maxRequestBytes} bytes", 1)
  else
    match requestProblem line with
    | some problem => (errorJson problem, 1)
    | none =>
        match Lean.Json.parse line with
        | .error e => (errorJson ("invalid JSON: " ++ e), 1)
        | .ok req => handler req

partial def readAll (h : IO.FS.Stream) (acc : String := "") : IO String := do
  let line ← h.getLine
  if line.isEmpty then pure acc
  else
    let acc := acc ++ line
    if acc.utf8ByteSize > maxRequestBytes then pure acc else readAll h acc

partial def serveLoop (o : Opts) (stdin stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then return
  let text := line.trimAscii.toString
  if !text.isEmpty then
    stdout.putStrLn (respondLine (handleRender o) text).1.compress
    stdout.flush
  serveLoop o stdin stdout

def parseOptions : List String → Option (Option String × Bool × Bool)
  | [] => some (none, false, false)
  | "--extra-words" :: path :: rest =>
      (parseOptions rest).bind fun (f, i, a) => if f.isSome then none else some (some path, i, a)
  | "--ignore-free-text" :: rest =>
      (parseOptions rest).bind fun (f, i, a) => if i then none else some (f, true, a)
  | "--allow-omissions" :: rest =>
      (parseOptions rest).bind fun (f, i, a) => if a then none else some (f, i, true)
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
  IO.eprintln "usage: dosegate render|serve [--extra-words FILE] [--ignore-free-text] [--allow-omissions], or dosegate fallback"
  pure 1

def optsOf (file? : Option String) (ign allow : Bool) : IO Opts := do
  let pol ← policyOf file?
  pure { policy := { pol with requireAll := !allow }, ignoreFreeText := ign }

def main (args : List String) : IO UInt32 := do
  let stdin ← IO.getStdin
  let stdout ← IO.getStdout
  let (cmd, rest) := match args with
    | c :: r => (c, r)
    | [] => ("", [])
  match cmd, parseOptions rest with
  | "render", some (file?, ign, allow) =>
      let o ← optsOf file? ign allow
      let (resp, code) := respondLine (handleRender o) (← readAll stdin)
      stdout.putStrLn resp.compress
      stdout.flush
      pure code.toUInt32
  | "serve", some (file?, ign, allow) =>
      let o ← optsOf file? ign allow
      serveLoop o stdin stdout
      pure 0
  | "fallback", some (none, false, false) =>
      let o : Opts := { policy := {}, ignoreFreeText := false }
      let (resp, code) := respondLine (handleFallback o) (← readAll stdin)
      stdout.putStrLn resp.compress
      stdout.flush
      pure code.toUInt32
  | _, _ => usage
