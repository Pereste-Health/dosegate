/-
What a correct rendering means. These definitions are the specification the
theorems in `DoseGate/Proofs` are stated against.

A text segment renders to itself. A slot renders to the formatted field of the
one active order in the chart that has the slot's id.
-/
import DoseGate.Render

namespace DoseGate

inductive Forall₂ {α β : Type} (R : α → β → Prop) : List α → List β → Prop where
  | nil : Forall₂ R [] []
  | cons {a : α} {b : β} {as : List α} {bs : List β} : R a b → Forall₂ R as bs → Forall₂ R (a :: as) (b :: bs)

def SegRendersTo (chart : List MedReq) : Seg → List Char → Prop
  | .text t, piece => piece = t
  | .slot f id, piece =>
      ∃ m ∈ chart, m.id = id ∧ m.active = true ∧ fmtField f m = some piece ∧
        ∀ m' ∈ chart, m'.id = id → m' = m

def Seg.isSlot : Seg → Bool
  | .slot _ _ => true
  | .text _ => false

def Seg.isValueSlot : Seg → Bool
  | .slot .drug _ => false
  | .slot _ _ => true
  | .text _ => false

def valueSlotTokens (segs : List Seg) (pieces : List (List Char)) : List (List Char) :=
  ((segs.zip pieces).filter (·.1.isValueSlot)).flatMap fun sp => (tokens sp.2).filter isForbidden

def valueSlotNumberTokens (segs : List Seg) (pieces : List (List Char)) : List (List Char) :=
  ((segs.zip pieces).filter (·.1.isValueSlot)).flatMap fun sp => (tokens sp.2).filter numberLike

end DoseGate
