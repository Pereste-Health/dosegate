/-
The approved words for number-only prose, one lowercase ASCII word per line in
data/prose_words.txt, embedded at compile time. In number-only mode a word of
free text outside a value sentence is printed only if it is on this list or in
the deployment's extra words, and it is never number-like (see `numberLike` in
`DoseGate/Tokens.lean`). The list holds no number, quantity, dose unit, schedule,
comparison, drug name, or drug class; `tests/check_prose_words.py` checks this.
-/
namespace DoseGate

def proseWordsText : String := include_str "../data/prose_words.txt"

def proseWords : List String := (proseWordsText.splitOn "\n").filter (fun w => !w.isEmpty)

end DoseGate
