/-
The model's output is free text with slots. A slot is written
`{{field:id}}`, where `field` is drug, dose, frequency, route, sig, or daily and
`id` is the id of a MedicationRequest in the patient's record. Any other brace in
the text makes the output malformed, and malformed output is blocked.
-/
import DoseGate.Fhir

namespace DoseGate

inductive Seg where
  | text (cs : List Char)
  | slot (f : Field) (id : List Char)
  deriving Repr, DecidableEq, Inhabited

def isIdChar (c : Char) : Bool := c.isAlphanum || c == '-' || c == '.'

def readSlot? (cs : List Char) : Option (Field × List Char × List Char) :=
  match cs.span (· != '}') with
  | (inside, '}' :: '}' :: after) =>
      match inside.span (· != ':') with
      | (name, ':' :: id) =>
          match Field.ofName? name with
          | some f => if !id.isEmpty && id.all isIdChar then some (f, id, after) else none
          | none => none
      | _ => none
  | _ => none

def flushText (cur : List Char) : List Seg :=
  if cur.isEmpty then [] else [.text cur.reverse]

def parseAux : Nat → List Char → List Char → Option (List Seg)
  | 0, _, _ => none
  | _ + 1, [], cur => some (flushText cur)
  | fuel + 1, '{' :: '{' :: rest, cur =>
      match readSlot? rest with
      | some (f, id, after) => (parseAux fuel after []).map (flushText cur ++ .slot f id :: ·)
      | none => none
  | _ + 1, '{' :: _, _ => none
  | _ + 1, '}' :: _, _ => none
  | fuel + 1, c :: cs, cur => parseAux fuel cs (c :: cur)

def parseTemplate (cs : List Char) : Option (List Seg) := parseAux (cs.length + 1) cs []

def Seg.unparse : Seg → List Char
  | .text cs => cs
  | .slot f id => "{{".toList ++ f.name ++ ':' :: id ++ "}}".toList

def unparse (segs : List Seg) : List Char := segs.flatMap Seg.unparse

end DoseGate
