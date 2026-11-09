/-
The gate. `render` takes the patient's medication orders and the model's
output, and either returns the text the reader will see or a reason it was
blocked. Nothing else leaves the gate.
-/
import DoseGate.Template
import DoseGate.Tokens

namespace DoseGate

structure Policy where
  extraWords : List String := []
  requireAll : Bool := true
  deriving Repr, Inhabited

inductive Block where
  | malformed
  | duplicateIds
  | disallowedCharacter
  | forbiddenWord (tok : List Char)
  | unknownWord (tok : List Char)
  | unknownRef (id : List Char)
  | inactiveOrder (id : List Char)
  | missingField (id : List Char) (f : Field)
  | unseparated
  | unbound
  | repeatedValue
  | ambiguousDrug (id : List Char)
  | signBeforeSlot
  | omittedOrder (id : List Char)
  | noActiveOrder
  deriving Repr, DecidableEq, Inhabited

def allowedWord (p : Policy) (tok : List Char) : Bool :=
  !isForbidden tok &&
    (wordIn vocab tok || wordIn instrWords tok || wordIn totalWords tok || wordIn p.extraWords tok)

def isTextChar (c : Char) : Bool :=
  c.isAlphanum || c == ' ' || c == '\n' || c == '.' || c == ',' || c == ';' || c == ':' ||
    c == '(' || c == ')' || c == '\'' || c == '"' || c == '-' || c == '/'

def checkText (p : Policy) (t : List Char) : Except Block Unit :=
  if !t.all isTextChar then .error .disallowedCharacter
  else match (tokens t).find? isForbidden with
    | some tok => .error (.forbiddenWord tok)
    | none => match (tokens t).find? (fun tok => !allowedWord p tok) with
      | some tok => .error (.unknownWord tok)
      | none => .ok ()

def renderSeg (p : Policy) (chart : List MedReq) : Seg → Except Block (List Char)
  | .text t => do checkText p t; pure t
  | .slot f id =>
      match chart.find? (·.id == id) with
      | none => .error (.unknownRef id)
      | some m =>
          if !m.active then .error (.inactiveOrder id)
          else if (chart.filter fun m' => m'.active && relatedDrug m'.drug m.drug).length > 1 then
            .error (.ambiguousDrug id)
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

def splitEnds (t : List Char) : List (List Char) :=
  t.foldr (fun c acc => if isSentenceEnd c then [] :: acc else
    match acc with
    | q :: qs => (c :: q) :: qs
    | [] => [[c]]) [[]]

def sentencesAux : List Seg → List Seg → List (List Seg)
  | [], cur => [cur]
  | .slot f id :: rest, cur => sentencesAux rest (cur ++ [.slot f id])
  | .text t :: rest, cur =>
      match splitEnds t with
      | [] => sentencesAux rest cur
      | [q] => sentencesAux rest (cur ++ [.text q])
      | q :: qs =>
          (cur ++ [.text q]) :: (qs.dropLast.map fun r => [Seg.text r]) ++
            sentencesAux rest [.text (qs.getLast?.getD [])]

def sentences (segs : List Seg) : List (List Seg) := sentencesAux segs []

def slotsOf (g : List Seg) : List (Field × List Char) :=
  g.filterMap fun
    | .slot f id => some (f, id)
    | .text _ => none

def wordsOf (g : List Seg) : List (List Char) :=
  g.flatMap fun
    | .text t => tokens t
    | .slot _ _ => []

def isValueField : Field → Bool
  | .drug => false
  | _ => true

inductive Item where
  | w (tok : List Char)
  | s (f : Field)
  deriving Repr, DecidableEq

def itemsOf (g : List Seg) : List Item :=
  g.flatMap fun
    | .text t => (tokens t).map Item.w
    | .slot f _ => [Item.s f]

def instrShape : List Item := [.w "take".toList, .s .drug, .s .dose, .s .route, .s .frequency]

def sigShape : List Item := [.w "take".toList, .s .drug, .s .sig]

def instrDailyShape : List Item :=
  instrShape ++ [.w "which".toList, .w "is".toList, .s .daily]

def sigDailyShape : List Item :=
  sigShape ++ [.w "which".toList, .w "is".toList, .s .daily]

def sentenceOk (p : Policy) (g : List Seg) : Bool :=
  let sl := slotsOf g
  let ids := sl.map (·.2)
  ids.all (· == ids.headD []) &&
  (if sl.any (isValueField ·.1) then
    itemsOf g == instrShape || itemsOf g == sigShape || itemsOf g == instrDailyShape ||
      itemsOf g == sigDailyShape
  else sl.isEmpty && (wordsOf g).all (fun w => wordIn vocab w || wordIn p.extraWords w))

def valueSlots (segs : List Seg) : List (Field × List Char) :=
  (slotsOf segs).filter (isValueField ·.1)

def noRepeatedValue (segs : List Seg) : Bool :=
  let vs := valueSlots segs
  vs.Nodup &&
  vs.all fun fi => fi.1 != .sig ||
    !vs.any fun gj => gj.2 == fi.2 && (gj.1 == .dose || gj.1 == .route || gj.1 == .frequency)

def endsSign (t : List Char) : Bool :=
  (t.reverse.takeWhile (fun c => !c.isAlphanum)).any (fun c => c == '-' || c == '+' || c == '/')

def hasSignBeforeSlot : List Seg → Bool
  | .text t :: .slot f id :: rest => endsSign t || hasSignBeforeSlot (.slot f id :: rest)
  | _ :: rest => hasSignBeforeSlot rest
  | [] => false

def unnamedOrder (p : Policy) (chart : List MedReq) (segs : List Seg) : Option (List Char) :=
  if p.requireAll then
    (chart.find? fun m => m.active && !(valueSlots segs).any (·.2 == m.id)).map (·.id)
  else none

def render (p : Policy) (chart : List MedReq) (out : List Char) : Except Block (List Char) := do
  if !(chart.map (·.id)).Nodup then throw .duplicateIds
  let some segs := parseTemplate out | throw .malformed
  if !(sentences segs).all (sentenceOk p) then throw .unbound
  if !noRepeatedValue segs then throw .repeatedValue
  if hasSignBeforeSlot segs then throw .signBeforeSlot
  match unnamedOrder p chart segs with
  | some id => throw (.omittedOrder id)
  | none => pure ()
  let pieces ← segs.mapM (renderSeg p chart)
  if !allSeparated pieces then throw .unseparated
  if p.requireAll && chart.all (!·.active) then throw .noActiveOrder
  pure pieces.flatten

end DoseGate
