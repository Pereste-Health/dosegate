import DoseGate.Spec
import DoseGate.Proofs.Dec

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

theorem allowedWord_not_forbidden {p : Policy} {tok : List Char} (h : allowedWord p tok = true) :
    isForbidden tok = false := by
  unfold allowedWord at h
  cases hf : isForbidden tok <;> simp_all

theorem checkText_ok {p : Policy} {t : List Char} (h : checkText p t = .ok ()) :
    t.all isTextChar = true ∧ (tokens t).all (allowedWord p) = true := by
  unfold checkText at h
  split at h
  · simp at h
  · rename_i hall
    split at h
    · simp at h
    · rename_i hforb
      split at h
      · simp at h
      · rename_i hfind
        refine ⟨by simpa using hall, ?_⟩
        rw [List.all_eq_true]
        intro tok htok
        have := List.find?_eq_none.mp hfind tok htok
        simpa using this

theorem bind_text_ok {t x : List Char} : ∀ (e : Except Block Unit),
    (e >>= fun _ => (pure t : Except Block (List Char))) = .ok x → e = .ok () ∧ x = t
  | .error _, h => by cases h
  | .ok (), h => by
      change (Except.ok t : Except Block (List Char)) = .ok x at h
      cases h
      exact ⟨rfl, rfl⟩

theorem renderSeg_text {p : Policy} {chart : List MedReq} {t x : List Char}
    (hs : p.numberOnly = false) (h : renderSeg p chart (.text t) = .ok x) :
    checkText p t = .ok () ∧ x = t := by
  unfold renderSeg at h
  rw [hs] at h
  simp only [Bool.false_eq_true, ↓reduceIte] at h
  exact bind_text_ok _ h

theorem renderSeg_text_eq {p : Policy} {chart : List MedReq} {t x : List Char}
    (h : renderSeg p chart (.text t) = .ok x) : x = t := by
  unfold renderSeg at h
  exact (bind_text_ok _ h).2

theorem text_no_forbidden {p : Policy} {t : List Char}
    (h : checkText p t = .ok ()) : (tokens t).filter isForbidden = [] := by
  obtain ⟨-, hall⟩ := checkText_ok h
  rw [List.filter_eq_nil_iff]
  intro tok htok
  simp [allowedWord_not_forbidden (List.all_eq_true.mp hall tok htok)]

theorem drugName_printed {m : MedReq} {x : List Char} (h : fmtField .drug m = some x) :
    drugNameOk x = true ∧ (tokens x).all (fun tok => !isNameWord tok) = true := by
  by_cases hk : drugNameOk m.drug = true
  · have hx : m.drug = x := by simpa [fmtField, hk] using h
    subst hx
    refine ⟨hk, ?_⟩
    simp only [drugNameOk, Bool.and_eq_true, Bool.not_eq_true'] at hk
    rw [List.all_eq_true]
    intro tok htok
    have hany := hk.2
    simp only [List.any_eq_false] at hany
    simpa using hany tok htok
  · simp [fmtField, hk] at h

theorem drug_no_forbidden {m : MedReq} {x : List Char} (h : fmtField .drug m = some x) :
    (tokens x).filter isForbidden = [] := by
  by_cases hk : drugNameOk m.drug = true
  · have hx : m.drug = x := by simpa [fmtField, hk] using h
    subst hx
    simp only [drugNameOk, Bool.and_eq_true, Bool.not_eq_true'] at hk
    rw [List.filter_eq_nil_iff]
    intro tok htok
    have hany := hk.1.2
    simp only [List.any_eq_false] at hany
    simpa using hany tok htok
  · simp [fmtField, hk] at h

theorem renderSeg_slot_spec {p : Policy} {chart : List MedReq} {f : Field} {id x : List Char}
    (h : renderSeg p chart (.slot f id) = .ok x) :
    ∃ m, chart.find? (·.id == id) = some m ∧ m.active = true ∧ fmtField f m = some x := by
  simp only [renderSeg] at h
  cases hfind : chart.find? (·.id == id) with
  | none => simp [hfind] at h
  | some m =>
    simp only [hfind] at h
    cases hact : m.active with
    | false => simp [hact] at h
    | true =>
      refine ⟨m, by simp [hfind], hact, ?_⟩
      cases hf : fmtField f m with
      | none => simp [hact, hf] at h <;> split at h <;> cases h
      | some piece =>
        simp [hact, hf] at h
        split at h <;> (try split at h) <;> first | exact congrArg some (Except.ok.inj h) | cases h

theorem renderSeg_drug_number {p : Policy} {chart : List MedReq} {id x : List Char}
    (hp : p.numberOnly = true) (h : renderSeg p chart (.slot .drug id) = .ok x) :
    (tokens x).any numberLike = false := by
  obtain ⟨m, hfind, hact, hf⟩ := renderSeg_slot_spec h
  cases hc : (tokens x).any numberLike with
  | false => rfl
  | true =>
    exfalso
    unfold renderSeg at h
    simp only [hfind, hact, hf, hp, hc, Bool.not_true, Bool.and_true, beq_self_eq_true,
      ↓reduceIte] at h
    by_cases hl : (chart.filter fun m' => m'.active && relatedDrug m'.drug m.drug).length > 1
    · simp [hl] at h
    · simp [hl] at h

theorem renderSeg_slot_find {p : Policy} {chart : List MedReq} {f : Field} {id x : List Char}
    (h : renderSeg p chart (.slot f id) = .ok x) :
    ∃ m ∈ chart, m.id = id ∧ m.active = true ∧ fmtField f m = some x := by
  obtain ⟨m, hfind, hact, hf⟩ := renderSeg_slot_spec h
  exact ⟨m, List.mem_of_find?_eq_some hfind, by simpa using List.find?_some hfind, hact, hf⟩

theorem forall₂_spec {p : Policy} {chart : List MedReq} (hn : (chart.map (·.id)).Nodup) :
    ∀ {segs : List Seg} {pieces : List (List Char)},
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces →
      Forall₂ (SegRendersTo chart) segs pieces
  | _, _, .nil => Forall₂.nil
  | s :: segs, x :: pieces, .cons hR hF => by
      refine Forall₂.cons ?_ (forall₂_spec hn hF)
      cases s with
      | text t =>
        obtain rfl := renderSeg_text_eq hR
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
    (hu : (sentences segs).all (sentenceOk p) = false) :
    render p chart out = .error .unbound := by
  unfold render
  simp only [hn, hp, hu]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_repeated_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = false) :
    render p chart out = .error .repeatedValue := by
  unfold render
  simp only [hn, hp, hu, hr]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_mapM_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hs : hasSignBeforeSlot segs = false)
    (ho : unnamedOrder p chart segs = none)
    (e : Block) (hm : segs.mapM (renderSeg p chart) = .error e) :
    render p chart out = .error e := by
  unfold render
  simp only [hn, hp, hu, hr, hs, ho, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_unseparated_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hs : hasSignBeforeSlot segs = false)
    (ho : unnamedOrder p chart segs = none)
    (pieces : List (List Char))
    (hm : segs.mapM (renderSeg p chart) = .ok pieces) (hsep : ¬ allSeparated pieces = true) :
    render p chart out = .error .unseparated := by
  unfold render
  simp only [hn, hp, hu, hr, hs, ho, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp [hsep] <;> rfl

theorem render_ok_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hs : hasSignBeforeSlot segs = false)
    (hna : (p.requireAll && chart.all (!·.active)) = false) (ho : unnamedOrder p chart segs = none)
    (pieces : List (List Char))
    (hm : segs.mapM (renderSeg p chart) = .ok pieces) (hsep : allSeparated pieces = true) :
    render p chart out = .ok pieces.flatten := by
  unfold render
  simp only [hn, hp, hu, hr, hs, hna, ho, hm]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp [hsep] <;> rfl

theorem render_sign_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hsg : hasSignBeforeSlot segs = true) :
    render p chart out = .error .signBeforeSlot := by
  unfold render
  simp only [hn, hp, hu, hr, hsg]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem render_noActive_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    {pieces : List (List Char)}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hs : hasSignBeforeSlot segs = false) (ho : unnamedOrder p chart segs = none)
    (hm : segs.mapM (renderSeg p chart) = .ok pieces) (hsep : allSeparated pieces = true)
    (hb : (p.requireAll && chart.all (!·.active)) = true) :
    render p chart out = .error .noActiveOrder := by
  unfold render
  simp only [hn, hp, hu, hr, hs, ho, hm, hb]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp [hsep] <;> rfl

theorem render_unnamed_eq {p : Policy} {chart : List MedReq} {out : List Char} {segs : List Seg}
    {id : List Char}
    (hn : (chart.map (·.id)).Nodup) (hp : parseTemplate out = some segs)
    (hu : (sentences segs).all (sentenceOk p) = true) (hr : noRepeatedValue segs = true)
    (hs : hasSignBeforeSlot segs = false)
    (ho : unnamedOrder p chart segs = some id) :
    render p chart out = .error (.omittedOrder id) := by
  unfold render
  simp only [hn, hp, hu, hr, hs, ho]
  dsimp only [bind, Except.bind, pure, Except.pure, throw]
  simp <;> rfl

theorem hasSignBeforeSlot_cons {x : Seg} {L : List Seg} (h : hasSignBeforeSlot (x :: L) = false) :
    hasSignBeforeSlot L = false := by
  cases L with
  | nil => rfl
  | cons y L' =>
    cases x with
    | text t =>
      cases y with
      | text t' => simpa [hasSignBeforeSlot] using h
      | slot f id =>
        simp only [hasSignBeforeSlot, Bool.or_eq_false_iff] at h
        exact h.2
    | slot f id => simpa [hasSignBeforeSlot] using h

theorem hasSignBeforeSlot_split : ∀ (s u : List Seg) (t : List Char) (f : Field) (id : List Char),
    hasSignBeforeSlot (s ++ Seg.text t :: Seg.slot f id :: u) = false → endsSign t = false
  | [], u, t, f, id, h => by
      simp only [List.nil_append, hasSignBeforeSlot, Bool.or_eq_false_iff] at h
      exact h.1
  | x :: s, u, t, f, id, h =>
      hasSignBeforeSlot_split s u t f id (hasSignBeforeSlot_cons (x := x) (by simpa using h))

theorem render_decomp_full {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    (chart.map (·.id)).Nodup ∧ ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces ∧
      allSeparated pieces = true ∧ r = pieces.flatten ∧
      (∀ g ∈ sentences segs, sentenceOk p g = true) ∧ noRepeatedValue segs = true ∧
      hasSignBeforeSlot segs = false ∧ (p.requireAll && chart.all (!·.active)) = false ∧
      unnamedOrder p chart segs = none := by
  have hn : (chart.map (·.id)).Nodup := by
    by_cases hn : (chart.map (·.id)).Nodup
    · exact hn
    · rw [render_dup hn] at h
      cases h
  rcases hp : parseTemplate out with _ | segs
  · rw [render_malformed_eq hn hp] at h
    cases h
  cases hu : (sentences segs).all (sentenceOk p)
  · rw [render_unbound_eq hn hp hu] at h
    cases h
  cases hr : noRepeatedValue segs
  · rw [render_repeated_eq hn hp hu hr] at h
    cases h
  have hs : hasSignBeforeSlot segs = false := by
    cases hs' : hasSignBeforeSlot segs with
    | false => rfl
    | true => rw [render_sign_eq hn hp hu hr hs'] at h; cases h
  have ho : unnamedOrder p chart segs = none := by
    cases ho' : unnamedOrder p chart segs with
    | none => rfl
    | some id => rw [render_unnamed_eq hn hp hu hr hs ho'] at h; cases h
  rcases hm : segs.mapM (renderSeg p chart) with e | pieces
  · rw [render_mapM_eq hn hp hu hr hs ho e hm] at h
    cases h
  by_cases hsep : allSeparated pieces = true
  · have hna : (p.requireAll && chart.all (!·.active)) = false := by
      cases hb : (p.requireAll && chart.all (!·.active)) with
      | false => rfl
      | true => rw [render_noActive_eq hn hp hu hr hs ho hm hsep hb] at h; cases h
    have hr' := render_ok_eq hn hp hu hr hs hna ho pieces hm hsep
    rw [hr'] at h
    exact ⟨hn, segs, pieces, rfl, mapM_forall₂ segs pieces hm, hsep, (Except.ok.inj h).symm,
      List.all_eq_true.mp hu, hr, hs, hna, ho⟩
  · rw [render_unseparated_eq hn hp hu hr hs ho pieces hm hsep] at h
    cases h

theorem render_decomp {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    (chart.map (·.id)).Nodup ∧ ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces ∧
      allSeparated pieces = true ∧ r = pieces.flatten ∧
      (∀ g ∈ sentences segs, sentenceOk p g = true) ∧ noRepeatedValue segs = true := by
  obtain ⟨hn, segs, pieces, hp, hF, hsep, hr, hs, hrep, -, -, -⟩ := render_decomp_full h
  exact ⟨hn, segs, pieces, hp, hF, hsep, hr, hs, hrep⟩

theorem endsSign_parts {t : List Char} (h : endsSign t = false) :
    (t.reverse.takeWhile (fun c => !c.isAlphanum)).any (fun c => c == '-' || c == '+') = false ∧
    (t.reverse.takeWhile (fun c => !c.isAlphanum)).any (fun c => c == '/') = false := by
  unfold endsSign at h
  generalize t.reverse.takeWhile (fun c => !c.isAlphanum) = run at h ⊢
  induction run with
  | nil => simp
  | cons c cs ih =>
      simp only [List.any_cons, Bool.or_eq_false_iff] at h ih ⊢
      exact ⟨⟨h.1.1, (ih h.2).1⟩, h.1.2, (ih h.2).2⟩

theorem render_no_sign_before_slot {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧ Forall₂ (SegRendersTo chart) segs pieces ∧
      r = pieces.flatten ∧
      ∀ (s u : List Seg) (t : List Char) (f : Field) (id : List Char),
        segs = s ++ Seg.text t :: Seg.slot f id :: u →
        (t.reverse.takeWhile (fun c => !c.isAlphanum)).any (fun c => c == '-' || c == '+') = false := by
  obtain ⟨hn, segs, pieces, hp, hF, -, hr, -, -, hs, -, -⟩ := render_decomp_full h
  refine ⟨segs, pieces, hp, forall₂_spec hn hF, hr, ?_⟩
  intro s u t f id hsplit
  exact (endsSign_parts (hasSignBeforeSlot_split s u t f id (by rw [← hsplit]; exact hs))).1

theorem render_no_slash_before_slot {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧ Forall₂ (SegRendersTo chart) segs pieces ∧
      r = pieces.flatten ∧
      ∀ (s u : List Seg) (t : List Char) (f : Field) (id : List Char),
        segs = s ++ Seg.text t :: Seg.slot f id :: u →
        (t.reverse.takeWhile (fun c => !c.isAlphanum)).any (fun c => c == '/') = false := by
  obtain ⟨hn, segs, pieces, hp, hF, -, hr, -, -, hs, -, -⟩ := render_decomp_full h
  refine ⟨segs, pieces, hp, forall₂_spec hn hF, hr, ?_⟩
  intro s u t f id hsplit
  exact (endsSign_parts (hasSignBeforeSlot_split s u t f id (by rw [← hsplit]; exact hs))).2

theorem dose_key (p : Policy) (chart : List MedReq) (hs : p.numberOnly = false) :
    ∀ (segs : List Seg) (pieces : List (List Char)),
    Forall₂ (fun s x => renderSeg p chart s = .ok x) segs pieces →
    pieces.flatMap (fun pc => (tokens pc).filter isForbidden) = valueSlotTokens segs pieces
  | _, _, .nil => by simp [valueSlotTokens]
  | s :: segs, x :: pieces, .cons hR hF => by
      have ih := dose_key p chart hs segs pieces hF
      unfold valueSlotTokens at ih ⊢
      cases s with
      | text t =>
        obtain ⟨hc, rfl⟩ := renderSeg_text hs hR
        simp [List.zip_cons_cons, Seg.isValueSlot, ih, text_no_forbidden hc]
      | slot f id =>
        by_cases hd : f = .drug
        · subst hd
          obtain ⟨m, -, -, -, hf⟩ := renderSeg_slot_find hR
          simp [List.zip_cons_cons, Seg.isValueSlot, ih, drug_no_forbidden hf]
        · have hv : (Seg.slot f id).isValueSlot = true := by
            cases f <;> simp_all [Seg.isValueSlot]
          simp [List.zip_cons_cons, hv, ih]

theorem tokens_flatten_filter_eq {pieces : List (List Char)} (hsep : allSeparated pieces = true) :
    (tokens pieces.flatten).filter isForbidden = pieces.flatMap (fun pc => (tokens pc).filter isForbidden) := by
  rw [tokens_flatten hsep, List.filter_flatMap]

theorem render_fidelity {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧ r = pieces.flatten := by
  obtain ⟨hn, segs, pieces, hp, hF, -, hr, -, -⟩ := render_decomp h
  exact ⟨segs, pieces, hp, forall₂_spec hn hF, hr⟩

theorem render_forbidden_tokens_from_value_slots {p : Policy} {chart : List MedReq} {out r : List Char}
    (hs : p.numberOnly = false) (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧
      (tokens r).filter isForbidden = valueSlotTokens segs pieces := by
  obtain ⟨hn, segs, pieces, hp, hF, hsep, hr, -, -⟩ := render_decomp h
  refine ⟨segs, pieces, hp, forall₂_spec hn hF, ?_⟩
  rw [hr, tokens_flatten_filter_eq hsep]
  exact dose_key p chart hs segs pieces hF

theorem render_text_clean {p : Policy} {chart : List MedReq} {out r t : List Char} {segs : List Seg}
    (hs : p.numberOnly = false) (h : render p chart out = .ok r) (hp : parseTemplate out = some segs)
    (ht : Seg.text t ∈ segs) :
    (tokens t).all (allowedWord p) = true ∧ (tokens t).all (fun tok => !isForbidden tok) = true ∧
      t.all isTextChar = true := by
  obtain ⟨-, segs', pieces, hp', hF, -, -, -, -⟩ := render_decomp h
  have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
  subst e
  obtain ⟨x, hx⟩ := forall₂_mem hF _ ht
  obtain ⟨hc, -⟩ := renderSeg_text hs hx
  obtain ⟨hchar, hallowed⟩ := checkText_ok hc
  refine ⟨hallowed, List.all_eq_true.mpr fun tok htok => ?_, hchar⟩
  simp [allowedWord_not_forbidden (p := p) (List.all_eq_true.mp hallowed tok htok)]

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
    obtain ⟨-, segs', pieces, hp', hF, -, -, -, -⟩ := render_decomp hr
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
    obtain ⟨-, segs', pieces, hp', hF, -, -, -, -⟩ := render_decomp hr
    have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
    subst e
    obtain ⟨x, hx⟩ := forall₂_mem hF _ hs
    obtain ⟨m, hm', hid, -, hf⟩ := renderSeg_slot_find hx
    have := hm m hm' hid
    simp_all

theorem render_duplicate_ids {p : Policy} {chart : List MedReq} {out : List Char}
    (h : ¬ (chart.map (·.id)).Nodup) : ∃ b, render p chart out = .error b :=
  ⟨.duplicateIds, render_dup h⟩

theorem isSentenceEnd_nonalnum {c : Char} (h : isSentenceEnd c = true) : c.isAlphanum = false := by
  unfold isSentenceEnd at h
  simp only [Bool.or_eq_true, beq_iff_eq] at h
  rcases h with ((((rfl | rfl) | rfl) | rfl) | rfl) | rfl <;> decide

theorem splitEnds_cons (c : Char) (cs : List Char) :
    splitEnds (c :: cs) = if isSentenceEnd c then [] :: splitEnds cs else
      match splitEnds cs with
      | q :: qs => (c :: q) :: qs
      | [] => [[c]] := by
  unfold splitEnds
  rw [List.foldr_cons]
  rfl

theorem splitEnds_exists : ∀ t : List Char, ∃ q qs, splitEnds t = q :: qs
  | [] => ⟨[], [], rfl⟩
  | c :: cs => by
      rw [splitEnds_cons]
      split
      · exact ⟨[], _, rfl⟩
      · obtain ⟨q, qs, h⟩ := splitEnds_exists cs
        rw [h]
        exact ⟨c :: q, qs, rfl⟩

theorem splitEnds_tokensAux : ∀ (t cur q : List Char) (qs : List (List Char)),
    splitEnds t = q :: qs → tokensAux t cur = tokensAux q cur ++ qs.flatMap tokens
  | [], cur, q, qs, h => by
      simp [splitEnds] at h
      obtain ⟨rfl, rfl⟩ := h
      simp [tokensAux]
  | c :: cs, cur, q, qs, h => by
      obtain ⟨q', qs', hs⟩ := splitEnds_exists cs
      rw [splitEnds_cons, hs] at h
      by_cases hc : isSentenceEnd c = true
      · simp only [hc, ↓reduceIte, List.cons.injEq] at h
        obtain ⟨rfl, rfl⟩ := h
        rw [tokensAux_sep c cs cur (isSentenceEnd_nonalnum hc), splitEnds_tokensAux cs [] _ _ hs]
        simp [tokensAux, tokens]
      · simp only [hc] at h
        obtain ⟨rfl, rfl⟩ := h
        by_cases ha : c.isAlphanum = true
        · rw [tokensAux_alnum c cs cur ha, tokensAux_alnum c q' cur ha]
          exact splitEnds_tokensAux cs (c.toLower :: cur) _ _ hs
        · have ha' : c.isAlphanum = false := by simpa using ha
          rw [tokensAux_sep c cs cur ha', tokensAux_sep c q' cur ha',
            splitEnds_tokensAux cs [] _ _ hs, List.append_assoc]

theorem splitEnds_flatMap {t q : List Char} {qs : List (List Char)} (h : splitEnds t = q :: qs) :
    (q :: qs).flatMap tokens = tokens t := by
  have e := splitEnds_tokensAux t [] q qs h
  rw [List.flatMap_cons]
  show tokens q ++ qs.flatMap tokens = tokensAux t []
  rw [e]
  rfl

theorem tokens_split_last (q : List Char) (qs : List (List Char)) (h : qs ≠ []) (t : List Char)
    (ht : splitEnds t = q :: qs) :
    tokens q ++ qs.dropLast.flatMap tokens ++ tokens (qs.getLast?.getD []) = tokens t := by
  have hw := splitEnds_flatMap ht
  have hd := congrArg (fun l => l.flatMap tokens) (List.dropLast_concat_getLast h)
  have hl : qs.getLast?.getD [] = qs.getLast h := by
    rw [List.getLast?_eq_some_getLast h]
    rfl
  simp only [List.flatMap_append, List.flatMap_singleton] at hd
  rw [hl, ← hw, List.flatMap_cons, ← hd, List.append_assoc]

theorem wordsOf_text_map : ∀ L : List (List Char),
    (L.map fun r => [Seg.text r]).flatMap wordsOf = L.flatMap tokens
  | [] => rfl
  | r :: L => by simp [wordsOf, wordsOf_text_map L]

theorem sentencesAux_words : ∀ (segs cur : List Seg),
    (sentencesAux segs cur).flatMap wordsOf = wordsOf cur ++ wordsOf segs
  | [], cur => by simp [sentencesAux, wordsOf]
  | .slot f id :: rest, cur => by
      simp only [sentencesAux]
      rw [sentencesAux_words rest]
      simp [wordsOf]
  | .text t :: rest, cur => by
      obtain ⟨q, qs, hs⟩ := splitEnds_exists t
      cases qs with
      | nil =>
          have e : sentencesAux (.text t :: rest) cur = sentencesAux rest (cur ++ [Seg.text q]) := by
            simp [sentencesAux, hs]
          have ht : tokens q = tokens t := by simpa using splitEnds_flatMap hs
          rw [e, sentencesAux_words rest (cur ++ [Seg.text q])]
          simp [wordsOf, ht]
      | cons q2 qs2 =>
          have hne : q2 :: qs2 ≠ [] := by simp
          have hk := tokens_split_last q (q2 :: qs2) hne t hs
          have e : sentencesAux (.text t :: rest) cur =
              (cur ++ [Seg.text q]) :: (((q2 :: qs2).dropLast).map fun r => [Seg.text r]) ++
                sentencesAux rest [Seg.text ((q2 :: qs2).getLast?.getD [])] := by
            simp [sentencesAux, hs]
          rw [e, List.flatMap_append, List.flatMap_cons, wordsOf_text_map,
            sentencesAux_words rest]
          simp only [wordsOf, List.flatMap_append, List.flatMap_cons, List.flatMap_nil,
            List.append_nil]
          rw [← hk]
          simp [List.append_assoc]

theorem sentences_words (segs : List Seg) : (sentences segs).flatMap wordsOf = wordsOf segs := by
  unfold sentences
  rw [sentencesAux_words segs []]
  simp [wordsOf]

theorem render_sentences {p : Policy} {chart : List MedReq} {out r : List Char} {segs : List Seg}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs) :
    (∀ g ∈ sentences segs, sentenceOk p g = true) ∧ noRepeatedValue segs = true := by
  obtain ⟨-, segs', pieces, hp', -, -, -, hs, hr⟩ := render_decomp h
  have e : segs' = segs := Option.some.inj (hp'.symm.trans hp)
  subst e
  exact ⟨hs, hr⟩

theorem renderSeg_unknownRef {p : Policy} {chart : List MedReq} {f : Field} {id : List Char}
    (h : ∀ m ∈ chart, m.id ≠ id) : renderSeg p chart (.slot f id) = .error (.unknownRef id) := by
  have hf : chart.find? (·.id == id) = none := by
    rw [List.find?_eq_none]
    intro m hm
    simpa using h m hm
  simp [renderSeg, hf]

theorem renderSeg_inactive {p : Policy} {chart : List MedReq} {f : Field} {id : List Char} {m : MedReq}
    (hf : chart.find? (·.id == id) = some m) (ha : m.active = false) :
    renderSeg p chart (.slot f id) = .error (.inactiveOrder id) := by
  simp [renderSeg, hf, ha]

theorem renderSeg_missing {p : Policy} {chart : List MedReq} {f : Field} {id : List Char} {m : MedReq}
    (hf : chart.find? (·.id == id) = some m) (ha : m.active = true) (hm : fmtField f m = none)
    (hd : (chart.filter fun m' => m'.active && relatedDrug m'.drug m.drug).length ≤ 1) :
    renderSeg p chart (.slot f id) = .error (.missingField id f) := by
  have hn : ¬ ((chart.filter fun m' => m'.active && relatedDrug m'.drug m.drug).length > 1) := by omega
  simp [renderSeg, hf, ha, hm, hn]

theorem dose_piece_readback {chart : List MedReq} {id piece : List Char}
    (h : SegRendersTo chart (.slot .dose id) piece) :
    ∃ m ∈ chart, ∃ d, m.id = id ∧ m.active = true ∧ m.dose = some d ∧
      (∃ one, piece = fmtDec d.amount ++ ' ' :: d.unit.name one) ∧
      parseDec? (fmtDec d.amount) = some d.amount.normalize := by
  obtain ⟨m, hm, hid, hact, hf, -⟩ := h
  cases hd : m.dose with
  | none => simp [fmtField, hd] at hf
  | some d =>
      simp [fmtField, hd] at hf
      exact ⟨m, hm, d, hid, hact, hd, ⟨_, hf.symm⟩, parseDec_fmtDec d.amount⟩

theorem eq_of_mem_of_length_le_one {α : Type} : ∀ {l : List α}, l.length ≤ 1 →
    ∀ {a b : α}, a ∈ l → b ∈ l → a = b
  | [], _, _, _, ha, _ => by simp at ha
  | [x], _, _, _, ha, hb => by simp_all
  | _ :: _ :: _, hl, _, _, _, _ => by simp at hl

theorem relatedDrug_self (a : List Char) : relatedDrug a a = true := by
  simp [relatedDrug]

theorem two_le_filter {α : Type} (P : α → Bool) : ∀ (l : List α) {a b : α}, a ∈ l → b ∈ l →
    a ≠ b → P a = true → P b = true → 2 ≤ (l.filter P).length
  | [], _, _, ha, _, _, _, _ => by simp at ha
  | x :: xs, a, b, ha, hb, hab, hPa, hPb => by
      rw [List.filter_cons]
      by_cases hx : P x = true
      · rw [if_pos hx, List.length_cons]
        have hy : ∃ y ∈ xs, P y = true := by
          rcases List.mem_cons.mp ha with rfl | ha'
          · rcases List.mem_cons.mp hb with rfl | hb'
            · exact absurd rfl hab
            · exact ⟨b, hb', hPb⟩
          · exact ⟨a, ha', hPa⟩
        obtain ⟨y, hy1, hy2⟩ := hy
        have := List.length_pos_of_mem (List.mem_filter.mpr ⟨hy1, hy2⟩)
        omega
      · rw [if_neg hx]
        have ha' : a ∈ xs := by
          rcases List.mem_cons.mp ha with rfl | ha'
          · exact absurd hPa hx
          · exact ha'
        have hb' : b ∈ xs := by
          rcases List.mem_cons.mp hb with rfl | hb'
          · exact absurd hPb hx
          · exact hb'
        exact two_le_filter P xs ha' hb' hab hPa hPb

theorem renderSeg_related_len {p : Policy} {chart : List MedReq} {f : Field} {id piece : List Char}
    {m : MedReq} (h : renderSeg p chart (.slot f id) = .ok piece)
    (hfind : chart.find? (·.id == id) = some m) (hact : m.active = true) :
    (chart.filter fun m' => m'.active && relatedDrug m'.drug m.drug).length ≤ 1 := by
  simp only [renderSeg, hfind, hact] at h
  split at h
  · cases h
  · split at h
    · cases h
    · split at h <;> first | cases h | omega

theorem renderSeg_unique_related {p : Policy} {chart : List MedReq} {f : Field} {id piece : List Char}
    (h : renderSeg p chart (.slot f id) = .ok piece) :
    ∃ m ∈ chart, m.id = id ∧ m.active = true ∧ fmtField f m = some piece ∧
      ∀ m' ∈ chart, m'.active = true → relatedDrug m'.drug m.drug = true → m' = m := by
  obtain ⟨m, hfind, hact, hf⟩ := renderSeg_slot_spec h
  have hm := List.mem_of_find?_eq_some hfind
  have hid : m.id = id := by simpa using List.find?_some hfind
  have hlen := renderSeg_related_len h hfind hact
  refine ⟨m, hm, hid, hact, hf, fun m' hm' ha' hd' => ?_⟩
  exact eq_of_mem_of_length_le_one hlen
    (List.mem_filter.mpr ⟨hm', by simp [ha', hd']⟩)
    (List.mem_filter.mpr ⟨hm, by simp [hact, relatedDrug_self]⟩)

theorem renderSeg_related_blocked {p : Policy} {chart : List MedReq} {f : Field} {id : List Char}
    {m m' : MedReq} (hf : chart.find? (·.id == id) = some m) (ha : m.active = true)
    (hm' : m' ∈ chart) (ha' : m'.active = true) (hr : relatedDrug m'.drug m.drug = true)
    (hne : m' ≠ m) :
    renderSeg p chart (.slot f id) = .error (.ambiguousDrug id) := by
  have hm := List.mem_of_find?_eq_some hf
  have h2 := two_le_filter (fun m'' => m''.active && relatedDrug m''.drug m.drug) chart hm' hm hne
    (by simp [ha', hr]) (by simp [ha, relatedDrug_self])
  have hgt : (chart.filter fun m'' => m''.active && relatedDrug m''.drug m.drug).length > 1 := by
    omega
  simp [renderSeg, hf, ha, hgt]

theorem render_no_active_default {p : Policy} {chart : List MedReq} {out : List Char}
    (hreq : p.requireAll = true) (hall : ∀ m ∈ chart, m.active = false) :
    ∃ b, render p chart out = .error b := by
  match hr : render p chart out with
  | .error b => exact ⟨b, by first | exact hr | rfl⟩
  | .ok r =>
    exfalso
    obtain ⟨-, -, -, -, -, -, -, -, -, -, hna, -⟩ := render_decomp_full hr
    have hall' : chart.all (!·.active) = true := List.all_eq_true.mpr fun m hm => by simp [hall m hm]
    simp [hreq, hall'] at hna

def liveChart : List MedReq :=
  [{ id := "m1".toList, active := true, drug := "aspirin".toList,
     dose := some { amount := { mant := 81, scale := 0 }, unit := .mg },
     timing := some { frequency := 1, period := 1, periodUnit := .d },
     route := some .oral, asNeeded := false }]

theorem render_one_active_ok :
    render ({} : Policy) liveChart "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}.".toList =
      .ok "Take aspirin 81 mg by mouth once a day.".toList := by
  have hn : (liveChart.map (·.id)).Nodup := by decide
  have hp : parseTemplate "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}.".toList =
      some [.text "Take ".toList, .slot .drug "m1".toList, .text " ".toList,
        .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList, .text " ".toList,
        .slot .frequency "m1".toList, .text ".".toList] := by decide
  have hu : (sentences [.text "Take ".toList, .slot .drug "m1".toList, .text " ".toList,
      .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList, .text " ".toList,
      .slot .frequency "m1".toList, .text ".".toList]).all (sentenceOk ({} : Policy)) = true := by decide
  have hr : noRepeatedValue [.text "Take ".toList, .slot .drug "m1".toList, .text " ".toList,
      .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList, .text " ".toList,
      .slot .frequency "m1".toList, .text ".".toList] = true := by decide
  have hs : hasSignBeforeSlot [.text "Take ".toList, .slot .drug "m1".toList, .text " ".toList,
      .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList, .text " ".toList,
      .slot .frequency "m1".toList, .text ".".toList] = false := by decide
  have hna : (({} : Policy).requireAll && liveChart.all (!·.active)) = false := by decide
  have ho : unnamedOrder ({} : Policy) liveChart [.text "Take ".toList, .slot .drug "m1".toList,
      .text " ".toList, .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList,
      .text " ".toList, .slot .frequency "m1".toList, .text ".".toList] = none := by decide
  have hnorm : Dec.normalize ⟨81, 0⟩ = ⟨81, 0⟩ := by simp [Dec.normalize]
  have t1 : renderSeg ({} : Policy) liveChart (.text "Take ".toList) = .ok "Take ".toList := by rfl
  have t2 : renderSeg ({} : Policy) liveChart (.text " ".toList) = .ok " ".toList := by rfl
  have t3 : renderSeg ({} : Policy) liveChart (.text ".".toList) = .ok ".".toList := by rfl
  have s1 : renderSeg ({} : Policy) liveChart (.slot .drug "m1".toList) = .ok "aspirin".toList := by rfl
  have s2 : renderSeg ({} : Policy) liveChart (.slot .route "m1".toList) = .ok "by mouth".toList := by rfl
  have s3 : renderSeg ({} : Policy) liveChart (.slot .frequency "m1".toList) = .ok "once a day".toList := by rfl
  have s4 : renderSeg ({} : Policy) liveChart (.slot .dose "m1".toList) = .ok "81 mg".toList := by
    simp +decide [renderSeg, liveChart, fmtField, fmtDose, fmtDec, hnorm, digitsOf, digitChar, DoseUnit.name]
  have hm : [.text "Take ".toList, .slot .drug "m1".toList, .text " ".toList,
      .slot .dose "m1".toList, .text " ".toList, .slot .route "m1".toList, .text " ".toList,
      .slot .frequency "m1".toList, .text ".".toList].mapM (renderSeg ({} : Policy) liveChart) =
      .ok ["Take ".toList, "aspirin".toList, " ".toList, "81 mg".toList, " ".toList,
        "by mouth".toList, " ".toList, "once a day".toList, ".".toList] := by
    simp only [List.mapM_cons, List.mapM_nil, t1, t2, t3, s1, s2, s3, s4, bind, Except.bind, pure,
      Except.pure, Functor.map, Except.map]
  have hsep : allSeparated ["Take ".toList, "aspirin".toList, " ".toList, "81 mg".toList, " ".toList,
      "by mouth".toList, " ".toList, "once a day".toList, ".".toList] = true := by decide
  rw [render_ok_eq hn hp hu hr hs hna ho _ hm hsep]
  rfl

end DoseGate
