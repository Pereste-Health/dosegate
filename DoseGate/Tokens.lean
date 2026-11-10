/-
Word tokens, the forbidden word classes, and the free-text vocabulary.

A token is a maximal run of ASCII letters and digits, lowercased. A token is
forbidden when it contains a digit or belongs to one of five word classes:
number words, dose unit words, route words, frequency and timing words, and
negation or qualifier words. Words in these classes may reach the reader only
from a filled slot.

Free text written by the model may use only words from `vocab`, a fixed list of
common words, together with any extra words a deployment adds. A forbidden
token is rejected even if a deployment adds it. `vocab_clean` in
`DoseGate/Proofs/Vocab.lean` checks that no vocabulary word is forbidden.

Two drug names are related when a reader could mistake one for the other, for
example when they differ only in case, share a word, or one word begins with
another. `relatedDrug` decides this conservatively.

Number-only mode uses a different test on model text. A token is number-like
when it could state a quantity, a dose unit, a schedule, or a change in amount.
`numberLike` decides this. In number-only mode, prose may use only words on the
approved list in `DoseGate/ProseWords.lean`, or the deployment's extra words, and
no prose word may be number-like.
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
   "once", "twice", "thrice", "double", "doubled", "triple", "tripled", "dbl",
   "dozen", "couple", "pair", "single", "both", "several", "few", "many", "much",
   "ii", "iii", "iv", "vi", "x", "tenfold", "extra", "another", "all", "some", "any"]

def unitWords : List String :=
  ["mcgs", "oz", "ounce", "ounces", "gtt", "gtts", "mg", "mgs", "mcg", "ug", "g", "gm", "gms", "gram", "grams", "milligram", "milligrams",
   "microgram", "micrograms", "kg", "ml", "mls", "milliliter", "milliliters", "millilitre",
   "millilitres", "l", "liter", "liters", "litre", "litres", "cc", "u", "iu", "ius", "unit",
   "units", "meq", "mmol", "tablet", "tablets", "tab", "tabs", "pill", "pills", "capsule",
   "capsules", "cap", "caps", "puff", "puffs", "spray", "sprays", "drop", "drops", "patch",
   "patches", "teaspoon", "teaspoons", "tsp", "tablespoon", "tablespoons", "tbsp", "vial",
   "vials", "ampule", "ampules", "ampoule", "ampoules", "scoop", "scoops", "dose", "doses",
   "dosage", "amount", "amounts", "strength", "strengths"]

def routeWords : List String :=
  ["sl", "pr", "pv", "it", "intrathecal", "intranasal", "into", "mouth", "oral", "orally", "po", "tongue", "sublingual", "sublingually", "skin",
   "subcutaneous", "subcutaneously", "sc", "sq", "subq", "shot", "shots", "inject",
   "injected", "injection", "injections", "needle", "vein", "iv", "intravenous",
   "intravenously", "muscle", "im", "intramuscular", "intramuscularly", "inhale",
   "inhaled", "inhaler", "breathe", "nose", "nasal", "eye", "eyes", "ear", "ears",
   "rectal", "rectum", "rectally", "topical", "topically", "transdermal", "swallow",
   "chew", "crush", "dissolve", "apply", "rub", "tube", "drip", "infusion", "route"]

def frequencyWords : List String :=
  ["qam", "qpm", "qw", "stat", "immediately", "promptly", "asap", "sleep", "sleeping", "meal", "meals", "food", "feel", "feeling", "daily", "day", "days", "nightly", "night", "nights", "morning", "mornings", "evening",
   "evenings", "noon", "bedtime", "breakfast", "lunch", "dinner", "supper", "hour", "hours",
   "hourly", "minute", "minutes", "week", "weeks", "weekly", "month", "months", "monthly",
   "year", "every", "each", "per", "times", "bid", "tid", "qid", "qd", "qod", "qhs", "prn",
   "q", "h", "hs", "ac", "pc", "needed", "directed", "regularly", "often", "frequency",
   "schedule", "scheduled", "today", "tonight", "tomorrow", "always", "again", "until",
   "before", "after", "while", "during", "when", "whenever", "then", "later", "now"]

def negationWords : List String :=
  ["may", "might", "can", "could", "should", "would", "as", "keep", "keeping", "continue", "lower", "lowered", "raise", "adjust", "exactly", "not", "no", "never", "don", "dont", "doesn", "t", "stop", "stopped", "skip", "skipped",
   "hold", "pause", "quit", "avoid", "without", "instead", "only", "if", "unless", "except",
   "but", "or", "nor", "cancel", "discontinue", "discontinued", "restart", "resume", "change",
   "increase", "increased", "decrease", "decreased", "reduce", "more", "less", "fewer", "most",
   "least", "max", "maximum", "min", "minimum", "up", "approximately", "about",
   "around", "roughly", "usual", "normal", "other", "else", "same", "replace"]

def vocab : List String :=
  ["a", "an", "the", "and", "to", "of", "for", "on", "at", "by", "from", "here", "there",
   "this", "that", "these", "those", "its", "they", "them", "their", "you", "your",
   "yours", "we", "our", "us", "is", "are", "be", "been", "being", "was", "were", "will",
   "also", "so", "ask", "have", "has", "medicine", "medicines", "medication", "medications",
   "list", "doctor", "doctors", "nurse", "nurses", "pharmacist", "pharmacists", "care", "team",
   "question", "questions", "please", "thank", "thanks", "hello", "hi",
   "information", "read", "carefully", "what", "who", "how", "why"]

def instrWords : List String := ["take"]

def totalWords : List String := ["which", "is"]

def nameStopWords : List String :=
  ["see", "call", "get", "help", "helps", "medical", "first", "milk", "water", "bleeding",
   "sliding", "scale", "taper", "tapering", "titrate", "titration", "protocol", "per", "until",
   "then", "do", "does", "go", "contact", "emergency", "urgent", "check", "monitor", "wait",
   "give", "use", "instructions", "instruction", "note", "refer", "label", "package", "insert",
   "phone", "office", "clinic", "hospital", "appointment", "visit", "start", "starting", "begin",
   "increase", "decrease", "reduce", "change", "switch", "new", "old", "prior", "previous",
   "replace", "replaced", "discontinue", "discontinued", "cancel", "cancelled", "canceled",
   "error", "wrong", "void", "sample", "placeholder", "unknown", "other", "misc", "test",
   "result", "results", "inr", "level", "levels"]

def wordIn (ws : List String) (tok : List Char) : Bool := ws.contains (String.ofList tok)

def isForbidden (tok : List Char) : Bool :=
  tok.any Char.isDigit || wordIn numberWords tok || wordIn unitWords tok ||
  wordIn routeWords tok || wordIn frequencyWords tok || wordIn negationWords tok

def isNameWord (tok : List Char) : Bool :=
  wordIn vocab tok || wordIn instrWords tok || wordIn totalWords tok || wordIn nameStopWords tok

def plainQuantifiers : List String := ["all", "some", "any", "both"]

def doseNouns : List String := ["dose", "doses", "dosage"]

def scheduleWords : List String :=
  ["every", "each", "per", "daily", "nightly", "weekly", "monthly", "hourly", "times", "bid",
   "tid", "qid", "qd", "qod", "qhs", "prn", "qam", "qpm", "qw", "q", "h", "hs", "ac", "pc",
   "morning", "mornings", "evening", "evenings", "night", "nights", "noon", "bedtime",
   "breakfast", "lunch", "dinner", "supper", "meal", "meals", "hour", "hours", "minute",
   "minutes", "day", "days", "week", "weeks", "month", "months", "year", "today", "tonight",
   "tomorrow", "again"]

def quantityChangeWords : List String :=
  ["more", "less", "fewer", "increase", "increased", "decrease", "decreased", "reduce", "lower",
   "lowered", "raise", "adjust", "max", "maximum", "min", "minimum", "most", "least"]

def romanWords : List String :=
  ["ii", "iii", "iv", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xv", "xx"]

def numberPrefixes : List String :=
  ["four", "five", "seven", "nine", "twelve", "twenty", "thirty", "forty", "fifty", "sixty",
   "eighty", "ninety", "hundred", "thousand", "million"]

def numberSuffixes : List String := ["mg", "mcg", "ml"]

def asciiLetterToken (tok : List Char) : Bool := tok.all Char.isAlpha

def nonAsciiChar (c : Char) : Bool := c.toNat ≥ 128

def relatedDrug (a b : List Char) : Bool :=
  !(tokens a).any asciiLetterToken || !(tokens b).any asciiLetterToken ||
  a.any nonAsciiChar || b.any nonAsciiChar ||
  a.map Char.toLower == b.map Char.toLower ||
  (tokens a).any fun u => (tokens b).any fun v =>
    u == v || (4 ≤ u.length && u.isPrefixOf v) || (4 ≤ v.length && v.isPrefixOf u)

def numberLike (tok : List Char) : Bool :=
  tok.any Char.isDigit ||
  (wordIn numberWords tok && !wordIn plainQuantifiers tok) ||
  (wordIn unitWords tok && !wordIn doseNouns tok) ||
  wordIn scheduleWords tok || wordIn quantityChangeWords tok ||
  (tok.length == 1 && tok != "a".toList && tok != "i".toList) ||
  wordIn romanWords tok ||
  numberPrefixes.any (fun pre => pre.toList.isPrefixOf tok) ||
  numberSuffixes.any (fun suf => suf.toList.isSuffixOf tok)

end DoseGate
