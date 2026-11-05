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
  ["mg", "mgs", "mcg", "ug", "g", "gm", "gms", "gram", "grams", "milligram", "milligrams",
   "microgram", "micrograms", "kg", "ml", "mls", "milliliter", "milliliters", "millilitre",
   "millilitres", "l", "liter", "liters", "litre", "litres", "cc", "u", "iu", "ius", "unit",
   "units", "meq", "mmol", "tablet", "tablets", "tab", "tabs", "pill", "pills", "capsule",
   "capsules", "cap", "caps", "puff", "puffs", "spray", "sprays", "drop", "drops", "patch",
   "patches", "teaspoon", "teaspoons", "tsp", "tablespoon", "tablespoons", "tbsp", "vial",
   "vials", "ampule", "ampules", "ampoule", "ampoules", "scoop", "scoops", "dose", "doses",
   "dosage", "amount", "amounts", "strength", "strengths"]

def routeWords : List String :=
  ["mouth", "oral", "orally", "po", "tongue", "sublingual", "sublingually", "skin",
   "subcutaneous", "subcutaneously", "sc", "sq", "subq", "shot", "shots", "inject",
   "injected", "injection", "injections", "needle", "vein", "iv", "intravenous",
   "intravenously", "muscle", "im", "intramuscular", "intramuscularly", "inhale",
   "inhaled", "inhaler", "breathe", "nose", "nasal", "eye", "eyes", "ear", "ears",
   "rectal", "rectum", "rectally", "topical", "topically", "transdermal", "swallow",
   "chew", "crush", "dissolve", "apply", "rub", "tube", "drip", "infusion", "route"]

def frequencyWords : List String :=
  ["daily", "day", "days", "nightly", "night", "nights", "morning", "mornings", "evening",
   "evenings", "noon", "bedtime", "breakfast", "lunch", "dinner", "supper", "hour", "hours",
   "hourly", "minute", "minutes", "week", "weeks", "weekly", "month", "months", "monthly",
   "year", "every", "each", "per", "times", "bid", "tid", "qid", "qd", "qod", "qhs", "prn",
   "q", "h", "hs", "ac", "pc", "needed", "directed", "regularly", "often", "frequency",
   "schedule", "scheduled", "today", "tonight", "tomorrow", "always", "again", "until",
   "before", "after", "while", "during", "when", "whenever", "then", "later", "now"]

def negationWords : List String :=
  ["not", "no", "never", "don", "dont", "doesn", "t", "stop", "stopped", "skip", "skipped",
   "hold", "pause", "quit", "avoid", "without", "instead", "only", "if", "unless", "except",
   "but", "or", "nor", "cancel", "discontinue", "discontinued", "restart", "resume", "change",
   "increase", "increased", "decrease", "decreased", "reduce", "more", "less", "fewer", "most",
   "least", "max", "maximum", "min", "minimum", "up", "least", "approximately", "about",
   "around", "roughly", "usual", "normal", "other", "else", "same", "instead", "replace"]

def vocab : List String :=
  ["a", "an", "the", "and", "to", "of", "for", "in", "on", "at", "with", "by", "from", "into",
   "this", "that", "these", "those", "it", "its", "they", "them", "their", "you", "your",
   "yours", "we", "our", "us", "is", "are", "be", "been", "being", "was", "were", "will", "can",
   "may", "might", "should", "could", "would", "do", "does", "also", "so", "because", "which",
   "who", "what", "how", "why", "here", "there", "please", "thank", "thanks", "as",
   "take", "taking", "takes", "keep", "keeps", "keeping", "help", "helps", "helping", "work",
   "works", "working", "lower", "lowers", "lowering", "control", "controls", "controlling",
   "prevent", "prevents", "preventing", "protect", "protects", "protecting", "relax", "relaxes",
   "relaxing", "manage", "manages", "managing", "treat", "treats", "treating", "ease", "eases",
   "support", "supports", "feel", "feeling", "remember", "follow", "ask", "call", "tell", "talk",
   "get", "stay", "make", "makes", "let", "have", "has", "see", "use", "using",
   "medicine", "medicines", "medication", "medications", "heart", "blood", "pressure", "sugar",
   "cholesterol", "pain", "body", "kidney", "kidneys", "liver", "lungs", "lung", "breathing",
   "vessels", "vessel", "arteries", "artery", "muscles", "swelling", "fluid", "water", "salt",
   "health", "doctor", "nurse", "pharmacist", "care", "team", "question", "questions", "side",
   "effect", "effects", "stroke", "strokes", "attack", "attacks", "infection", "infections",
   "thyroid", "mood", "sleep", "stomach", "food", "meal", "glass", "condition", "conditions",
   "level", "levels", "risk", "plan", "list", "clots", "clot", "bones", "bone", "joints",
   "inflammation", "fever", "allergies", "anxiety", "depression", "seizures", "diabetes",
   "asthma", "healthy", "well", "better", "steady", "stable", "high", "low", "strong", "safe",
   "safely", "important", "good", "exactly", "prescribed", "calm", "comfortable",
   "relaxed", "open", "clear", "flowing", "smoothly", "properly", "symptoms", "symptom", "life"]

def wordIn (ws : List String) (tok : List Char) : Bool := ws.contains (String.ofList tok)

def isForbidden (tok : List Char) : Bool :=
  tok.any Char.isDigit || wordIn numberWords tok || wordIn unitWords tok ||
  wordIn routeWords tok || wordIn frequencyWords tok || wordIn negationWords tok

end DoseGate
