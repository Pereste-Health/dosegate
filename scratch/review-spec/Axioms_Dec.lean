import DoseGate.Dec

namespace DoseGate

open Dec

def digVal (l : List Nat) : Nat := l.foldl (fun a k => a * 10 + k) 0

def padDigits (m s : Nat) : List Nat :=
  List.replicate (s + 1 - (digitsOf m).length) 0 ++ digitsOf m

theorem eqv_refl' (a : Dec) : Dec.Eqv a a := by
  unfold Dec.Eqv
  rfl

theorem eqv_symm' {a b : Dec} (h : Dec.Eqv a b) : Dec.Eqv b a := by
  unfold Dec.Eqv at *
  exact h.symm

theorem eqv_trans' {a b c : Dec} (h1 : Dec.Eqv a b) (h2 : Dec.Eqv b c) : Dec.Eqv a c := by
  unfold Dec.Eqv at *
  apply Nat.eq_of_mul_eq_mul_right (Nat.pow_pos (show 0 < 10 by decide) : 0 < 10 ^ b.scale)
  grind

theorem normalize_normal (n : Dec) (h : n.IsNormal) : n.normalize = n := by
  obtain ⟨m, s⟩ := n
  cases s with
  | zero => rw [Dec.normalize.eq_1]
  | succ s =>
    have hm : m % 10 ≠ 0 := by simpa [IsNormal] using h
    rw [Dec.normalize.eq_2, if_neg hm]

theorem eqv_step (m s : Nat) (h : m % 10 = 0) : Dec.Eqv ⟨m, s + 1⟩ ⟨m / 10, s⟩ := by
  show m * 10 ^ s = m / 10 * 10 ^ (s + 1)
  have hm : m = 10 * (m / 10) := by omega
  generalize m / 10 = q at hm ⊢
  subst hm
  rw [Nat.pow_succ]
  grind

theorem normalize_aux (s m : Nat) :
    Dec.Eqv ⟨m, s⟩ (Dec.normalize ⟨m, s⟩) ∧ IsNormal (Dec.normalize ⟨m, s⟩) := by
  induction s generalizing m with
  | zero =>
    rw [Dec.normalize.eq_1]
    exact ⟨eqv_refl' _, Or.inl rfl⟩
  | succ s ih =>
    by_cases h : m % 10 = 0
    · rw [Dec.normalize.eq_2, if_pos h]
      obtain ⟨ih1, ih2⟩ := ih (m / 10)
      exact ⟨eqv_trans' (eqv_step m s h) ih1, ih2⟩
    · rw [Dec.normalize.eq_2, if_neg h]
      exact ⟨eqv_refl' _, Or.inr h⟩

theorem normalize_eqv (d : Dec) : Dec.Eqv d d.normalize := by
  obtain ⟨m, s⟩ := d
  exact (normalize_aux s m).1

theorem normalize_isNormal (d : Dec) : d.normalize.IsNormal := by
  obtain ⟨m, s⟩ := d
  exact (normalize_aux s m).2

theorem eqv_normal_eq (a b : Dec) (h : Dec.Eqv a b) (ha : a.IsNormal) (hb : b.IsNormal) : a = b := by
  obtain ⟨am, as⟩ := a
  obtain ⟨bm, bs⟩ := b
  unfold Dec.Eqv at h
  simp only at h
  simp only [IsNormal] at ha hb
  rcases Nat.lt_trichotomy as bs with hlt | heq | hgt
  · exfalso
    obtain ⟨k, hk⟩ : ∃ k, bs = as + k + 1 := ⟨bs - as - 1, by omega⟩
    subst hk
    have hb' : bm = am * 10 ^ k * 10 := by
      apply Nat.eq_of_mul_eq_mul_left (Nat.pow_pos (show 0 < 10 by decide) : 0 < 10 ^ as)
      rw [Nat.pow_add, Nat.pow_succ] at h
      grind
    have hmod : bm % 10 = 0 := by rw [hb']; omega
    rcases hb with hb | hb
    · omega
    · exact hb hmod
  · subst heq
    have : am = bm := Nat.eq_of_mul_eq_mul_right (Nat.pow_pos (show 0 < 10 by decide) : 0 < 10 ^ as) h
    subst this
    rfl
  · exfalso
    obtain ⟨k, hk⟩ : ∃ k, as = bs + k + 1 := ⟨as - bs - 1, by omega⟩
    subst hk
    have ha' : am = bm * 10 ^ k * 10 := by
      apply Nat.eq_of_mul_eq_mul_left (Nat.pow_pos (show 0 < 10 by decide) : 0 < 10 ^ bs)
      rw [Nat.pow_add, Nat.pow_succ] at h
      grind
    have hmod : am % 10 = 0 := by rw [ha']; omega
    rcases ha with ha | ha
    · omega
    · exact ha hmod

theorem normalize_eq_of_eqv {a b : Dec} (h : Dec.Eqv a b) : a.normalize = b.normalize :=
  eqv_normal_eq _ _
    (eqv_trans' (eqv_symm' (normalize_eqv a)) (eqv_trans' h (normalize_eqv b)))
    (normalize_isNormal a) (normalize_isNormal b)

theorem normalize_idem (d : Dec) : d.normalize.normalize = d.normalize :=
  normalize_normal _ (normalize_isNormal d)

theorem fmtDec_normalize (d : Dec) : fmtDec d.normalize = fmtDec d := by
  simp only [fmtDec, normalize_idem]

theorem fold_acc (l : List Nat) (a : Nat) :
    l.foldl (fun a k => a * 10 + k) a = a * 10 ^ l.length + l.foldl (fun a k => a * 10 + k) 0 := by
  induction l generalizing a with
  | nil => simp
  | cons k l ih =>
    rw [List.foldl_cons, List.foldl_cons, Nat.zero_mul, Nat.zero_add, ih (a * 10 + k), ih k,
      List.length_cons, Nat.pow_succ]
    grind

theorem digVal_cons (k : Nat) (l : List Nat) :
    digVal (k :: l) = k * 10 ^ l.length + digVal l := by
  unfold digVal
  rw [List.foldl_cons, Nat.zero_mul, Nat.zero_add]
  exact fold_acc l k

theorem digVal_nil : digVal [] = 0 := rfl

theorem digVal_append (l1 l2 : List Nat) :
    digVal (l1 ++ l2) = digVal l1 * 10 ^ l2.length + digVal l2 := by
  unfold digVal
  rw [List.foldl_append]
  exact fold_acc _ _

theorem digVal_replicate_zero (z : Nat) : digVal (List.replicate z 0) = 0 := by
  induction z with
  | zero => rfl
  | succ z ih => rw [List.replicate_succ, digVal_cons, ih]; simp

theorem digitsOf_succ_eq (n : Nat) (h : ¬ n < 10) : digitsOf n = digitsOf (n / 10) ++ [n % 10] := by
  rw [digitsOf, if_neg h]

theorem digitsOf_small (n : Nat) (h : n < 10) : digitsOf n = [n] := by
  rw [digitsOf, if_pos h]

theorem digitsOf_props (n : Nat) :
    (∀ k ∈ digitsOf n, k < 10) ∧ digVal (digitsOf n) = n ∧ digitsOf n ≠ [] ∧
      (digitsOf n).getLast? = some (n % 10) := by
  induction n using Nat.strongRecOn with
  | _ n ih =>
    by_cases h : n < 10
    · rw [digitsOf_small n h]
      refine ⟨?_, ?_, ?_, ?_⟩
      · intro k hk
        simp at hk
        omega
      · simp [digVal, Nat.mod_eq_of_lt h]
      · simp
      · simp [Nat.mod_eq_of_lt h]
    · obtain ⟨h1, h2, h3, h4⟩ := ih (n / 10) (by omega)
      rw [digitsOf_succ_eq n h]
      refine ⟨?_, ?_, ?_, ?_⟩
      · intro k hk
        rcases List.mem_append.1 hk with hk | hk
        · exact h1 k hk
        · simp at hk
          omega
      · rw [digVal_append, h2]
        simp [digVal]
        omega
      · simp
      · simp

theorem digitChar_facts : ∀ k, k < 10 →
    (digitChar k).isDigit = true ∧ charDigit? (digitChar k) = some k ∧ digitChar k ≠ '.' := by
  decide

theorem digitChar_inj : ∀ a, a < 10 → ∀ b, b < 10 → digitChar a = digitChar b → a = b := by
  decide

theorem digitChar_zero : digitChar 0 = '0' := by decide

theorem foldlM_digits (l : List Nat) (a : Nat) (hl : ∀ k ∈ l, k < 10) :
    (l.map digitChar).foldlM (fun acc c => (charDigit? c).map (fun k => acc * 10 + k)) a
      = some (l.foldl (fun a k => a * 10 + k) a) := by
  induction l generalizing a with
  | nil => simp
  | cons k l ih =>
    have hk := hl k (by simp)
    have hl' : ∀ j ∈ l, j < 10 := fun j hj => hl j (by simp [hj])
    rw [List.map_cons, List.foldlM_cons, (digitChar_facts k hk).2.1, Option.map_some]
    exact ih (a * 10 + k) hl'

theorem readNat_digits (l : List Nat) (hl : ∀ k ∈ l, k < 10) (hne : l ≠ []) :
    readNat? (l.map digitChar) = some (digVal l) := by
  obtain ⟨k, t, rfl⟩ := List.exists_cons_of_ne_nil hne
  unfold readNat?
  rw [if_neg (by simp), foldlM_digits _ 0 hl]
  rfl

theorem span_loop_nodot : ∀ (l acc : List Char), (∀ c ∈ l, c ≠ '.') →
    List.span.loop (· != '.') l acc = (acc.reverse ++ l, [])
  | [], acc, _ => by simp [List.span.loop]
  | a :: l, acc, h => by
    have ha := h a (by simp)
    have hl : ∀ c ∈ l, c ≠ '.' := fun c hc => h c (by simp [hc])
    have ha' : (a != '.') = true := by simpa using ha
    simp [List.span.loop, ha', span_loop_nodot l (a :: acc) hl]

theorem span_loop_dot : ∀ (l r acc : List Char), (∀ c ∈ l, c ≠ '.') →
    List.span.loop (· != '.') (l ++ '.' :: r) acc = (acc.reverse ++ l, '.' :: r)
  | [], r, acc, _ => by simp [List.span.loop]
  | a :: l, r, acc, h => by
    have ha := h a (by simp)
    have hl : ∀ c ∈ l, c ≠ '.' := fun c hc => h c (by simp [hc])
    have ha' : (a != '.') = true := by simpa using ha
    simp [List.span.loop, ha', span_loop_dot l r (a :: acc) hl]

theorem span_nodot (l : List Char) (h : ∀ c ∈ l, c ≠ '.') : l.span (· != '.') = (l, []) := by
  unfold List.span
  simpa using span_loop_nodot l [] h

theorem span_dot (l r : List Char) (h : ∀ c ∈ l, c ≠ '.') :
    (l ++ '.' :: r).span (· != '.') = (l, '.' :: r) := by
  unfold List.span
  simpa using span_loop_dot l r [] h

theorem dc_mem (Q : List Nat) (hd : ∀ k ∈ Q, k < 10) (c : Char) (hc : c ∈ Q.map digitChar) :
    c.isDigit = true ∧ c ≠ '.' := by
  obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hc
  exact ⟨(digitChar_facts x (hd x hx)).1, (digitChar_facts x (hd x hx)).2.2⟩

theorem padDigits_props (m s : Nat) :
    (∀ k ∈ padDigits m s, k < 10) ∧ digVal (padDigits m s) = m ∧
      s + 1 ≤ (padDigits m s).length ∧
      (digitsOf m ≠ [] → (padDigits m s).getLast? = some (m % 10)) := by
  obtain ⟨h1, h2, h3, h4⟩ := digitsOf_props m
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro k hk
    rcases List.mem_append.1 hk with hk | hk
    · rw [List.eq_of_mem_replicate hk]
      decide
    · exact h1 k hk
  · unfold padDigits
    rw [digVal_append, digVal_replicate_zero, h2]
    simp
  · unfold padDigits
    simp only [List.length_append, List.length_replicate]
    omega
  · intro hne
    unfold padDigits
    rw [List.getLast?_append]
    simp [h4]

theorem padDigits_zero (m : Nat) (h : digitsOf m ≠ []) : padDigits m 0 = digitsOf m := by
  unfold padDigits
  have hL : 1 ≤ (digitsOf m).length := by
    rcases hh : digitsOf m with _ | ⟨a, t⟩
    · exact absurd hh h
    · simp
  rw [show 0 + 1 - (digitsOf m).length = 0 by omega, List.replicate_zero, List.nil_append]

theorem parse_core (Q : List Nat) (s m : Nat) (hd : ∀ k ∈ Q, k < 10) (hv : digVal Q = m)
    (hlen : s + 1 ≤ Q.length) (hs : 1 ≤ s) :
    parseDec? ((Q.map digitChar).take (Q.length - s) ++ '.' ::
      (Q.map digitChar).drop (Q.length - s)) = some ⟨m, s⟩ := by
  have hlt : ∀ c ∈ (Q.take (Q.length - s)).map digitChar, c ≠ '.' :=
    fun c hc => (dc_mem _ (fun k hk => hd k (List.mem_of_mem_take hk)) c hc).2
  have hne1 : Q.take (Q.length - s) ≠ [] := by
    intro h
    rcases List.take_eq_nil_iff.1 h with h | h
    · omega
    · rw [h] at hlen
      simp at hlen
  have hne2 : Q.drop (Q.length - s) ≠ [] := by
    intro h
    have := congrArg List.length h
    simp only [List.length_drop, List.length_nil] at this
    omega
  have hlen2 : (Q.drop (Q.length - s)).length = s := by
    simp only [List.length_drop]
    omega
  have hsum := digVal_append (Q.take (Q.length - s)) (Q.drop (Q.length - s))
  rw [List.take_append_drop, hlen2, hv] at hsum
  rw [← List.map_take, ← List.map_drop]
  unfold parseDec?
  rw [span_dot _ _ hlt]
  dsimp only
  rw [readNat_digits _ (fun k hk => hd k (List.mem_of_mem_take hk)) hne1,
    readNat_digits _ (fun k hk => hd k (List.mem_of_mem_drop hk)) hne2]
  simp only [List.length_map, hlen2]
  rw [hsum]
  rfl

theorem parse_nodot (Q : List Nat) (hd : ∀ k ∈ Q, k < 10) (hne : Q ≠ []) :
    parseDec? (Q.map digitChar) = some ⟨digVal Q, 0⟩ := by
  have hc : ∀ c ∈ Q.map digitChar, c ≠ '.' := fun c hc => (dc_mem Q hd c hc).2
  unfold parseDec?
  rw [span_nodot _ hc]
  dsimp only
  rw [readNat_digits Q hd hne]
  rfl

theorem fmtDec_normal (m s : Nat) (hn : IsNormal ⟨m, s⟩) :
    fmtDec ⟨m, s⟩ = if s = 0 then (padDigits m s).map digitChar
      else ((padDigits m s).map digitChar).take ((padDigits m s).length - s) ++ '.' ::
        ((padDigits m s).map digitChar).drop ((padDigits m s).length - s) := by
  have h0 : digitChar 0 = '0' := digitChar_zero
  simp only [fmtDec, normalize_normal ⟨m, s⟩ hn, padDigits, List.map_append, List.map_replicate,
    h0, List.length_map, List.length_append, List.length_replicate]

theorem parse_normal (m s : Nat) (hn : IsNormal ⟨m, s⟩) :
    parseDec? (fmtDec ⟨m, s⟩) = some ⟨m, s⟩ := by
  obtain ⟨hd, hv, hlen, -⟩ := padDigits_props m s
  obtain ⟨-, hval, hne, -⟩ := digitsOf_props m
  rw [fmtDec_normal m s hn]
  by_cases hs : s = 0
  · subst hs
    rw [if_pos rfl, padDigits_zero m hne, parse_nodot (digitsOf m) (digitsOf_props m).1 hne, hval]
  · rw [if_neg hs]
    exact parse_core (padDigits m s) s m hd hv hlen (by omega)

theorem normal_chars (m s : Nat) (hn : IsNormal ⟨m, s⟩) :
    ∀ c ∈ fmtDec ⟨m, s⟩, c.isDigit = true ∨ c = '.' := by
  intro c hc
  have hd := (padDigits_props m s).1
  rw [fmtDec_normal m s hn] at hc
  by_cases hs : s = 0
  · rw [if_pos hs] at hc
    exact Or.inl (dc_mem _ hd c hc).1
  · rw [if_neg hs] at hc
    rcases List.mem_append.1 hc with h | h
    · exact Or.inl (dc_mem _ hd c (List.mem_of_mem_take h)).1
    · rcases List.mem_cons.1 h with h | h
      · exact Or.inr h
      · exact Or.inl (dc_mem _ hd c (List.mem_of_mem_drop h)).1

theorem normal_leading (m s : Nat) (hn : IsNormal ⟨m, s⟩) :
    ∃ c rest, fmtDec ⟨m, s⟩ = c :: rest ∧ c.isDigit = true := by
  obtain ⟨hd, -, hlen, -⟩ := padDigits_props m s
  rw [fmtDec_normal m s hn]
  have hne : (padDigits m s).map digitChar ≠ [] := by
    intro h
    have := congrArg List.length h
    simp only [List.length_map, List.length_nil] at this
    omega
  by_cases hs : s = 0
  · rw [if_pos hs]
    obtain ⟨c, rest, h⟩ := List.exists_cons_of_ne_nil hne
    have hc : c ∈ (padDigits m s).map digitChar := by rw [h]; simp
    exact ⟨c, rest, h, (dc_mem _ hd c hc).1⟩
  · rw [if_neg hs]
    have hne' : ((padDigits m s).map digitChar).take ((padDigits m s).length - s) ≠ [] := by
      intro h
      rcases List.take_eq_nil_iff.1 h with h | h
      · omega
      · exact hne h
    obtain ⟨c, t, h⟩ := List.exists_cons_of_ne_nil hne'
    have hc : c ∈ ((padDigits m s).map digitChar).take ((padDigits m s).length - s) := by
      rw [h]; simp
    exact ⟨c, t ++ '.' :: ((padDigits m s).map digitChar).drop ((padDigits m s).length - s),
      by rw [h]; rfl, (dc_mem _ hd c (List.mem_of_mem_take hc)).1⟩

theorem normal_last (m s : Nat) (hs : s ≠ 0) (hD : digitsOf m ≠ []) (hn : IsNormal ⟨m, s⟩) :
    (fmtDec ⟨m, s⟩).getLast? = some (digitChar (m % 10)) := by
  obtain ⟨-, -, hlen, hlast⟩ := padDigits_props m s
  have hlast' := hlast hD
  have hdrop : (((padDigits m s).map digitChar).drop ((padDigits m s).length - s)).getLast?
      = some (digitChar (m % 10)) := by
    rw [List.getLast?_drop, if_neg (by simp only [List.length_map]; omega), List.getLast?_map, hlast']
    rfl
  rw [fmtDec_normal m s hn, if_neg hs]
  simp [List.getLast?_append, List.getLast?_cons, hdrop]

theorem normal_no_trailing (n : Dec) (hn : n.IsNormal) (h : '.' ∈ fmtDec n) :
    (fmtDec n).getLast? ≠ some '0' := by
  obtain ⟨m, s⟩ := n
  by_cases hs : s = 0
  · subst hs
    rw [fmtDec_normal m 0 hn, if_pos rfl] at h
    obtain ⟨x, hx, hxeq⟩ := List.mem_map.1 h
    exact absurd hxeq (digitChar_facts x ((padDigits_props m 0).1 x hx)).2.2
  · have hD := (digitsOf_props m).2.2.1
    rw [normal_last m s hs hD hn]
    intro heq
    have hm : m % 10 ≠ 0 := by
      rcases hn with h' | h'
      · exact absurd h' hs
      · exact h'
    have h10 := Nat.mod_lt m (show 10 > 0 by decide)
    have := Option.some.inj heq
    rw [← digitChar_zero] at this
    exact hm (digitChar_inj _ h10 0 (by decide) this)

theorem parseDec_normal' (n : Dec) (hn : n.IsNormal) : parseDec? (fmtDec n) = some n := by
  obtain ⟨m, s⟩ := n
  exact parse_normal m s hn

theorem parseDec_fmtDec (d : Dec) : parseDec? (fmtDec d) = some d.normalize := by
  rw [← fmtDec_normalize d]
  exact parseDec_normal' _ (normalize_isNormal d)

theorem normal_chars' (n : Dec) (hn : n.IsNormal) :
    ∀ c ∈ fmtDec n, c.isDigit = true ∨ c = '.' := by
  obtain ⟨m, s⟩ := n
  exact normal_chars m s hn

theorem normal_leading' (n : Dec) (hn : n.IsNormal) :
    ∃ c rest, fmtDec n = c :: rest ∧ c.isDigit = true := by
  obtain ⟨m, s⟩ := n
  exact normal_leading m s hn

theorem fmtDec_chars (d : Dec) : ∀ c ∈ fmtDec d, c.isDigit = true ∨ c = '.' := by
  rw [← fmtDec_normalize d]
  exact normal_chars' _ (normalize_isNormal d)

theorem fmtDec_leading_digit (d : Dec) : ∃ c rest, fmtDec d = c :: rest ∧ c.isDigit = true := by
  rw [← fmtDec_normalize d]
  exact normal_leading' _ (normalize_isNormal d)

theorem fmtDec_no_trailing_zero (d : Dec) (h : '.' ∈ fmtDec d) : (fmtDec d).getLast? ≠ some '0' := by
  rw [← fmtDec_normalize d] at h ⊢
  exact normal_no_trailing d.normalize (normalize_isNormal d) h

theorem fmtDec_eq_iff (a b : Dec) : fmtDec a = fmtDec b ↔ Dec.Eqv a b := by
  constructor
  · intro h
    have h3 : parseDec? (fmtDec a) = parseDec? (fmtDec b) := by rw [h]
    rw [parseDec_fmtDec, parseDec_fmtDec] at h3
    have hn : a.normalize = b.normalize := Option.some.inj h3
    have e1 := normalize_eqv a
    have e2 := normalize_eqv b
    rw [hn] at e1
    exact eqv_trans' e1 (eqv_symm' e2)
  · intro h
    rw [← fmtDec_normalize a, ← fmtDec_normalize b, normalize_eq_of_eqv h]

end DoseGate

#print axioms DoseGate.eqv_refl'
#print axioms DoseGate.eqv_symm'
#print axioms DoseGate.eqv_trans'
#print axioms DoseGate.normalize_normal
#print axioms DoseGate.eqv_step
#print axioms DoseGate.normalize_aux
#print axioms DoseGate.normalize_eqv
#print axioms DoseGate.normalize_isNormal
#print axioms DoseGate.eqv_normal_eq
#print axioms DoseGate.normalize_eq_of_eqv
#print axioms DoseGate.normalize_idem
#print axioms DoseGate.fmtDec_normalize
#print axioms DoseGate.fold_acc
#print axioms DoseGate.digVal_cons
#print axioms DoseGate.digVal_nil
#print axioms DoseGate.digVal_append
#print axioms DoseGate.digVal_replicate_zero
#print axioms DoseGate.digitsOf_succ_eq
#print axioms DoseGate.digitsOf_small
#print axioms DoseGate.digitsOf_props
#print axioms DoseGate.digitChar_facts
#print axioms DoseGate.digitChar_inj
#print axioms DoseGate.digitChar_zero
#print axioms DoseGate.foldlM_digits
#print axioms DoseGate.readNat_digits
#print axioms DoseGate.span_loop_nodot
#print axioms DoseGate.span_loop_dot
#print axioms DoseGate.span_nodot
#print axioms DoseGate.span_dot
#print axioms DoseGate.dc_mem
#print axioms DoseGate.padDigits_props
#print axioms DoseGate.padDigits_zero
#print axioms DoseGate.parse_core
#print axioms DoseGate.parse_nodot
#print axioms DoseGate.fmtDec_normal
#print axioms DoseGate.parse_normal
#print axioms DoseGate.normal_chars
#print axioms DoseGate.normal_leading
#print axioms DoseGate.normal_last
#print axioms DoseGate.normal_no_trailing
#print axioms DoseGate.parseDec_normal'
#print axioms DoseGate.parseDec_fmtDec
#print axioms DoseGate.normal_chars'
#print axioms DoseGate.normal_leading'
#print axioms DoseGate.fmtDec_chars
#print axioms DoseGate.fmtDec_leading_digit
#print axioms DoseGate.fmtDec_no_trailing_zero
#print axioms DoseGate.fmtDec_eq_iff
