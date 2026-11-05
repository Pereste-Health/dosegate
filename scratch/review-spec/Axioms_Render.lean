import DoseGate.Spec

namespace DoseGate

theorem tokensAux_alnum (c : Char) (cs cur : List Char) (h : c.isAlphanum = true) :
    tokensAux (c :: cs) cur = tokensAux cs (c.toLower :: cur) := by
  simp [tokensAux, h]

theorem tokensAux_sep (c : Char) (cs cur : List Char) (h : c.isAlphanum = false) :
    tokensAux (c :: cs) cur = (if cur.isEmpty then [] else [cur.reverse]) ++ tokensAux cs [] := by
  simp [tokensAux, h]

theorem tokensAux_append_of_last : ∀ (a b cur : List Char),
    (a.getLast?.map isSep).getD false = true → tokensAux (a ++ b) cur = tokensAux a cur ++ tokensAux b []
  | [], _, _, h => by simp at h
  | [x], b, cur, h => by
      have hx : x.isAlphanum = false := by simpa [isSep] using h
      rw [List.cons_append, List.nil_append, tokensAux_sep x b cur hx, tokensAux_sep x [] cur hx]
      simp [tokensAux]
  | x :: y :: l, b, cur, h => by
      have h' : ((y :: l).getLast?.map isSep).getD false = true := by
        simpa [List.getLast?_cons_cons] using h
      by_cases hx : x.isAlphanum = true
      · rw [List.cons_append, tokensAux_alnum x _ cur hx, tokensAux_alnum x _ cur hx]
        exact tokensAux_append_of_last (y :: l) b (x.toLower :: cur) h'
      · have hx' : x.isAlphanum = false := by simpa using hx
        rw [List.cons_append, tokensAux_sep x _ cur hx', tokensAux_sep x _ cur hx',
          tokensAux_append_of_last (y :: l) b [] h', List.append_assoc]

theorem tokensAux_prepend_of_first (c : Char) (b' : List Char) (hc : c.isAlphanum = false) :
    ∀ (a cur : List Char), tokensAux (a ++ c :: b') cur = tokensAux a cur ++ tokensAux (c :: b') []
  | [], cur => by
      rw [List.nil_append, tokensAux_sep c b' cur hc]
      simp [tokensAux, hc]
  | x :: a', cur => by
      by_cases hx : x.isAlphanum = true
      · rw [List.cons_append, tokensAux_alnum x _ cur hx, tokensAux_alnum x _ cur hx]
        exact tokensAux_prepend_of_first c b' hc a' (x.toLower :: cur)
      · have hx' : x.isAlphanum = false := by simpa using hx
        rw [List.cons_append, tokensAux_sep x _ cur hx', tokensAux_sep x _ cur hx',
          tokensAux_prepend_of_first c b' hc a' [], List.append_assoc]

theorem tokens_append_of_separated {a b : List Char} (h : separated a b = true) :
    tokens (a ++ b) = tokens a ++ tokens b := by
  unfold separated at h
  rw [Bool.or_eq_true] at h
  unfold tokens
  rcases h with h | h
  · exact tokensAux_append_of_last a b [] h
  · cases b with
    | nil => simp at h
    | cons c b' =>
      have hc : c.isAlphanum = false := by simpa [isSep] using h
      exact tokensAux_prepend_of_first c b' hc a []

theorem separated_append_of_ne (p q r : List Char) (hq : q ≠ []) :
    separated p (q ++ r) = separated p q := by
  cases q with
  | nil => contradiction
  | cons x xs => simp [separated]

theorem tokens_flatten_chain : ∀ ps : List (List Char), sepChain ps = true →
    (∀ x ∈ ps, x ≠ []) → tokens ps.flatten = ps.flatMap tokens
  | [], _, _ => by simp [tokens, tokensAux]
  | [p], _, _ => by simp
  | p :: q :: rest, hs, hne => by
      have hsep : separated p q = true := by
        simp only [sepChain, Bool.and_eq_true] at hs
        exact hs.1
      have hrest : sepChain (q :: rest) = true := by
        simp only [sepChain, Bool.and_eq_true] at hs
        exact hs.2
      have hq : q ≠ [] := hne q (by simp)
      have ih := tokens_flatten_chain (q :: rest) hrest (fun x hx => hne x (by simp_all))
      have e1 : (q :: rest).flatten = q ++ rest.flatten := List.flatten_cons
      have e2 : (p :: q :: rest).flatten = p ++ (q :: rest).flatten := List.flatten_cons
      have hs' : separated p (q :: rest).flatten = true := by
        rw [e1, separated_append_of_ne p q _ hq]
        exact hsep
      rw [e2, tokens_append_of_separated hs', ih]
      rfl

theorem flatten_filter_nonempty (ps : List (List Char)) :
    (ps.filter (fun x => !x.isEmpty)).flatten = ps.flatten := by
  induction ps with
  | nil => simp
  | cons p ps ih =>
    by_cases hp : p.isEmpty
    · obtain rfl := List.isEmpty_iff.mp hp
      simp [ih]
    · simp [hp, ih]

theorem flatMap_tokens_filter_nonempty (ps : List (List Char)) :
    (ps.filter (fun x => !x.isEmpty)).flatMap tokens = ps.flatMap tokens := by
  induction ps with
  | nil => simp
  | cons p ps ih =>
    by_cases hp : p.isEmpty
    · obtain rfl := List.isEmpty_iff.mp hp
      simp [ih, tokens, tokensAux]
    · simp [hp, ih]

theorem tokens_flatten {ps : List (List Char)} (h : allSeparated ps = true) :
    tokens ps.flatten = ps.flatMap tokens := by
  unfold allSeparated at h
  have hne : ∀ x ∈ ps.filter (fun x => !x.isEmpty), x ≠ [] := by
    intro x hx h'
    subst h'
    simp at hx
  have := tokens_flatten_chain _ h hne
  rw [flatten_filter_nonempty, flatMap_tokens_filter_nonempty] at this
  exact this

theorem mapM_forall₂ {p : Policy} {chart : List MedReq} :
    ∀ (segs : List Seg) (pieces : List (List Char)),
      segs.mapM (renderSeg p chart) = .ok pieces →
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces
  | [], pieces, h => by
      change Except.ok [] = Except.ok pieces at h
      cases h
      exact Forall₂.nil
  | s :: ss, pieces, h => by
      rw [List.mapM_cons] at h
      cases hs : renderSeg p chart s with
      | error b =>
        simp only [hs, bind, Except.bind] at h
        cases h
      | ok x =>
        cases hm : ss.mapM (renderSeg p chart) with
        | error b =>
          simp only [hs, hm, bind, Except.bind] at h
          cases h
        | ok xs =>
          simp only [hs, hm, bind, Except.bind] at h
          cases h
          exact Forall₂.cons hs (mapM_forall₂ ss xs hm)

theorem forall₂_mem {R : Seg → List Char → Prop} : ∀ {segs : List Seg} {pieces : List (List Char)},
    Forall₂ R segs pieces → ∀ s ∈ segs, ∃ x, R s x
  | _, _, .nil, s, hs => by simp at hs
  | _, _, .cons hR hF, s, hs => by
      rcases List.mem_cons.mp hs with rfl | hs
      · exact ⟨_, hR⟩
      · exact forall₂_mem hF s hs

theorem nodup_map_eq {α β : Type} (f : α → β) : ∀ (l : List α), (l.map f).Nodup →
    ∀ a ∈ l, ∀ b ∈ l, f a = f b → a = b
  | [], _, a, ha, _, _, _ => by simp at ha
  | x :: xs, hn, a, ha, b, hb, hab => by
      rw [List.map_cons, List.nodup_cons] at hn
      rcases List.mem_cons.mp ha with hax | ha'
      · rcases List.mem_cons.mp hb with hbx | hb'
        · rw [hax, hbx]
        · subst hax
          exact absurd (by rw [hab]; exact List.mem_map_of_mem hb') hn.1
      · rcases List.mem_cons.mp hb with hbx | hb'
        · subst hbx
          exact absurd (by rw [← hab]; exact List.mem_map_of_mem ha') hn.1
        · exact nodup_map_eq f xs hn.2 a ha' b hb' hab

theorem checkText_ok {p : Policy} {t : List Char} (h : checkText p t = .ok ()) :
    t.all (·.toNat < 128) = true ∧ (tokens t).all (fun tok => !blockedToken p tok) = true := by
  unfold checkText at h
  split at h
  · simp at h
  · rename_i hall
    split at h
    · simp at h
    · rename_i hfind
      refine ⟨by simpa using hall, ?_⟩
      rw [List.all_eq_true]
      intro tok htok
      have := List.find?_eq_none.mp hfind tok htok
      simpa using this

theorem renderSeg_text {p : Policy} {chart : List MedReq} {t x : List Char}
    (h : renderSeg p chart (.text t) = .ok x) : checkText p t = .ok () ∧ x = t := by
  simp only [renderSeg] at h
  cases hc : checkText p t with
  | error b => simp only [hc, bind, Except.bind] at h; cases h
  | ok u =>
    cases u
    simp only [hc, bind, Except.bind] at h
    cases h
    exact ⟨rfl, rfl⟩

theorem text_no_blocked {p : Policy} {t : List Char}
    (h : checkText p t = .ok ()) : (tokens t).filter (blockedToken p) = [] := by
  unfold checkText at h
  split at h
  · simp at h
  · rename_i hall
    split at h
    · simp at h
    · rename_i hfind
      rw [List.filter_eq_nil_iff]
      intro tok htok
      have := List.find?_eq_none.mp hfind tok htok
      simpa using this

theorem renderSeg_slot_find {p : Policy} {chart : List MedReq} {f : Field} {id x : List Char}
    (h : renderSeg p chart (.slot f id) = .ok x) :
    ∃ m ∈ chart, m.id = id ∧ m.active = true ∧ fmtField f m = some x := by
  simp only [renderSeg] at h
  cases hfind : chart.find? (·.id == id) with
  | none => simp [hfind] at h
  | some m =>
    simp only [hfind] at h
    have hm := List.mem_of_find?_eq_some hfind
    have hid : m.id = id := by simpa using List.find?_some hfind
    cases hact : m.active with
    | false => simp [hact] at h
    | true =>
      cases hf : fmtField f m with
      | none => simp [hact, hf] at h
      | some piece =>
        simp [hact, hf] at h
        exact ⟨m, hm, hid, hact, by rw [hf, h]⟩

theorem forall₂_spec {p : Policy} {chart : List MedReq} (hn : (chart.map (·.id)).Nodup) :
    ∀ {segs : List Seg} {pieces : List (List Char)},
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces →
      Forall₂ (SegRendersTo chart) segs pieces
  | _, _, .nil => Forall₂.nil
  | s :: segs, x :: pieces, .cons hR hF => by
      refine Forall₂.cons ?_ (forall₂_spec hn hF)
      cases s with
      | text t =>
        obtain ⟨-, rfl⟩ := renderSeg_text hR
        simp [SegRendersTo]
      | slot f id =>
        obtain ⟨m, hm, hid, hact, hf⟩ := renderSeg_slot_find hR
        exact ⟨m, hm, hid, hact, hf, fun m' hm' hid' =>
          nodup_map_eq (fun m => m.id) chart hn m' hm' m hm (hid'.trans hid.symm)⟩

theorem render_dup {p : Policy} {chart : List MedReq} {out : List Char}
    (hn : ¬ (chart.map (·.id)).Nodup) : render p chart out = .error .duplicateIds := by
  unfold render
  simp only [hn]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_malformed_eq {p : Policy} {chart : List MedReq} {out : List Char}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = none) :
    render p chart out = .error .malformed := by
  unfold render
  simp only [hn, hp]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_unbound_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentenceGroups segs []).all groupBound = false) :
    render p chart out = .error .unbound := by
  unfold render
  simp only [hn, hp, hu]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_mapM_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentenceGroups segs []).all groupBound = true) (e : Block)
    (hm : segs.mapM (renderSeg p chart) = .error e) :
    render p chart out = .error e := by
  unfold render
  simp only [hn, hp, hu, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_unseparated_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentenceGroups segs []).all groupBound = true) (pieces : List (List Char))
    (hm : segs.mapM (renderSeg p chart) = .ok pieces) (hsep : ¬ allSeparated pieces = true) :
    render p chart out = .error .unseparated := by
  unfold render
  simp only [hn, hp, hu, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp [hsep] <;> rfl

theorem render_ok_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentenceGroups segs []).all groupBound = true) (pieces : List (List Char))
    (hm : segs.mapM (renderSeg p chart) = .ok pieces) (hsep : allSeparated pieces = true) :
    render p chart out = .ok pieces.flatten := by
  unfold render
  simp only [hn, hp, hu, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp [hsep] <;> rfl

theorem render_decomp {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    (chart.map (·.id)).Nodup ∧ ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces ∧
      allSeparated pieces = true ∧ r = pieces.flatten ∧
      (sentenceGroups segs []).all groupBound = true := by
  have hn : (chart.map (·.id)).Nodup := by
    by_cases hn : (chart.map (·.id)).Nodup
    · exact hn
    · rw [render_dup hn] at h
      cases h
  rcases hp : parseTemplate out with _ | segs
  · rw [render_malformed_eq hn hp] at h
    cases h
  rcases hu : (sentenceGroups segs []).all groupBound with _ | _
  · rw [render_unbound_eq hn hp hu] at h
    cases h
  rcases hm : segs.mapM (renderSeg p chart) with e | pieces
  · rw [render_mapM_eq hn hp hu e hm] at h
    cases h
  by_cases hsep : allSeparated pieces = true
  · refine ⟨hn, segs, pieces, rfl, mapM_forall₂ segs pieces hm, hsep, ?_, hu⟩
    rw [render_ok_eq hn hp hu pieces hm hsep] at h
    exact (Except.ok.inj h).symm
  · rw [render_unseparated_eq hn hp hu pieces hm hsep] at h
    cases h

theorem dose_key (p : Policy) (chart : List MedReq) : ∀ (segs : List Seg) (pieces : List (List Char)),
    Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces →
    pieces.flatMap (fun pc => (tokens pc).filter (blockedToken p)) = slotDoseTokens p segs pieces
  | _, _, .nil => by simp [slotDoseTokens]
  | s :: segs, x :: pieces, .cons hR hF => by
      have ih := dose_key p chart segs pieces hF
      unfold slotDoseTokens at ih ⊢
      cases s with
      | text t =>
        obtain ⟨hc, rfl⟩ := renderSeg_text hR
        simp [List.zip_cons_cons, Seg.isSlot, ih, text_no_blocked hc]
      | slot f id =>
        simp [List.zip_cons_cons, Seg.isSlot, ih]

theorem tokens_flatten_filter_eq {p : Policy} {pieces : List (List Char)} (hsep : allSeparated pieces = true) :
    (tokens pieces.flatten).filter (blockedToken p) = pieces.flatMap (fun pc => (tokens pc).filter (blockedToken p)) := by
  rw [tokens_flatten hsep, List.filter_flatMap]

theorem render_fidelity {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧ r = pieces.flatten := by
  obtain ⟨hn, segs, pieces, hp, hF, -, hr, -⟩ := render_decomp h
  exact ⟨segs, pieces, hp, forall₂_spec hn hF, hr⟩

theorem render_dose_tokens_from_chart {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧
      (tokens r).filter (blockedToken p) = slotDoseTokens p segs pieces := by
  obtain ⟨hn, segs, pieces, hp, hF, hsep, hr, -⟩ := render_decomp h
  refine ⟨segs, pieces, hp, forall₂_spec hn hF, ?_⟩
  rw [hr, tokens_flatten_filter_eq hsep]
  exact dose_key p chart segs pieces hF

theorem render_text_clean {p : Policy} {chart : List MedReq} {out r t : List Char} {segs : List Seg}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs) (ht : Seg.text t ∈ segs) :
    (tokens t).all (fun tok => !blockedToken p tok) = true ∧ t.all (·.toNat < 128) = true := by
  obtain ⟨-, segs', pieces, hp', hF, -, -, -⟩ := render_decomp h
  have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
  subst e
  obtain ⟨x, hx⟩ := forall₂_mem hF _ ht
  obtain ⟨hc, -⟩ := renderSeg_text hx
  exact ⟨(checkText_ok hc).2, (checkText_ok hc).1⟩

theorem render_malformed {p : Policy} {chart : List MedReq} {out : List Char}
    (h : parseTemplate out = none) : ∃ b, render p chart out = .error b := by
  by_cases hn : (chart.map (·.id)).Nodup
  · exact ⟨.malformed, render_malformed_eq hn h⟩
  · exact ⟨.duplicateIds, render_dup hn⟩

theorem render_no_active_order {p : Policy} {chart : List MedReq} {out id : List Char}
    {segs : List Seg} {f : Field}
    (hp : parseTemplate out = some segs) (hs : Seg.slot f id ∈ segs)
    (hn : ∀ m ∈ chart, m.id = id → m.active = false) :
    ∃ b, render p chart out = .error b := by
  match hr : render p chart out with
  | .error b => exact ⟨b, by first | exact hr | rfl⟩
  | .ok r =>
    exfalso
    obtain ⟨-, segs', pieces, hp', hF, -, -, -⟩ := render_decomp hr
    have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
    subst e
    obtain ⟨x, hx⟩ := forall₂_mem hF _ hs
    obtain ⟨m, hm, hid, hact, -⟩ := renderSeg_slot_find hx
    have := hn m hm hid
    simp_all

theorem render_missing_field {p : Policy} {chart : List MedReq} {out id : List Char}
    {segs : List Seg} {f : Field}
    (hp : parseTemplate out = some segs) (hs : Seg.slot f id ∈ segs)
    (hm : ∀ m ∈ chart, m.id = id → fmtField f m = none) :
    ∃ b, render p chart out = .error b := by
  match hr : render p chart out with
  | .error b => exact ⟨b, by first | exact hr | rfl⟩
  | .ok r =>
    exfalso
    obtain ⟨-, segs', pieces, hp', hF, -, -, -⟩ := render_decomp hr
    have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
    subst e
    obtain ⟨x, hx⟩ := forall₂_mem hF _ hs
    obtain ⟨m, hm', hid, -, hf⟩ := renderSeg_slot_find hx
    have := hm m hm' hid
    simp_all

theorem render_duplicate_ids {p : Policy} {chart : List MedReq} {out : List Char}
    (h : ¬ (chart.map (·.id)).Nodup) : ∃ b, render p chart out = .error b :=
  ⟨.duplicateIds, render_dup h⟩

theorem render_binding {p : Policy} {chart : List MedReq} {out r : List Char} {segs : List Seg}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs) :
    ∀ g ∈ sentenceGroups segs [], groupBound g = true := by
  obtain ⟨-, segs', pieces, hp', -, -, -, hu⟩ := render_decomp h
  have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
  subst e
  intro g hg
  exact List.all_eq_true.mp hu g hg

end DoseGate

#print axioms DoseGate.tokensAux_alnum
#print axioms DoseGate.tokensAux_sep
#print axioms DoseGate.tokensAux_append_of_last
#print axioms DoseGate.tokensAux_prepend_of_first
#print axioms DoseGate.tokens_append_of_separated
#print axioms DoseGate.separated_append_of_ne
#print axioms DoseGate.tokens_flatten_chain
#print axioms DoseGate.flatten_filter_nonempty
#print axioms DoseGate.flatMap_tokens_filter_nonempty
#print axioms DoseGate.tokens_flatten
#print axioms DoseGate.mapM_forall₂
#print axioms DoseGate.forall₂_mem
#print axioms DoseGate.nodup_map_eq
#print axioms DoseGate.checkText_ok
#print axioms DoseGate.renderSeg_text
#print axioms DoseGate.text_no_blocked
#print axioms DoseGate.renderSeg_slot_find
#print axioms DoseGate.forall₂_spec
#print axioms DoseGate.render_dup
#print axioms DoseGate.render_malformed_eq
#print axioms DoseGate.render_unbound_eq
#print axioms DoseGate.render_mapM_eq
#print axioms DoseGate.render_unseparated_eq
#print axioms DoseGate.render_ok_eq
#print axioms DoseGate.render_decomp
#print axioms DoseGate.dose_key
#print axioms DoseGate.tokens_flatten_filter_eq
#print axioms DoseGate.render_fidelity
#print axioms DoseGate.render_dose_tokens_from_chart
#print axioms DoseGate.render_text_clean
#print axioms DoseGate.render_malformed
#print axioms DoseGate.render_no_active_order
#print axioms DoseGate.render_missing_field
#print axioms DoseGate.render_duplicate_ids
#print axioms DoseGate.render_binding
