import DoseGate.Dec

namespace DoseGate

theorem normalize_eqv (d : Dec) : Dec.Eqv d d.normalize := sorry

theorem normalize_isNormal (d : Dec) : d.normalize.IsNormal := sorry

theorem normalize_eq_of_eqv {a b : Dec} (h : Dec.Eqv a b) : a.normalize = b.normalize := sorry

theorem parseDec_fmtDec (d : Dec) : parseDec? (fmtDec d) = some d.normalize := sorry

theorem fmtDec_chars (d : Dec) : ∀ c ∈ fmtDec d, c.isDigit = true ∨ c = '.' := sorry

theorem fmtDec_leading_digit (d : Dec) : ∃ c rest, fmtDec d = c :: rest ∧ c.isDigit = true := sorry

theorem fmtDec_no_trailing_zero (d : Dec) (h : '.' ∈ fmtDec d) : (fmtDec d).getLast? ≠ some '0' := sorry

theorem fmtDec_eq_iff (a b : Dec) : fmtDec a = fmtDec b ↔ Dec.Eqv a b := sorry

end DoseGate
