import DoseGate.Proofs.Render

namespace DoseGate

theorem sentenceOk_value_shape {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = true) :
    itemsOf g = instrShape ∨ itemsOf g = sigShape ∨ itemsOf g = totalShape := by
  unfold sentenceOk at h
  simp only [hv, ite_true, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at h
  rcases h.2 with (h1 | h2) | h3
  · exact Or.inl h1
  · exact Or.inr (Or.inl h2)
  · exact Or.inr (Or.inr h3)

theorem sentenceOk_free_words {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = false) :
    (wordsOf g).all (fun w => wordIn vocab w || wordIn p.extraWords w) = true := by
  unfold sentenceOk at h
  simp only [hv, Bool.false_eq_true, ite_false, Bool.and_eq_true] at h
  exact h.2

theorem sentenceOk_one_order {p : Policy} {g : List Seg} (h : sentenceOk p g = true) :
    ((slotsOf g).map (·.2)).all (· == ((slotsOf g).map (·.2)).headD []) = true := by
  unfold sentenceOk at h
  simp only [Bool.and_eq_true] at h
  exact h.1

theorem checkText_forbidden {p : Policy} {t tok : List Char} (hc : t.all isTextChar = true)
    (hf : (tokens t).find? isForbidden = some tok) : checkText p t = .error (.forbiddenWord tok) := by
  unfold checkText
  simp [hc, hf]

end DoseGate
