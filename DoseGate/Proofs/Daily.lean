import DoseGate.Proofs.Units

namespace DoseGate

theorem dosesPerDay_spec {t : Timing} {k : Nat} (h : dosesPerDay? t = some k) :
    (t.periodUnit = .d ∧ t.period = 1 ∧ k = t.frequency) ∨
    (t.periodUnit = .h ∧ k * t.period = t.frequency * 24) := sorry

theorem dosesPerDay_pos {t : Timing} {k : Nat} (h : dosesPerDay? t = some k) : 0 < k := sorry

theorem dosesPerDay_none_long {t : Timing} (h : t.periodUnit = .wk ∨ t.periodUnit = .mo) :
    dosesPerDay? t = none := sorry

theorem dailyDose_spec {m : MedReq} {dd : Dose} (h : dailyDose? m = some dd) :
    ∃ d t k, m.asNeeded = false ∧ m.dose = some d ∧ m.timing = some t ∧ dosesPerDay? t = some k ∧
      dd.unit = d.unit ∧ ∀ q, toQty d.amount d.unit = some q → toQty dd.amount dd.unit = some ⟨q.dim, k * q.base⟩ := sorry

theorem dailyDose_none_prn {m : MedReq} (h : m.asNeeded = true) : dailyDose? m = none := sorry

end DoseGate
