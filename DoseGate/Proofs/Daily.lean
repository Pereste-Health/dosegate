import DoseGate.Proofs.Units

namespace DoseGate

theorem dosesPerDay_spec {t : Timing} {k : Nat} (h : dosesPerDay? t = some k) :
    (t.periodUnit = .d ∧ t.period = 1 ∧ k = t.frequency) ∨
    (t.periodUnit = .h ∧ k * t.period = t.frequency * 24) := by
  rcases t with ⟨f, p, u⟩
  unfold dosesPerDay? at h
  cases u
  · simp only at h
    split at h
    next hc =>
      obtain rfl := Option.some.inj h
      have hd : p ∣ 24 := Nat.dvd_of_mod_eq_zero hc.2.1
      refine Or.inr ⟨rfl, ?_⟩
      show f * (24 / p) * p = f * 24
      rw [Nat.mul_assoc, Nat.div_mul_cancel hd]
    next => cases h
  · simp only at h
    split at h
    next hc =>
      obtain rfl := Option.some.inj h
      exact Or.inl ⟨rfl, hc.1, rfl⟩
    next => cases h
  · cases h
  · cases h

theorem dosesPerDay_pos {t : Timing} {k : Nat} (h : dosesPerDay? t = some k) : 0 < k := by
  rcases t with ⟨f, p, u⟩
  unfold dosesPerDay? at h
  cases u
  · simp only at h
    split at h
    next hc =>
      obtain rfl := Option.some.inj h
      have hd : p ∣ 24 := Nat.dvd_of_mod_eq_zero hc.2.1
      exact Nat.mul_pos (Nat.pos_of_ne_zero hc.2.2)
        (Nat.div_pos (Nat.le_of_dvd (by decide) hd) (Nat.pos_of_ne_zero hc.1))
    next => cases h
  · simp only at h
    split at h
    next hc =>
      obtain rfl := Option.some.inj h
      exact Nat.pos_of_ne_zero hc.2
    next => cases h
  · cases h
  · cases h

theorem dosesPerDay_none_long {t : Timing} (h : t.periodUnit = .wk ∨ t.periodUnit = .mo) :
    dosesPerDay? t = none := by
  unfold dosesPerDay?
  rcases h with h | h <;> simp [h]

theorem dailyDose_spec {m : MedReq} {dd : Dose} (h : dailyDose? m = some dd) :
    ∃ d t k, m.asNeeded = false ∧ m.dose = some d ∧ m.timing = some t ∧ dosesPerDay? t = some k ∧
      dd.unit = d.unit ∧ ∀ q, toQty d.amount d.unit = some q → toQty dd.amount dd.unit = some ⟨q.dim, k * q.base⟩ := by
  have hn : m.asNeeded = false := by
    cases ha : m.asNeeded
    · rfl
    · simp [dailyDose?, ha] at h
  unfold dailyDose? at h
  simp only [hn, Bool.false_eq_true, ↓reduceIte] at h
  rcases hd : m.dose with _ | d <;> rcases ht : m.timing with _ | t <;> simp only [hd, ht] at h
  · cases h
  · cases h
  · cases h
  rcases hk : dosesPerDay? t with _ | k
  · simp [hk] at h
  simp only [hk, Option.map_some] at h
  obtain rfl := Option.some.inj h
  refine ⟨d, t, k, hn, rfl, rfl, hk, rfl, ?_⟩
  intro q hq
  obtain ⟨hmod, rfl⟩ := (toQty_eq_some _ _ _).1 hq
  have e : d.amount.mant * k * d.unit.factor = d.amount.mant * d.unit.factor * k :=
    Nat.mul_right_comm _ _ _
  obtain ⟨h1, h2⟩ := mul_transfer (d.amount.mant * d.unit.factor) (10 ^ d.amount.scale) k
    (Nat.pow_pos (by decide)) hmod
  rw [toQty_eq_some]
  refine ⟨?_, ?_⟩
  · show d.amount.mant * k * d.unit.factor % 10 ^ d.amount.scale = 0
    rw [e]
    exact h1
  · show (⟨d.unit.dim, k * (d.amount.mant * d.unit.factor / 10 ^ d.amount.scale)⟩ : Qty) =
      ⟨d.unit.dim, d.amount.mant * k * d.unit.factor / 10 ^ d.amount.scale⟩
    rw [e, h2, Nat.mul_comm k]

theorem dailyDose_none_prn {m : MedReq} (h : m.asNeeded = true) : dailyDose? m = none := by
  unfold dailyDose?
  simp [h]

theorem dailyDose_exact {m : MedReq} {dd : Dose} (h : dailyDose? m = some dd) :
    ∃ d t k, m.asNeeded = false ∧ m.dose = some d ∧ m.timing = some t ∧ dosesPerDay? t = some k ∧
      dd = ⟨⟨d.amount.mant * k, d.amount.scale⟩, d.unit⟩ := by
  have hn : m.asNeeded = false := by
    cases ha : m.asNeeded
    · rfl
    · simp [dailyDose?, ha] at h
  unfold dailyDose? at h
  simp only [hn, Bool.false_eq_true, ↓reduceIte] at h
  rcases hd : m.dose with _ | d <;> rcases ht : m.timing with _ | t <;> simp only [hd, ht] at h
  · cases h
  · cases h
  · cases h
  rcases hk : dosesPerDay? t with _ | k
  · simp [hk] at h
  simp only [hk, Option.map_some] at h
  obtain rfl := Option.some.inj h
  exact ⟨d, t, k, hn, rfl, rfl, hk, rfl⟩

end DoseGate
