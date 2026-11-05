import DoseGate.Proofs.Render

namespace DoseGate

theorem sentenceOk_value_shape {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = true) :
    itemsOf g = instrShape ∨ itemsOf g = sigShape ∨ itemsOf g = instrDailyShape ∨
      itemsOf g = sigDailyShape := by
  unfold sentenceOk at h
  simp only [hv, ite_true, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at h
  rcases h.2 with ((h1 | h2) | h3) | h4
  · exact Or.inl h1
  · exact Or.inr (Or.inl h2)
  · exact Or.inr (Or.inr (Or.inl h3))
  · exact Or.inr (Or.inr (Or.inr h4))

theorem sentenceOk_free {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = false) :
    (slotsOf g).isEmpty = true ∧ (wordsOf g).all (fun w => wordIn vocab w || wordIn p.extraWords w) = true := by
  unfold sentenceOk at h
  simp only [hv, Bool.false_eq_true, ite_false, Bool.and_eq_true] at h
  exact h.2

theorem sentenceOk_free_words {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = false) :
    (wordsOf g).all (fun w => wordIn vocab w || wordIn p.extraWords w) = true :=
  (sentenceOk_free h hv).2

theorem sentenceOk_one_order {p : Policy} {g : List Seg} (h : sentenceOk p g = true) :
    ((slotsOf g).map (·.2)).all (· == ((slotsOf g).map (·.2)).headD []) = true := by
  unfold sentenceOk at h
  simp only [Bool.and_eq_true] at h
  exact h.1

theorem mem_slotsOf_of_slot : ∀ (g : List Seg) (f : Field) (id : List Char),
    Seg.slot f id ∈ g → (f, id) ∈ slotsOf g
  | [], _, _, h => by simp at h
  | s :: g, f, id, h => by
      rcases List.mem_cons.mp h with rfl | h'
      · simp [slotsOf]
      · have ih := mem_slotsOf_of_slot g f id h'
        cases s <;> simp_all [slotsOf]

theorem mem_of_mem_slotsOf (g : List Seg) (f : Field) (id : List Char) (h : (f, id) ∈ slotsOf g) :
    Seg.slot f id ∈ g := by
  unfold slotsOf at h
  rw [List.mem_filterMap] at h
  obtain ⟨s, hs, hsf⟩ := h
  cases s with
  | text t => simp at hsf
  | slot f' id' =>
    simp only [Option.some.injEq, Prod.mk.injEq] at hsf
    obtain ⟨rfl, rfl⟩ := hsf
    exact hs

theorem sentenceOk_free_no_slot {p : Policy} {g : List Seg} (h : sentenceOk p g = true)
    (hv : (slotsOf g).any (isValueField ·.1) = false) : ∀ s ∈ g, s.isSlot = false := by
  intro s hs
  cases s with
  | text t => rfl
  | slot f id =>
    exfalso
    have hm := mem_slotsOf_of_slot g f id hs
    have he := (sentenceOk_free h hv).1
    rw [List.isEmpty_iff] at he
    rw [he] at hm
    simp at hm

theorem sentenceOk_one_id {p : Policy} {g : List Seg} {f : Field} {id : List Char}
    (h : sentenceOk p g = true) (hm : (f, id) ∈ slotsOf g) :
    ∀ q ∈ slotsOf g, q.2 = id := by
  have h1 := sentenceOk_one_order h
  rw [List.all_eq_true] at h1
  have hid : id ∈ (slotsOf g).map (·.2) := List.mem_map.mpr ⟨(f, id), hm, rfl⟩
  intro q hq
  have hq' : q.2 ∈ (slotsOf g).map (·.2) := List.mem_map.mpr ⟨q, hq, rfl⟩
  have e1 := h1 _ hq'
  have e2 := h1 _ hid
  simp only [beq_iff_eq] at e1 e2
  exact e1.trans e2.symm

theorem slotsOf_text_map : ∀ L : List (List Char),
    (L.map fun r => [Seg.text r]).flatMap slotsOf = []
  | [] => rfl
  | r :: L => by simp [slotsOf, slotsOf_text_map L]

theorem sentencesAux_slots : ∀ (segs cur : List Seg),
    (sentencesAux segs cur).flatMap slotsOf = slotsOf cur ++ slotsOf segs
  | [], cur => by simp [sentencesAux, slotsOf]
  | .slot f id :: rest, cur => by
      simp only [sentencesAux]
      rw [sentencesAux_slots rest]
      simp [slotsOf]
  | .text t :: rest, cur => by
      obtain ⟨q, qs, hs⟩ := splitEnds_exists t
      cases qs with
      | nil =>
          have e : sentencesAux (.text t :: rest) cur = sentencesAux rest (cur ++ [Seg.text q]) := by
            simp [sentencesAux, hs]
          rw [e, sentencesAux_slots rest (cur ++ [Seg.text q])]
          simp [slotsOf]
      | cons q2 qs2 =>
          have e : sentencesAux (.text t :: rest) cur =
              (cur ++ [Seg.text q]) :: (((q2 :: qs2).dropLast).map fun r => [Seg.text r]) ++
                sentencesAux rest [Seg.text ((q2 :: qs2).getLast?.getD [])] := by
            simp [sentencesAux, hs]
          rw [e, List.flatMap_append, List.flatMap_cons, slotsOf_text_map, sentencesAux_slots rest]
          simp [slotsOf]

theorem slot_in_sentence {segs : List Seg} {f : Field} {id : List Char}
    (hs : (f, id) ∈ slotsOf segs) : ∃ g ∈ sentences segs, (f, id) ∈ slotsOf g := by
  have h : (f, id) ∈ (sentences segs).flatMap slotsOf := by
    unfold sentences
    rw [sentencesAux_slots]
    exact List.mem_append.mpr (Or.inr hs)
  exact List.mem_flatMap.mp h

theorem item_of_slot : ∀ (g : List Seg) (f : Field) (id : List Char),
    Seg.slot f id ∈ g → Item.s f ∈ itemsOf g
  | [], _, _, h => by simp at h
  | s :: g, f, id, h => by
      unfold itemsOf
      rw [List.flatMap_cons]
      rcases List.mem_cons.mp h with rfl | h'
      · simp
      · exact List.mem_append.mpr (Or.inr (item_of_slot g f id h'))

theorem item_slot : ∀ (g : List Seg) (f : Field), Item.s f ∈ itemsOf g → ∃ id, (f, id) ∈ slotsOf g
  | [], _, h => by simp [itemsOf] at h
  | s :: g, f, h => by
      unfold itemsOf at h
      rw [List.flatMap_cons] at h
      rcases List.mem_append.mp h with h1 | h2
      · cases s with
        | text t =>
            simp only [List.mem_map] at h1
            obtain ⟨w, -, hw⟩ := h1
            exact absurd hw (by simp)
        | slot f' id' =>
            simp only [List.mem_singleton, Item.s.injEq] at h1
            subst h1
            exact ⟨id', by simp [slotsOf]⟩
      · obtain ⟨id, hid⟩ := item_slot g f (by simpa [itemsOf] using h2)
        cases s with
        | text t => exact ⟨id, by simpa [slotsOf] using hid⟩
        | slot f' id' => exact ⟨id, by simpa [slotsOf] using Or.inr hid⟩

theorem render_value_sentence {p : Policy} {chart : List MedReq} {out r : List Char} {segs : List Seg}
    {f : Field} {id : List Char}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs)
    (hs : Seg.slot f id ∈ segs) :
    ∃ g ∈ sentences segs, Seg.slot f id ∈ g ∧ (∀ q ∈ slotsOf g, q.2 = id) ∧
      (itemsOf g = instrShape ∨ itemsOf g = sigShape ∨ itemsOf g = instrDailyShape ∨
        itemsOf g = sigDailyShape) := by
  obtain ⟨hs', -⟩ := render_sentences h hp
  obtain ⟨g, hg, hm⟩ := slot_in_sentence (mem_slotsOf_of_slot segs f id hs)
  have hsg := hs' g hg
  have hslot := mem_of_mem_slotsOf g f id hm
  have hv : (slotsOf g).any (isValueField ·.1) = true := by
    cases hc : (slotsOf g).any (isValueField ·.1) with
    | true => rfl
    | false =>
      exfalso
      have := sentenceOk_free_no_slot hsg hc (Seg.slot f id) hslot
      simp [Seg.isSlot] at this
  exact ⟨g, hg, hslot, sentenceOk_one_id hsg hm, sentenceOk_value_shape hsg hv⟩

theorem render_daily_sentence {p : Policy} {chart : List MedReq} {out r : List Char}
    {segs : List Seg} {id : List Char}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs)
    (hs : Seg.slot .daily id ∈ segs) :
    ∃ g ∈ sentences segs, Seg.slot .daily id ∈ g ∧
      ((Seg.slot .dose id ∈ g ∧ Seg.slot .route id ∈ g ∧ Seg.slot .frequency id ∈ g) ∨
        Seg.slot .sig id ∈ g) := by
  obtain ⟨g, hg, hgs, hid, hshape⟩ := render_value_sentence h hp hs
  have key : ∀ f', Item.s f' ∈ itemsOf g → Seg.slot f' id ∈ g := by
    intro f' hf'
    obtain ⟨id', hid'⟩ := item_slot g f' hf'
    have e : id' = id := hid _ hid'
    rw [e] at hid'
    exact mem_of_mem_slotsOf g f' id hid'
  have hd : Item.s .daily ∈ itemsOf g := item_of_slot g .daily id hgs
  refine ⟨g, hg, hgs, ?_⟩
  rcases hshape with h1 | h2 | h3 | h4
  · rw [h1] at hd
    simp [instrShape] at hd
  · rw [h2] at hd
    simp [sigShape] at hd
  · exact Or.inl ⟨key .dose (by rw [h3]; simp [instrDailyShape, instrShape]),
      key .route (by rw [h3]; simp [instrDailyShape, instrShape]),
      key .frequency (by rw [h3]; simp [instrDailyShape, instrShape])⟩
  · exact Or.inr (key .sig (by rw [h4]; simp [sigDailyShape, sigShape]))

theorem checkText_forbidden {p : Policy} {t tok : List Char} (hc : t.all isTextChar = true)
    (hf : (tokens t).find? isForbidden = some tok) : checkText p t = .error (.forbiddenWord tok) := by
  unfold checkText
  simp [hc, hf]

theorem render_all_orders_named {p : Policy} {chart : List MedReq} {out r : List Char}
    (hreq : p.requireAll = true) (h : render p chart out = .ok r) :
    ∃ segs, parseTemplate out = some segs ∧
      ∀ m ∈ chart, m.active = true → ∃ f, f ≠ .drug ∧ Seg.slot f m.id ∈ segs := by
  obtain ⟨-, segs, -, hp, -, -, -, -, -, -, hom⟩ := render_decomp_full h
  refine ⟨segs, hp, fun m hm ha => ?_⟩
  unfold unnamedOrder at hom
  simp only [hreq, ↓reduceIte] at hom
  have hfind : chart.find? (fun m => m.active && !(valueSlots segs).any (·.2 == m.id)) = none := by
    cases hf : chart.find? (fun m => m.active && !(valueSlots segs).any (·.2 == m.id)) with
    | none => rfl
    | some x => simp [hf] at hom
  have hnot := List.find?_eq_none.mp hfind m hm
  have hany : (valueSlots segs).any (·.2 == m.id) = true := by
    simpa [ha] using hnot
  obtain ⟨⟨f, id⟩, hs, hid⟩ := List.any_eq_true.mp hany
  unfold valueSlots at hs
  rw [List.mem_filter] at hs
  have hid' : id = m.id := beq_iff_eq.mp hid
  refine ⟨f, ?_, ?_⟩
  · have hv := hs.2
    cases f <;> simp [isValueField] at hv ⊢
  · rw [← hid']
    exact mem_of_mem_slotsOf segs f id hs.1


theorem render_all_orders_named_default {chart : List MedReq} {out r : List Char}
    (h : render ({} : Policy) chart out = .ok r) :
    ∃ segs, parseTemplate out = some segs ∧
      ∀ m ∈ chart, m.active = true → ∃ f, f ≠ .drug ∧ Seg.slot f m.id ∈ segs :=
  render_all_orders_named (p := {}) rfl h

end DoseGate
