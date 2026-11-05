import DoseGate.Render

namespace DoseGate

theorem vocab_clean : vocab.all (fun w => !isForbidden w.toList) = true := sorry

theorem allowed_not_forbidden {p : Policy} {tok : List Char} (h : allowedWord p tok = true) :
    isForbidden tok = false := sorry

end DoseGate
