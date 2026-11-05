/-
The gate. `render` takes the patient's medication orders and the model's
output, and either returns the text the reader will see or a reason it was
blocked. Nothing else leaves the gate.
-/
import DoseGate.Template
import DoseGate.Tokens

namespace DoseGate

structure Policy where
  allow : List (List Char) := []
  deriving Repr, Inhabited

inductive Block where
  | malformed
  | duplicateIds
  | nonAscii
  | doseTokenInText (tok : List Char)
  | unknownRef (id : List Char)
  | inactiveOrder (id : List Char)
  | missingField (id : List Char) (f : Field)
  | unseparated
  | unbound
  deriving Repr, DecidableEq, Inhabited

def blockedToken (p : Policy) (tok : List Char) : Bool :=
  isDoseToken tok && !p.allow.contains tok

def checkText (p : Policy) (t : List Char) : Except Block Unit :=
  if !t.all (·.toNat < 128) then .error .nonAscii
  else match (tokens t).find? (blockedToken p) with
    | some tok => .error (.doseTokenInText tok)
    | none => .ok ()

def renderSeg (p : Policy) (chart : List MedReq) : Seg → Except Block (List Char)
  | .text t => do checkText p t; pure t
  | .slot f id =>
      match chart.find? (·.id == id) with
      | none => .error (.unknownRef id)
      | some m =>
          if !m.active then .error (.inactiveOrder id)
          else match fmtField f m with
            | none => .error (.missingField id f)
            | some piece => .ok piece

def isSep (c : Char) : Bool := !c.isAlphanum

def separated (a b : List Char) : Bool :=
  (a.getLast?.map isSep).getD false || (b.head?.map isSep).getD false

def sepChain : List (List Char) → Bool
  | a :: b :: rest => separated a b && sepChain (b :: rest)
  | _ => true

def allSeparated (ps : List (List Char)) : Bool := sepChain (ps.filter (!·.isEmpty))

def isSentenceEnd (c : Char) : Bool :=
  c == '.' || c == '!' || c == '?' || c == ';' || c == ':' || c == '\n'

def sentenceGroups : List Seg → List (Field × List Char) → List (List (Field × List Char))
  | [], cur => [cur]
  | .text t :: rest, cur =>
      if t.any isSentenceEnd then cur :: sentenceGroups rest [] else sentenceGroups rest cur
  | .slot f id :: rest, cur => sentenceGroups rest ((f, id) :: cur)

def groupBound (g : List (Field × List Char)) : Bool :=
  let fs := g.map (·.1)
  let ids := g.map (·.2)
  ids.all (· == (ids.headD [])) &&
  fs.Nodup &&
  (!fs.contains .sig || !(fs.contains .dose || fs.contains .frequency || fs.contains .route)) &&
  (!(fs.contains .dose || fs.contains .frequency || fs.contains .route || fs.contains .sig) ||
    fs.contains .drug)

def render (p : Policy) (chart : List MedReq) (out : List Char) : Except Block (List Char) := do
  if !(chart.map (·.id)).Nodup then throw .duplicateIds
  let some segs := parseTemplate out | throw .malformed
  if !(sentenceGroups segs []).all groupBound then throw .unbound
  let pieces ← segs.mapM (renderSeg p chart)
  if !allSeparated pieces then throw .unseparated
  pure pieces.flatten

end DoseGate
