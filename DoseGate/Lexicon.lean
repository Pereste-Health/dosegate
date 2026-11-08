import Std.Data.HashSet

/-
The drug-name lexicon: every RxNorm ingredient, precise ingredient, multiple
ingredient, and brand name (term types IN, PIN, MIN, BN), lowercased, one per
line in data/rxnorm_names.txt, embedded at compile time. The reader prints a
drug name only if, lowercased, it is one of these names.
-/
namespace DoseGate

def lexiconText : String := include_str "../data/rxnorm_names.txt"

def lexicon : Std.HashSet String :=
  (lexiconText.splitOn "\n").foldl (fun s n => if n.isEmpty then s else s.insert n)
    (Std.HashSet.emptyWithCapacity 32768)

def inLexicon (name : String) : Bool := lexicon.contains name.trimAscii.toString.toLower

end DoseGate
