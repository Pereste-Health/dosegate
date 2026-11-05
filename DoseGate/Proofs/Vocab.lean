import DoseGate.Render

namespace DoseGate

theorem vocab_clean : vocab.all (fun w => !isForbidden w.toList) = true := by
  decide +kernel

theorem allowed_not_forbidden {p : Policy} {tok : List Char} (h : allowedWord p tok = true) :
    isForbidden tok = false := by
  unfold allowedWord at h
  cases hf : isForbidden tok
  · rfl
  · simp [hf] at h

end DoseGate
