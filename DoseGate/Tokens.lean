/-
Word tokens and dose tokens.

A token is a maximal run of ASCII letters and digits, lowercased. A dose token
is any token that states or implies an amount: one containing a digit, a number
word, or a dose unit word. Free text written by the model may contain no dose
token, so every amount the reader sees has to come from the chart.

This definition is the boundary of the guarantee. A phrasing that names an
amount without any of these tokens is outside what is proved, and its rate is
measured separately.
-/
namespace DoseGate

def tokensAux : List Char → List Char → List (List Char)
  | [], cur => if cur.isEmpty then [] else [cur.reverse]
  | c :: cs, cur =>
      if c.isAlphanum then tokensAux cs (c.toLower :: cur)
      else (if cur.isEmpty then [] else [cur.reverse]) ++ tokensAux cs []

def tokens (cs : List Char) : List (List Char) := tokensAux cs []

def numberWords : List String :=
  ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
   "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
   "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
   "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
   "half", "halves", "quarter", "quarters", "third", "thirds",
   "once", "twice", "thrice", "double", "triple", "dozen", "couple", "single"]

def unitWords : List String :=
  ["mg", "mcg", "ug", "g", "gram", "grams", "milligram", "milligrams", "microgram",
   "micrograms", "kg", "ml", "milliliter", "milliliters", "millilitre", "millilitres",
   "l", "liter", "liters", "litre", "litres", "cc", "u", "iu", "unit", "units",
   "meq", "mmol", "tablet", "tablets", "tab", "tabs", "pill", "pills", "capsule",
   "capsules", "cap", "caps", "puff", "puffs", "spray", "sprays", "drop", "drops",
   "patch", "patches", "teaspoon", "teaspoons", "tsp", "tablespoon", "tablespoons",
   "tbsp", "vial", "vials", "ampule", "ampules", "scoop", "scoops"]

def isDoseToken (tok : List Char) : Bool :=
  tok.any Char.isDigit ||
  numberWords.contains (String.ofList tok) ||
  unitWords.contains (String.ofList tok)

end DoseGate
