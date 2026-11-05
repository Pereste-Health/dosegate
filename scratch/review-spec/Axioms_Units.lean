import DoseGate.Fhir
import DoseGate.Proofs.Dec

namespace DoseGate

theorem toQty_eq_some (d : Dec) (u : DoseUnit) (q : Qty) :
    toQty d u = some q ↔
      (d.mant * u.factor) % 10 ^ d.scale = 0 ∧ q = ⟨u.dim, d.mant * u.factor / 10 ^ d.scale⟩ := by
  unfold toQty
  dsimp only
  by_cases h : (d.mant * u.factor) % 10 ^ d.scale = 0
  · rw [if_pos h]
    constructor
    · intro e
      exact ⟨h, (Option.some.inj e).symm⟩
    · rintro ⟨-, rfl⟩
      rfl
  · rw [if_neg h]
    constructor
    · intro e
      cases e
    · rintro ⟨h', -⟩
      exact absurd h' h

theorem toQty_dim {d : Dec} {u : DoseUnit} {q : Qty} (h : toQty d u = some q) : q.dim = u.dim := by
  rw [toQty_eq_some] at h
  rw [h.2]

theorem toQty_exact {d : Dec} {u : DoseUnit} {q : Qty} (h : toQty d u = some q) :
    q.base * 10 ^ d.scale = d.mant * u.factor := by
  rw [toQty_eq_some] at h
  obtain ⟨hmod, rfl⟩ := h
  exact Nat.div_mul_cancel (Nat.dvd_of_mod_eq_zero hmod)

theorem div_transfer (A B P Q : Nat) (hP : 0 < P) (hQ : 0 < Q) (h : A * Q = B * P)
    (hA : A % P = 0) : B % Q = 0 ∧ B / Q = A / P := by
  obtain ⟨x, rfl⟩ := Nat.dvd_of_mod_eq_zero hA
  have hB : B = x * Q := by
    apply Nat.eq_of_mul_eq_mul_right hP
    grind
  subst hB
  refine ⟨Nat.mul_mod_left _ _, ?_⟩
  rw [Nat.mul_div_cancel x hQ, Nat.mul_div_cancel_left x hP]

theorem toQty_eqv {a b : Dec} (u : DoseUnit) (h : Dec.Eqv a b) : toQty a u = toQty b u := by
  have hE : a.mant * 10 ^ b.scale = b.mant * 10 ^ a.scale := h
  have hAB : (a.mant * u.factor) * 10 ^ b.scale = (b.mant * u.factor) * 10 ^ a.scale := by
    calc (a.mant * u.factor) * 10 ^ b.scale = (a.mant * 10 ^ b.scale) * u.factor :=
          Nat.mul_right_comm _ _ _
      _ = (b.mant * 10 ^ a.scale) * u.factor := by rw [hE]
      _ = (b.mant * u.factor) * 10 ^ a.scale := Nat.mul_right_comm _ _ _
  have hP : 0 < 10 ^ a.scale := Nat.pow_pos (by decide)
  have hQ : 0 < 10 ^ b.scale := Nat.pow_pos (by decide)
  unfold toQty
  dsimp only
  by_cases hA : (a.mant * u.factor) % 10 ^ a.scale = 0
  · obtain ⟨h1, h2⟩ := div_transfer _ _ _ _ hP hQ hAB hA
    rw [if_pos hA, if_pos h1, h2]
  · have hB : ¬ ((b.mant * u.factor) % 10 ^ b.scale = 0) := fun hB =>
      hA (div_transfer _ _ _ _ hQ hP hAB.symm hB).1
    rw [if_neg hA, if_neg hB]

theorem mul_transfer (n P k : Nat) (hP : 0 < P) (hn : n % P = 0) :
    (n * k) % P = 0 ∧ n * k / P = n / P * k := by
  obtain ⟨c, rfl⟩ := Nat.dvd_of_mod_eq_zero hn
  rw [Nat.mul_assoc]
  refine ⟨Nat.mul_mod_right _ _, ?_⟩
  rw [Nat.mul_div_cancel_left (c * k) hP, Nat.mul_div_cancel_left c hP]

theorem toQty_mcg_mg {d : Dec} {q : Qty} (h : toQty d .mcg = some q) :
    toQty d .mg = some ⟨.mass, 1000 * q.base⟩ := by
  rw [toQty_eq_some] at h
  obtain ⟨hmod, rfl⟩ := h
  rw [toQty_eq_some]
  have ht := mul_transfer (d.mant * 1000) (10 ^ d.scale) 1000 (Nat.pow_pos (by decide)) hmod
  have e : d.mant * DoseUnit.factor .mg = d.mant * 1000 * 1000 := by
    show d.mant * 1000000 = d.mant * 1000 * 1000
    omega
  rw [e]
  refine ⟨ht.1, ?_⟩
  show (⟨Dim.mass, 1000 * (d.mant * 1000 / 10 ^ d.scale)⟩ : Qty) =
    ⟨Dim.mass, d.mant * 1000 * 1000 / 10 ^ d.scale⟩
  rw [ht.2, Nat.mul_comm 1000]

theorem toQty_mg_g {d : Dec} {q : Qty} (h : toQty d .mg = some q) :
    toQty d .g = some ⟨.mass, 1000 * q.base⟩ := by
  rw [toQty_eq_some] at h
  obtain ⟨hmod, rfl⟩ := h
  rw [toQty_eq_some]
  have ht := mul_transfer (d.mant * 1000000) (10 ^ d.scale) 1000 (Nat.pow_pos (by decide)) hmod
  have e : d.mant * DoseUnit.factor .g = d.mant * 1000000 * 1000 := by
    show d.mant * 1000000000 = d.mant * 1000000 * 1000
    omega
  rw [e]
  refine ⟨ht.1, ?_⟩
  show (⟨Dim.mass, 1000 * (d.mant * 1000000 / 10 ^ d.scale)⟩ : Qty) =
    ⟨Dim.mass, d.mant * 1000000 * 1000 / 10 ^ d.scale⟩
  rw [ht.2, Nat.mul_comm 1000]

theorem toQty_mL_L {d : Dec} {q : Qty} (h : toQty d .mL = some q) :
    toQty d .L = some ⟨.volume, 1000 * q.base⟩ := by
  rw [toQty_eq_some] at h
  obtain ⟨hmod, rfl⟩ := h
  rw [toQty_eq_some]
  have ht := mul_transfer (d.mant * 1000000) (10 ^ d.scale) 1000 (Nat.pow_pos (by decide)) hmod
  have e : d.mant * DoseUnit.factor .L = d.mant * 1000000 * 1000 := by
    show d.mant * 1000000000 = d.mant * 1000000 * 1000
    omega
  rw [e]
  refine ⟨ht.1, ?_⟩
  show (⟨Dim.volume, 1000 * (d.mant * 1000000 / 10 ^ d.scale)⟩ : Qty) =
    ⟨Dim.volume, d.mant * 1000000 * 1000 / 10 ^ d.scale⟩
  rw [ht.2, Nat.mul_comm 1000]

theorem toQty_mg_total {d : Dec} (h : d.scale ≤ 6) : (toQty d .mg).isSome = true := by
  have h6 : 10 ^ d.scale ∣ 1000000 := Nat.pow_dvd_pow 10 h
  have hd : 10 ^ d.scale ∣ d.mant * DoseUnit.factor .mg :=
    Nat.dvd_trans h6 (Nat.dvd_mul_left 1000000 d.mant)
  unfold toQty
  dsimp only
  rw [if_pos (Nat.mod_eq_zero_of_dvd hd)]
  rfl

theorem le?_cross_dim {a b : Qty} (h : a.dim ≠ b.dim) : a.le? b = none := by
  unfold Qty.le?
  rw [if_neg h]

theorem le?_same_dim {a b : Qty} (h : a.dim = b.dim) : a.le? b = some (decide (a.base ≤ b.base)) := by
  unfold Qty.le?
  rw [if_pos h]

theorem name_inj {u v : DoseUnit} {o o' : Bool} (h : u.name o = v.name o') : u = v := by
  cases u <;> cases v <;> cases o <;> cases o' <;> revert h <;> decide

theorem sep_split : ∀ (X X' Y Y' : List Char), (∀ c ∈ X, c ≠ ' ') → (∀ c ∈ X', c ≠ ' ') →
    X ++ ' ' :: Y = X' ++ ' ' :: Y' → X = X' ∧ Y = Y' := by
  intro X
  induction X with
  | nil =>
    intro X' Y Y' _ hX' h
    cases X' with
    | nil => simpa using h
    | cons x X' =>
      simp only [List.nil_append, List.cons_append, List.cons.injEq] at h
      exact absurd h.1.symm (hX' x (by simp))
  | cons x X ih =>
    intro X' Y Y' hX hX' h
    cases X' with
    | nil =>
      simp only [List.nil_append, List.cons_append, List.cons.injEq] at h
      exact absurd h.1 (hX x (by simp))
    | cons x' X' =>
      simp only [List.cons_append, List.cons.injEq] at h
      obtain ⟨hx, ht⟩ := h
      subst hx
      obtain ⟨h1, h2⟩ := ih X' Y Y' (fun c hc => hX c (by simp [hc]))
        (fun c hc => hX' c (by simp [hc])) ht
      exact ⟨by rw [h1], h2⟩

theorem sep_suffix (X X' W W' : List Char) (hW : ∀ c ∈ W, c ≠ ' ') (hW' : ∀ c ∈ W', c ≠ ' ')
    (h : X ++ ' ' :: W = X' ++ ' ' :: W') : X = X' ∧ W = W' := by
  have h2 : W.reverse ++ ' ' :: X.reverse = W'.reverse ++ ' ' :: X'.reverse := by
    have := congrArg List.reverse h
    simpa using this
  obtain ⟨h3, h4⟩ := sep_split W.reverse W'.reverse X.reverse X'.reverse
    (fun c hc => hW c (List.mem_reverse.1 hc)) (fun c hc => hW' c (List.mem_reverse.1 hc)) h2
  exact ⟨List.reverse_inj.1 h4, List.reverse_inj.1 h3⟩

theorem unitWord_inj (p q : PeriodUnit) (b c : Bool) (h : unitWord p b = unitWord q c) :
    p = q ∧ b = c := by
  cases p <;> cases q <;> cases b <;> cases c <;> revert h <;> decide

theorem unitWord_nospace (p : PeriodUnit) (b : Bool) : ∀ c ∈ unitWord p b, c ≠ ' ' := by
  cases p <;> cases b <;> decide

theorem unitWord_false_ne_hour (p : PeriodUnit) : unitWord p false ≠ "hour".toList := by
  cases p <;> decide

theorem tw_gen (f : Nat) (h1 : f ≠ 1) (h2 : f ≠ 2) (h3 : f ≠ 3) (h4 : f ≠ 4) :
    timesWord f = fmtDec ⟨f, 0⟩ ++ " times".toList := by
  simp [timesWord, h1, h2, h3, h4]

theorem tw_lit (f : Nat) (h : f = 1 ∨ f = 2 ∨ f = 3 ∨ f = 4) :
    ∃ c r, timesWord f = c :: r ∧ c.isDigit = false ∧ c ≠ 'e' := by
  rcases h with rfl | rfl | rfl | rfl
  · exact ⟨'o', "nce".toList, rfl, by decide, by decide⟩
  · exact ⟨'t', "wice".toList, rfl, by decide, by decide⟩
  · exact ⟨'t', "hree times".toList, rfl, by decide, by decide⟩
  · exact ⟨'f', "our times".toList, rfl, by decide, by decide⟩

theorem tw_gen_head (f : Nat) (h1 : f ≠ 1) (h2 : f ≠ 2) (h3 : f ≠ 3) (h4 : f ≠ 4) :
    ∃ c r, timesWord f = c :: r ∧ c.isDigit = true ∧ c ≠ 'e' := by
  obtain ⟨c, rest, hc, hd⟩ := fmtDec_leading_digit ⟨f, 0⟩
  refine ⟨c, rest ++ " times".toList, ?_, hd, ?_⟩
  · rw [tw_gen f h1 h2 h3 h4, hc, List.cons_append]
  · intro e
    rw [e] at hd
    exact absurd hd (by decide)

theorem tw_inj (m n : Nat) (h : timesWord m = timesWord n) : m = n := by
  by_cases hm : m = 1 ∨ m = 2 ∨ m = 3 ∨ m = 4 <;> by_cases hn : n = 1 ∨ n = 2 ∨ n = 3 ∨ n = 4
  · rcases hm with rfl | rfl | rfl | rfl <;> rcases hn with rfl | rfl | rfl | rfl <;>
      first | rfl | (revert h; decide)
  · obtain ⟨c1, r1, h1, hd1, -⟩ := tw_lit m hm
    obtain ⟨c2, r2, h2, hd2, -⟩ := tw_gen_head n (by omega) (by omega) (by omega) (by omega)
    rw [h1, h2] at h
    obtain ⟨hc, -⟩ := List.cons.inj h
    rw [← hc, hd1] at hd2
    exact absurd hd2 (by decide)
  · obtain ⟨c1, r1, h1, hd1, -⟩ := tw_lit n hn
    obtain ⟨c2, r2, h2, hd2, -⟩ := tw_gen_head m (by omega) (by omega) (by omega) (by omega)
    rw [h1, h2] at h
    obtain ⟨hc, -⟩ := List.cons.inj h
    rw [hc, hd1] at hd2
    exact absurd hd2 (by decide)
  · have h' := h
    rw [tw_gen m (by omega) (by omega) (by omega) (by omega),
      tw_gen n (by omega) (by omega) (by omega) (by omega)] at h'
    have h'' := (fmtDec_eq_iff _ _).1 (List.append_cancel_right h')
    simpa [Dec.Eqv] using h''

theorem tw_head_ne_e (f : Nat) : ∃ c r, timesWord f = c :: r ∧ c ≠ 'e' := by
  by_cases hm : f = 1 ∨ f = 2 ∨ f = 3 ∨ f = 4
  · obtain ⟨c, r, h, -, h'⟩ := tw_lit f hm
    exact ⟨c, r, h, h'⟩
  · obtain ⟨c, r, h, -, h'⟩ := tw_gen_head f (by omega) (by omega) (by omega) (by omega)
    exact ⟨c, r, h, h'⟩

theorem head_tw_app (f : Nat) (X : List Char) : (timesWord f ++ X).head? ≠ some 'e' := by
  obtain ⟨c, r, hc, hne⟩ := tw_head_ne_e f
  rw [hc]
  simpa using hne

theorem fmtDec_nospace (d : Dec) : ∀ c ∈ fmtDec d, c ≠ ' ' := by
  intro c hc he
  subst he
  rcases fmtDec_chars d ' ' hc with h | h
  · exact absurd h (by decide)
  · exact absurd h (by decide)

theorem fmtDec_nat_inj (p q : Nat) (h : fmtDec ⟨p, 0⟩ = fmtDec ⟨q, 0⟩) : p = q := by
  have := (fmtDec_eq_iff _ _).1 h
  simpa [Dec.Eqv] using this

theorem B_shape (T U : List Char) : T ++ " a ".toList ++ U = (T ++ " a".toList) ++ ' ' :: U := by
  simp only [List.append_assoc]
  rfl

theorem D_shape (T P U : List Char) :
    T ++ " every ".toList ++ P ++ ' ' :: U = ((T ++ " every".toList) ++ ' ' :: P) ++ ' ' :: U := by
  simp only [List.append_assoc]
  rfl

theorem timing_ext {a b : Timing} (h1 : a.frequency = b.frequency) (h2 : a.period = b.period)
    (h3 : a.periodUnit = b.periodUnit) : a = b := by
  obtain ⟨f1, p1, u1⟩ := a
  obtain ⟨f2, p2, u2⟩ := b
  simp only at h1 h2 h3
  subst h1 h2 h3
  rfl

theorem timing_form (t : Timing) (s : List Char) (h : fmtTiming t = some s) :
    (t.period = 1 ∧ t.frequency = 1 ∧ t.periodUnit = .h ∧ s = "every hour".toList) ∨
    (t.period = 1 ∧ ¬(t.frequency = 1 ∧ t.periodUnit = .h) ∧ t.frequency ≠ 0 ∧
      s = timesWord t.frequency ++ " a ".toList ++ unitWord t.periodUnit true) ∨
    (t.period ≠ 1 ∧ t.period ≠ 0 ∧ t.frequency = 1 ∧
      s = "every ".toList ++ fmtDec ⟨t.period, 0⟩ ++ ' ' :: unitWord t.periodUnit false) ∨
    (t.period ≠ 1 ∧ t.period ≠ 0 ∧ t.frequency ≠ 1 ∧ t.frequency ≠ 0 ∧
      s = timesWord t.frequency ++ " every ".toList ++ fmtDec ⟨t.period, 0⟩ ++
        ' ' :: unitWord t.periodUnit false) := by
  unfold fmtTiming at h
  by_cases h0 : t.frequency = 0 ∨ t.period = 0
  · rw [if_pos h0] at h
    cases h
  rw [if_neg h0] at h
  have hf0 : t.frequency ≠ 0 := fun e => h0 (Or.inl e)
  have hp0 : t.period ≠ 0 := fun e => h0 (Or.inr e)
  by_cases hp : t.period = 1
  · rw [if_pos hp] at h
    by_cases hfh : t.frequency = 1 ∧ t.periodUnit = .h
    · rw [if_pos hfh] at h
      exact Or.inl ⟨hp, hfh.1, hfh.2, (Option.some.inj h).symm⟩
    · rw [if_neg hfh] at h
      exact Or.inr (Or.inl ⟨hp, hfh, hf0, (Option.some.inj h).symm⟩)
  · rw [if_neg hp] at h
    by_cases hf : t.frequency = 1
    · rw [if_pos hf] at h
      exact Or.inr (Or.inr (Or.inl ⟨hp, hp0, hf, (Option.some.inj h).symm⟩))
    · rw [if_neg hf] at h
      exact Or.inr (Or.inr (Or.inr ⟨hp, hp0, hf, hf0, (Option.some.inj h).symm⟩))

theorem form_A_head (s : List Char) (hs : s = "every hour".toList) : s.head? = some 'e' := by
  rw [hs]
  rfl

theorem form_C_head (s : List Char) (p : Nat) (u : PeriodUnit)
    (hs : s = "every ".toList ++ fmtDec ⟨p, 0⟩ ++ ' ' :: unitWord u false) :
    s.head? = some 'e' := by
  rw [hs]
  rfl

theorem form_B_head (s : List Char) (f : Nat) (u : PeriodUnit)
    (hs : s = timesWord f ++ " a ".toList ++ unitWord u true) : s.head? ≠ some 'e' := by
  rw [hs]
  simp only [List.append_assoc]
  exact head_tw_app _ _

theorem form_D_head (s : List Char) (f p : Nat) (u : PeriodUnit)
    (hs : s = timesWord f ++ " every ".toList ++ fmtDec ⟨p, 0⟩ ++ ' ' :: unitWord u false) :
    s.head? ≠ some 'e' := by
  rw [hs]
  simp only [List.append_assoc]
  exact head_tw_app _ _

theorem fmtTiming_inj {a b : Timing} {s : List Char}
    (ha : fmtTiming a = some s) (hb : fmtTiming b = some s) : a = b := by
  rcases timing_form a s ha with ⟨pa, fa, ua, hsa⟩ | ⟨pa, hna, fa0, hsa⟩ | ⟨pa, pa0, fa1, hsa⟩ |
      ⟨pa, pa0, fa1, fa0, hsa⟩
  · rcases timing_form b s hb with ⟨pb, fb, ub, hsb⟩ | ⟨pb, hnb, fb0, hsb⟩ | ⟨pb, pb0, fb1, hsb⟩ |
      ⟨pb, pb0, fb1, fb0, hsb⟩
    · exact timing_ext (fa.trans fb.symm) (pa.trans pb.symm) (ua.trans ub.symm)
    · exact absurd (form_A_head s hsa) (form_B_head s _ _ hsb)
    · exfalso
      have h1 : "every".toList ++ ' ' :: "hour".toList =
          (("every".toList ++ ' ' :: fmtDec ⟨b.period, 0⟩) ++ ' ' :: unitWord b.periodUnit false) :=
        hsa.symm.trans hsb
      obtain ⟨-, hw⟩ := sep_suffix _ _ _ _ (by decide) (unitWord_nospace _ _) h1
      exact unitWord_false_ne_hour b.periodUnit hw.symm
    · exact absurd (form_A_head s hsa) (form_D_head s _ _ _ hsb)
  · rcases timing_form b s hb with ⟨pb, fb, ub, hsb⟩ | ⟨pb, hnb, fb0, hsb⟩ | ⟨pb, pb0, fb1, hsb⟩ |
      ⟨pb, pb0, fb1, fb0, hsb⟩
    · exact absurd (form_A_head s hsb) (form_B_head s _ _ hsa)
    · have ea : s = (timesWord a.frequency ++ " a".toList) ++ ' ' :: unitWord a.periodUnit true :=
        hsa.trans (B_shape _ _)
      have eb : s = (timesWord b.frequency ++ " a".toList) ++ ' ' :: unitWord b.periodUnit true :=
        hsb.trans (B_shape _ _)
      obtain ⟨hX, hW⟩ := sep_suffix _ _ _ _ (unitWord_nospace _ _) (unitWord_nospace _ _)
        (ea.symm.trans eb)
      have hT := List.append_cancel_right hX
      exact timing_ext (tw_inj _ _ hT) (pa.trans pb.symm) (unitWord_inj _ _ _ _ hW).1
    · exact absurd (form_C_head s _ _ hsb) (form_B_head s _ _ hsa)
    · have ea : s = (timesWord a.frequency ++ " a".toList) ++ ' ' :: unitWord a.periodUnit true :=
        hsa.trans (B_shape _ _)
      have ed : s = ((timesWord b.frequency ++ " every".toList) ++ ' ' :: fmtDec ⟨b.period, 0⟩) ++
          ' ' :: unitWord b.periodUnit false := hsb.trans (D_shape _ _ _)
      obtain ⟨-, hW⟩ := sep_suffix _ _ _ _ (unitWord_nospace _ _) (unitWord_nospace _ _)
        (ea.symm.trans ed)
      exact absurd (unitWord_inj _ _ _ _ hW).2 (by decide)
  · rcases timing_form b s hb with ⟨pb, fb, ub, hsb⟩ | ⟨pb, hnb, fb0, hsb⟩ | ⟨pb, pb0, fb1, hsb⟩ |
      ⟨pb, pb0, fb1, fb0, hsb⟩
    · exfalso
      have h1 : "every".toList ++ ' ' :: "hour".toList =
          (("every".toList ++ ' ' :: fmtDec ⟨a.period, 0⟩) ++ ' ' :: unitWord a.periodUnit false) :=
        hsb.symm.trans hsa
      obtain ⟨-, hw⟩ := sep_suffix _ _ _ _ (by decide) (unitWord_nospace _ _) h1
      exact unitWord_false_ne_hour a.periodUnit hw.symm
    · exact absurd (form_C_head s _ _ hsa) (form_B_head s _ _ hsb)
    · obtain ⟨hX, hU⟩ := sep_suffix _ _ _ _ (unitWord_nospace _ _) (unitWord_nospace _ _)
        (hsa.symm.trans hsb)
      exact timing_ext (fa1.trans fb1.symm) (fmtDec_nat_inj _ _ (List.append_cancel_left hX))
        (unitWord_inj _ _ _ _ hU).1
    · exact absurd (form_C_head s _ _ hsa) (form_D_head s _ _ _ hsb)
  · rcases timing_form b s hb with ⟨pb, fb, ub, hsb⟩ | ⟨pb, hnb, fb0, hsb⟩ | ⟨pb, pb0, fb1, hsb⟩ |
      ⟨pb, pb0, fb1, fb0, hsb⟩
    · exact absurd (form_A_head s hsb) (form_D_head s _ _ _ hsa)
    · have eb : s = (timesWord b.frequency ++ " a".toList) ++ ' ' :: unitWord b.periodUnit true :=
        hsb.trans (B_shape _ _)
      have ed : s = ((timesWord a.frequency ++ " every".toList) ++ ' ' :: fmtDec ⟨a.period, 0⟩) ++
          ' ' :: unitWord a.periodUnit false := hsa.trans (D_shape _ _ _)
      obtain ⟨-, hW⟩ := sep_suffix _ _ _ _ (unitWord_nospace _ _) (unitWord_nospace _ _)
        (eb.symm.trans ed)
      exact absurd (unitWord_inj _ _ _ _ hW).2 (by decide)
    · exact absurd (form_C_head s _ _ hsb) (form_D_head s _ _ _ hsa)
    · have ea : s = ((timesWord a.frequency ++ " every".toList) ++ ' ' :: fmtDec ⟨a.period, 0⟩) ++
          ' ' :: unitWord a.periodUnit false := hsa.trans (D_shape _ _ _)
      have eb : s = ((timesWord b.frequency ++ " every".toList) ++ ' ' :: fmtDec ⟨b.period, 0⟩) ++
          ' ' :: unitWord b.periodUnit false := hsb.trans (D_shape _ _ _)
      obtain ⟨hX, hU⟩ := sep_suffix _ _ _ _ (unitWord_nospace _ _) (unitWord_nospace _ _)
        (ea.symm.trans eb)
      obtain ⟨hX1, hP⟩ := sep_suffix _ _ _ _ (fmtDec_nospace ⟨a.period, 0⟩)
        (fmtDec_nospace ⟨b.period, 0⟩) hX
      have hT := List.append_cancel_right hX1
      exact timing_ext (tw_inj _ _ hT) (fmtDec_nat_inj _ _ hP) (unitWord_inj _ _ _ _ hU).1

theorem route_phrase_inj {a b : Route} (h : a.phrase = b.phrase) : a = b := by
  cases a <;> cases b <;> revert h <;> decide

theorem fmtDose_inj {a b : Dose} (h : fmtDose a = fmtDose b) :
    Dec.Eqv a.amount b.amount ∧ a.unit = b.unit := by
  unfold fmtDose at h
  obtain ⟨hf, hn⟩ := sep_split (fmtDec a.amount) (fmtDec b.amount) _ _ (fmtDec_nospace _)
    (fmtDec_nospace _) h
  have hE := (fmtDec_eq_iff _ _).1 hf
  have hnorm := normalize_eq_of_eqv hE
  have hflag : (a.amount.normalize == (⟨1, 0⟩ : Dec)) = (b.amount.normalize == (⟨1, 0⟩ : Dec)) := by
    rw [hnorm]
  rw [hflag] at hn
  exact ⟨hE, name_inj hn⟩

end DoseGate

#print axioms DoseGate.toQty_eq_some
#print axioms DoseGate.toQty_dim
#print axioms DoseGate.toQty_exact
#print axioms DoseGate.div_transfer
#print axioms DoseGate.toQty_eqv
#print axioms DoseGate.mul_transfer
#print axioms DoseGate.toQty_mcg_mg
#print axioms DoseGate.toQty_mg_g
#print axioms DoseGate.toQty_mL_L
#print axioms DoseGate.toQty_mg_total
#print axioms DoseGate.le?_cross_dim
#print axioms DoseGate.le?_same_dim
#print axioms DoseGate.name_inj
#print axioms DoseGate.sep_split
#print axioms DoseGate.sep_suffix
#print axioms DoseGate.unitWord_inj
#print axioms DoseGate.unitWord_nospace
#print axioms DoseGate.unitWord_false_ne_hour
#print axioms DoseGate.tw_gen
#print axioms DoseGate.tw_lit
#print axioms DoseGate.tw_gen_head
#print axioms DoseGate.tw_inj
#print axioms DoseGate.tw_head_ne_e
#print axioms DoseGate.head_tw_app
#print axioms DoseGate.fmtDec_nospace
#print axioms DoseGate.fmtDec_nat_inj
#print axioms DoseGate.B_shape
#print axioms DoseGate.D_shape
#print axioms DoseGate.timing_ext
#print axioms DoseGate.timing_form
#print axioms DoseGate.form_A_head
#print axioms DoseGate.form_C_head
#print axioms DoseGate.form_B_head
#print axioms DoseGate.form_D_head
#print axioms DoseGate.fmtTiming_inj
#print axioms DoseGate.route_phrase_inj
#print axioms DoseGate.fmtDose_inj
