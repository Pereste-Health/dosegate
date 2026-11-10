import DoseGate.Proofs.Shape
import DoseGate.ProseWords

namespace DoseGate

def shapeWordOk : Item → Bool
  | .w tok => !numberLike tok
  | .s _ => true

theorem numberShapes_words : numberShapes.all (fun S => S.all shapeWordOk) = true := by
  decide +kernel

theorem forall₂_mem_right {R : Seg → List Char → Prop} : ∀ {segs : List Seg} {pieces : List (List Char)},
    Forall₂ R segs pieces → ∀ x ∈ pieces, ∃ s ∈ segs, R s x
  | _, _, .nil, x, hx => by simp at hx
  | _, _, .cons hR hF, x, hx => by
      rcases List.mem_cons.mp hx with rfl | hx
      · exact ⟨_, by simp, hR⟩
      · obtain ⟨s, hs, hRs⟩ := forall₂_mem_right hF x hx
        exact ⟨s, by simp [hs], hRs⟩

theorem segRendersTo_of_renderSeg {p : Policy} {chart : List MedReq} {s : Seg} {x : List Char}
    (hn : (chart.map (·.id)).Nodup) (h : renderSeg p chart s = .ok x) : SegRendersTo chart s x :=
  match forall₂_spec hn (Forall₂.cons h Forall₂.nil) with
  | .cons h1 _ => h1

theorem mem_wordsOf_items : ∀ (g : List Seg) (tok : List Char), tok ∈ wordsOf g →
    Item.w tok ∈ itemsOf g
  | [], _, h => by simp [wordsOf] at h
  | s :: g, tok, h => by
      have ih := mem_wordsOf_items g tok
      cases s with
      | text t =>
        change tok ∈ tokens t ++ wordsOf g at h
        change Item.w tok ∈ (tokens t).map Item.w ++ itemsOf g
        rcases List.mem_append.mp h with h | h
        · exact List.mem_append.mpr (Or.inl (List.mem_map.mpr ⟨tok, h, rfl⟩))
        · exact List.mem_append.mpr (Or.inr (ih h))
      | slot f id =>
        change tok ∈ [] ++ wordsOf g at h
        change Item.w tok ∈ [Item.s f] ++ itemsOf g
        exact List.mem_append.mpr (Or.inr (ih (by simpa using h)))

theorem value_word_not_numberLike {g : List Seg} {tok : List Char} (hg : itemsOf g ∈ numberShapes)
    (hw : tok ∈ wordsOf g) : numberLike tok = false := by
  have hS : (itemsOf g).all shapeWordOk = true := List.all_eq_true.mp numberShapes_words _ hg
  have hi := List.all_eq_true.mp hS (.w tok) (mem_wordsOf_items g tok hw)
  simpa [shapeWordOk] using hi

theorem sentenceOk_num_prose {p : Policy} {g : List Seg} (hn : p.numberOnly = true)
    (h : sentenceOk p g = true) (hv : (slotsOf g).any (isValueField ·.1) = false) :
    (slotsOf g).isEmpty = true ∧
      ∀ w ∈ wordsOf g, numberLike w = false ∧ (wordIn proseWords w || wordIn p.extraWords w) = true := by
  unfold sentenceOk at h
  simp only [hv, hn, Bool.false_eq_true, ↓reduceIte, Bool.and_eq_true] at h
  refine ⟨h.2.1, fun w hw => ?_⟩
  have hall := List.all_eq_true.mp h.2.2 w hw
  simp only [Bool.and_eq_true, Bool.not_eq_true'] at hall
  exact ⟨hall.1, hall.2⟩

theorem sentenceOk_num_value {p : Policy} {g : List Seg} (hn : p.numberOnly = true)
    (h : sentenceOk p g = true) (hv : (slotsOf g).any (isValueField ·.1) = true) :
    itemsOf g ∈ numberShapes := by
  unfold sentenceOk at h
  simp only [hv, hn, ite_true, Bool.and_eq_true] at h
  exact List.elem_iff.mp h.2

theorem text_word_not_numberLike {p : Policy} {segs : List Seg} (hn : p.numberOnly = true)
    (hsent : ∀ g ∈ sentences segs, sentenceOk p g = true) {t : List Char} (ht : Seg.text t ∈ segs)
    {w : List Char} (hw : w ∈ tokens t) : numberLike w = false := by
  have hw' : w ∈ wordsOf segs := List.mem_flatMap.mpr ⟨.text t, ht, hw⟩
  rw [← sentences_words] at hw'
  obtain ⟨g, hg, hwg⟩ := List.mem_flatMap.mp hw'
  cases hc : (slotsOf g).any (isValueField ·.1) with
  | true => exact value_word_not_numberLike (sentenceOk_num_value hn (hsent g hg) hc) hwg
  | false => exact ((sentenceOk_num_prose hn (hsent g hg) hc).2 w hwg).1

theorem number_key {p : Policy} {chart : List MedReq} (hn : p.numberOnly = true) :
    ∀ (segs : List Seg) (pieces : List (List Char)),
    (∀ s ∈ segs, ∀ t, s = .text t → (tokens t).filter numberLike = []) →
    Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces →
    pieces.flatMap (fun pc => (tokens pc).filter numberLike) = valueSlotNumberTokens segs pieces
  | _, _, _, .nil => by simp [valueSlotNumberTokens]
  | s :: segs, x :: pieces, hc, .cons hR hF => by
      have ih := number_key hn segs pieces (fun s' hs' t ht => hc s' (by simp [hs']) t ht) hF
      unfold valueSlotNumberTokens at ih ⊢
      cases s with
      | text t =>
        obtain rfl := renderSeg_text_eq hR
        have hcl := hc (.text x) (by simp) x rfl
        simp [List.zip_cons_cons, Seg.isValueSlot, ih, hcl]
      | slot f id =>
        by_cases hd : f = .drug
        · subst hd
          have hz := renderSeg_drug_number hn hR
          have hz' : (tokens x).filter numberLike = [] := by
            rw [List.filter_eq_nil_iff]
            intro w hw
            have := List.any_eq_false.mp hz w hw
            simpa using this
          simp [List.zip_cons_cons, Seg.isValueSlot, ih, hz']
        · have hv : (Seg.slot f id).isValueSlot = true := by
            cases f <;> simp_all [Seg.isValueSlot]
          simp [List.zip_cons_cons, hv, ih]

theorem numberFilter_flatten {pieces : List (List Char)} (hsep : allSeparated pieces = true) :
    (tokens pieces.flatten).filter numberLike = pieces.flatMap (fun pc => (tokens pc).filter numberLike) := by
  rw [tokens_flatten hsep, List.filter_flatMap]

theorem number_only_no_invented_numbers {p : Policy} {chart : List MedReq} {out r : List Char}
    (hn : p.numberOnly = true) (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧ Forall₂ (SegRendersTo chart) segs pieces ∧
      r = pieces.flatten ∧ (tokens r).filter numberLike = valueSlotNumberTokens segs pieces := by
  obtain ⟨hnodup, segs, pieces, hp, hF, hsep, hr, hsent, -, -, -, -⟩ := render_decomp_full h
  refine ⟨segs, pieces, hp, forall₂_spec hnodup hF, hr, ?_⟩
  rw [hr, numberFilter_flatten hsep]
  refine number_key hn segs pieces ?_ hF
  intro s hs t ht
  subst ht
  rw [List.filter_eq_nil_iff]
  intro w hw
  simpa using text_word_not_numberLike hn hsent hs hw

theorem number_only_fidelity {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧ Forall₂ (SegRendersTo chart) segs pieces ∧
      r = pieces.flatten :=
  render_fidelity h

theorem number_only_value_sentence {p : Policy} {chart : List MedReq} {out r : List Char}
    {segs : List Seg} (hn : p.numberOnly = true) (h : render p chart out = .ok r)
    (hp : parseTemplate out = some segs) :
    ∀ g ∈ sentences segs, (slotsOf g).any (isValueField ·.1) = true →
      itemsOf g ∈ numberShapes ∧ ∃ id, ∀ q ∈ slotsOf g, q.2 = id := by
  intro g hg hv
  have hs := (render_sentences h hp).1 g hg
  obtain ⟨⟨f, id⟩, hm, -⟩ := List.any_eq_true.mp hv
  exact ⟨sentenceOk_num_value hn hs hv, id, sentenceOk_one_id hs hm⟩

theorem number_only_prose_clean {p : Policy} {chart : List MedReq} {out r : List Char}
    {segs : List Seg} (hn : p.numberOnly = true) (h : render p chart out = .ok r)
    (hp : parseTemplate out = some segs) :
    ∀ g ∈ sentences segs, (slotsOf g).any (isValueField ·.1) = false →
      (slotsOf g).isEmpty = true ∧
        ∀ w ∈ wordsOf g, numberLike w = false ∧ (wordIn proseWords w || wordIn p.extraWords w) = true :=
  fun g hg hv => sentenceOk_num_prose hn ((render_sentences h hp).1 g hg) hv

theorem number_only_extra_words_cannot_add {p : Policy} {chart : List MedReq} {out r : List Char}
    {segs : List Seg} (hn : p.numberOnly = true) (ws : List String)
    (h : render {p with extraWords := ws} chart out = .ok r) (hp : parseTemplate out = some segs) :
    ∀ g ∈ sentences segs, (slotsOf g).any (isValueField ·.1) = false →
      ∀ w ∈ wordsOf g, numberLike w = false ∧ (wordIn proseWords w || wordIn ws w) = true :=
  fun g hg hv w hw => (number_only_prose_clean (p := {p with extraWords := ws}) hn h hp g hg hv).2 w hw

theorem number_only_guarantee {p : Policy} {chart : List MedReq} {out r : List Char}
    (hn : p.numberOnly = true) (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧ Forall₂ (SegRendersTo chart) segs pieces ∧
      r = pieces.flatten ∧
      (tokens r).filter numberLike = valueSlotNumberTokens segs pieces ∧
      (∀ g ∈ sentences segs, (slotsOf g).any (isValueField ·.1) = true →
        itemsOf g ∈ numberShapes ∧ ∃ id, ∀ q ∈ slotsOf g, q.2 = id) ∧
      (∀ g ∈ sentences segs, (slotsOf g).any (isValueField ·.1) = false →
        (slotsOf g).isEmpty = true ∧
          ∀ w ∈ wordsOf g, numberLike w = false ∧ (wordIn proseWords w || wordIn p.extraWords w) = true) := by
  obtain ⟨segs, pieces, hp, hF, hr, h1⟩ := number_only_no_invented_numbers hn h
  exact ⟨segs, pieces, hp, hF, hr, h1, number_only_value_sentence hn h hp,
    number_only_prose_clean hn h hp⟩

end DoseGate
