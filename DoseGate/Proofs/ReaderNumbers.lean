/-
Links from the parsed FHIR JSON to the numbers in a MedReq: the dose value,
dose unit, and timing fields that the reader copies from a dosageInstruction.
Each theorem names the JSON fields it reads and the conditions the reader
imposes on them. The JSON text parser (Lean.Json.parse) is outside this file.
-/
import DoseGate.Json
import DoseGate.Proofs.Dec

namespace DoseGate

open Lean (Json JsonNumber)

theorem jDec?_spec {j : Json} {d : Dec} (h : jDec? j = some d) :
    ∃ n : JsonNumber, j = .num n ∧ 0 ≤ n.mantissa ∧ n.exponent ≤ 9 ∧
      (d.mant : Int) = n.mantissa ∧ d.scale = n.exponent := by
  cases j with
  | num n =>
    have hd : jDec? (.num n) = if n.mantissa < 0 ∨ n.exponent > 9 ∨ 10 ^ 15 ≤ n.mantissa.toNat then none
        else some ⟨n.mantissa.toNat, n.exponent⟩ := rfl
    rw [hd] at h
    split at h
    · simp at h
    · rename_i hc
      have h0 : 0 ≤ n.mantissa := by omega
      have h9 : n.exponent ≤ 9 := by omega
      cases h
      exact ⟨n, rfl, h0, h9, Int.toNat_of_nonneg h0, rfl⟩
  | null => simp [jDec?] at h
  | bool _ => simp [jDec?] at h
  | str _ => simp [jDec?] at h
  | arr _ => simp [jDec?] at h
  | obj _ => simp [jDec?] at h

theorem jCount?_spec {j : Json} {v : Nat} (h : jCount? j = some v) :
    ∃ n : JsonNumber, j = .num n ∧ n.mantissa = (v : Int) * 10 ^ n.exponent ∧ v ≤ maxCount := by
  cases j with
  | num n =>
    have hd : jCount? (.num n) = if n.mantissa < 0 then none
        else if n.mantissa.toNat % 10 ^ n.exponent = 0 ∧ n.mantissa.toNat / 10 ^ n.exponent ≤ maxCount
          then some (n.mantissa.toNat / 10 ^ n.exponent) else none := rfl
    rw [hd] at h
    split at h
    · simp at h
    · rename_i hneg
      have h0 : 0 ≤ n.mantissa := by omega
      split at h
      · rename_i hc
        cases h
        have hdiv : n.mantissa.toNat = n.mantissa.toNat / 10 ^ n.exponent * 10 ^ n.exponent :=
          (Nat.div_mul_cancel (Nat.dvd_of_mod_eq_zero hc.1)).symm
        have key : ((n.mantissa.toNat : Nat) : Int)
            = ((n.mantissa.toNat / 10 ^ n.exponent : Nat) : Int) * 10 ^ n.exponent := by
          exact_mod_cast hdiv
        rw [Int.toNat_of_nonneg h0] at key
        exact ⟨n, rfl, key, hc.2⟩
      · simp at h
  | null => simp [jCount?] at h
  | bool _ => simp [jCount?] at h
  | str _ => simp [jCount?] at h
  | arr _ => simp [jCount?] at h
  | obj _ => simp [jCount?] at h

theorem jTiming?_spec {r : Json} {t : Timing} (h : jTiming? r = some t) :
    (∃ n : JsonNumber, jField? r "frequency" = some (.num n) ∧
        n.mantissa = (t.frequency : Int) * 10 ^ n.exponent) ∧
    (∃ n : JsonNumber, jField? r "period" = some (.num n) ∧
        n.mantissa = (t.period : Int) * 10 ^ n.exponent) ∧
    (∃ s : String, jStr? r "periodUnit" = some s ∧ PeriodUnit.ofCode? s = some t.periodUnit) := by
  unfold jTiming? at h
  obtain ⟨f, hX, hF⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨p, hY, hG⟩ := Option.bind_eq_some_iff.mp hF
  obtain ⟨u, hZ, hH⟩ := Option.bind_eq_some_iff.mp hG
  obtain ⟨vf, hvf, hcf⟩ := Option.bind_eq_some_iff.mp hX
  obtain ⟨vp, hvp, hcp⟩ := Option.bind_eq_some_iff.mp hY
  obtain ⟨n1, rfl, e1, -⟩ := jCount?_spec hcf
  obtain ⟨n2, rfl, e2, -⟩ := jCount?_spec hcp
  obtain ⟨s, hs, hu⟩ := Option.bind_eq_some_iff.mp hZ
  cases hH
  exact ⟨⟨n1, hvf, e1⟩, ⟨n2, hvp, e2⟩, ⟨s, hs, hu⟩⟩

theorem jUnit?_spec {q : Json} {u : DoseUnit} (h : jUnit? q = some u) :
    (∃ c, jField? q "code" = some (.str c) ∧ DoseUnit.ofCode? c = some u) ∨
    (jField? q "code" = none ∧ ∃ s, jStr? q "unit" = some s ∧ DoseUnit.ofCode? s = some u) := by
  cases hc : jField? q "code" with
  | none =>
    simp only [jUnit?, hc] at h
    obtain ⟨s, hs, hu⟩ := Option.bind_eq_some_iff.mp h
    exact Or.inr ⟨rfl, s, hs, hu⟩
  | some v =>
    cases v with
    | str c =>
      simp only [jUnit?, hc] at h
      exact Or.inl ⟨c, rfl, h⟩
    | null => simp [jUnit?, hc] at h
    | bool _ => simp [jUnit?, hc] at h
    | num _ => simp [jUnit?, hc] at h
    | arr _ => simp [jUnit?, hc] at h
    | obj _ => simp [jUnit?, hc] at h

theorem jDose?_spec {q : Json} {d : Dose} (h : jDose? q = some d) :
    ∃ n : JsonNumber, jField? q "value" = some (.num n) ∧ (d.amount.mant : Int) = n.mantissa ∧
      d.amount.scale = n.exponent ∧ d.amount.mant ≠ 0 ∧ d.unit.dim ≠ .count ∧
      ((∃ c, jField? q "code" = some (.str c) ∧ DoseUnit.ofCode? c = some d.unit) ∨
        (jField? q "code" = none ∧ ∃ s, jStr? q "unit" = some s ∧ DoseUnit.ofCode? s = some d.unit)) := by
  unfold jDose? at h
  rcases hb : (jField? q "value").bind jDec? with _ | amount
  · simp only [hb] at h
    simp at h
  · obtain ⟨v, hv, hdec⟩ := Option.bind_eq_some_iff.mp hb
    obtain ⟨n, rfl, -, -, hm, hs⟩ := jDec?_spec hdec
    simp only [hb] at h
    split at h
    · simp at h
    · rename_i hz
      rcases hu : jUnit? q with _ | u
      · simp [hu] at h
      · simp only [hu, Option.bind_some] at h
        split at h
        · simp at h
        · rename_i hdim
          cases h
          exact ⟨n, hv, hm, hs, hz, hdim, jUnit?_spec hu⟩

theorem doseQuantityOk_spec {q : Json} (h : doseQuantityOk q = true) :
    (jField? q "system" = none ∨ jField? q "system" = some (.str unitsOfMeasure)) ∧
    (∀ c u, jField? q "code" = some (.str c) → jField? q "unit" = some (.str u) → unitAccepted c u = true) := by
  unfold doseQuantityOk at h
  simp only [Bool.and_eq_true] at h
  obtain ⟨hsys, hunit⟩ := h
  constructor
  · cases hs : jField? q "system" with
    | none => exact Or.inl rfl
    | some sv =>
      rw [hs] at hsys
      cases sv with
      | str s =>
        simp only [beq_iff_eq] at hsys
        exact Or.inr (by rw [hsys])
      | null => simp at hsys
      | bool _ => simp at hsys
      | num _ => simp at hsys
      | arr _ => simp at hsys
      | obj _ => simp at hsys
  · intro c u hc hu
    simp only [hc, hu] at hunit
    exact hunit

theorem failsCheck_some {o : Option Json} {ok : Json → Bool} {q : Json}
    (h : failsCheck o ok = false) (hq : o = some q) : ok q = true := by
  subst hq
  simpa [failsCheck] using h

theorem closedDosage_dose {d q : Json} (h : closedDosage d = false)
    (hq : (jArr? d "doseAndRate").head?.bind (fun r => jField? r "doseQuantity") = some q) :
    doseQuantityOk q = true := by
  simp only [closedDosage] at h
  exact failsCheck_some (Bool.or_eq_false_iff.mp (Bool.or_eq_false_iff.mp h).1).2 hq

theorem freeText_or {ig b : Bool} (h : (!ig && b) = false) : ig = true ∨ b = false := by
  cases ig <;> simp_all

theorem or5_false {a b c d e : Bool} (h : (a || b || c || d || e) = false) :
    a = false ∧ b = false ∧ c = false ∧ d = false ∧ e = false := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> simp_all

theorem medReqOfJson_entry {ig : Bool} {patient : Option String} {refs : List String}
    {meds : List (Option String × Json)} {mr : Json} {m : MedReq}
    (h : medReqOfJson ig patient refs meds mr = some m) (hd : m.dose ≠ none ∨ m.timing ≠ none) :
    ∃ id d, jStr? mr "id" = some id ∧ jArr? mr "dosageInstruction" = [d] ∧
      failsClosed d = false ∧ closedDosage d = false ∧ closedOrder mr id refs = false ∧
      (ig = true ∨ hasFreeText mr d = false) ∧
      m.dose = ((jArr? d "doseAndRate").head?.bind (fun r => jField? r "doseQuantity")).bind jDose? ∧
      m.timing = (jField? d "timing").bind (fun t => (jField? t "repeat").bind jTiming?) := by
  unfold medReqOfJson at h
  obtain ⟨id, hid, hX⟩ := Option.bind_eq_some_iff.mp h
  dsimp only at hX
  split at hX
  · rename_i d hl
    split at hX
    · have hm := Option.some.inj hX
      subst hm
      simp at hd
    · rename_i hc
      have hb : (failsClosed d || closedOrder mr id refs || closedDosage d || !(medicationNamed meds mr).ok
          || (!ig && hasFreeText mr d)) = false := by simpa using hc
      obtain ⟨h1, h2, h3, -, h5⟩ := or5_false hb
      have hm := Option.some.inj hX
      subst hm
      exact ⟨id, d, hid, hl, h1, h3, h2, freeText_or h5, rfl, rfl⟩
  · cases hX
    simp at hd

theorem medReqOfJson_dose_json {ig : Bool} {patient : Option String} {refs : List String}
    {meds : List (Option String × Json)} {mr : Json} {m : MedReq}
    (h : medReqOfJson ig patient refs meds mr = some m) {x : Dose} (hx : m.dose = some x) :
    ∃ id d q n, jStr? mr "id" = some id ∧ jArr? mr "dosageInstruction" = [d] ∧
      failsClosed d = false ∧ closedDosage d = false ∧ closedOrder mr id refs = false ∧
      (ig = true ∨ hasFreeText mr d = false) ∧
      (jArr? d "doseAndRate").head?.bind (fun r => jField? r "doseQuantity") = some q ∧
      doseQuantityOk q = true ∧
      (jField? q "system" = none ∨ jField? q "system" = some (.str unitsOfMeasure)) ∧
      jField? q "value" = some (.num n) ∧ (x.amount.mant : Int) = n.mantissa ∧
      x.amount.scale = n.exponent ∧ x.amount.mant ≠ 0 ∧ x.unit.dim ≠ .count ∧
      ((∃ c, jField? q "code" = some (.str c) ∧ DoseUnit.ofCode? c = some x.unit) ∨
        (jField? q "code" = none ∧ ∃ s, jStr? q "unit" = some s ∧ DoseUnit.ofCode? s = some x.unit)) := by
  obtain ⟨id, d, hid, hl, h1, h3, h2, h5, hdose, -⟩ :=
    medReqOfJson_entry h (Or.inl (by simp [hx]))
  have hx' : ((jArr? d "doseAndRate").head?.bind (fun r => jField? r "doseQuantity")).bind jDose?
      = some x := by
    rw [← hdose]
    exact hx
  obtain ⟨q, hq, hjq⟩ := Option.bind_eq_some_iff.mp hx'
  have hok := closedDosage_dose h3 hq
  obtain ⟨hsys, -⟩ := doseQuantityOk_spec hok
  obtain ⟨n, hv, hm, hs, hnz, hdim, hunit⟩ := jDose?_spec hjq
  exact ⟨id, d, q, n, hid, hl, h1, h3, h2, h5, hq, hok, hsys, hv, hm, hs, hnz, hdim, hunit⟩

theorem medReqOfJson_timing_json {ig : Bool} {patient : Option String} {refs : List String}
    {meds : List (Option String × Json)} {mr : Json} {m : MedReq}
    (h : medReqOfJson ig patient refs meds mr = some m) {t : Timing} (hx : m.timing = some t) :
    ∃ id d tj r, jStr? mr "id" = some id ∧ jArr? mr "dosageInstruction" = [d] ∧
      failsClosed d = false ∧ closedDosage d = false ∧ closedOrder mr id refs = false ∧
      (ig = true ∨ hasFreeText mr d = false) ∧
      jField? d "timing" = some tj ∧ jField? tj "repeat" = some r ∧ jTiming? r = some t ∧
      (∃ n : JsonNumber, jField? r "frequency" = some (.num n) ∧
        n.mantissa = (t.frequency : Int) * 10 ^ n.exponent) ∧
      (∃ n : JsonNumber, jField? r "period" = some (.num n) ∧
        n.mantissa = (t.period : Int) * 10 ^ n.exponent) ∧
      (∃ s : String, jStr? r "periodUnit" = some s ∧ PeriodUnit.ofCode? s = some t.periodUnit) := by
  obtain ⟨id, d, hid, hl, h1, h3, h2, h5, -, htim⟩ :=
    medReqOfJson_entry h (Or.inr (by simp [hx]))
  have hx' : (jField? d "timing").bind (fun t => (jField? t "repeat").bind jTiming?) = some t := by
    rw [← htim]
    exact hx
  obtain ⟨tj, htj, hr⟩ := Option.bind_eq_some_iff.mp hx'
  obtain ⟨r, hr', hjt⟩ := Option.bind_eq_some_iff.mp hr
  obtain ⟨hf, hp, hu⟩ := jTiming?_spec hjt
  exact ⟨id, d, tj, r, hid, hl, h1, h3, h2, h5, htj, hr', hjt, hf, hp, hu⟩

theorem jDec?_text {j : Json} {d : Dec} (h : jDec? j = some d) :
    ∃ n : JsonNumber, j = .num n ∧ parseDec? (fmtDec d) = some d.normalize ∧ Dec.Eqv d d.normalize ∧
      (d.mant : Int) = n.mantissa ∧ d.scale = n.exponent := by
  obtain ⟨n, rfl, -, -, hm, hs⟩ := jDec?_spec h
  exact ⟨n, rfl, parseDec_fmtDec d, normalize_eqv d, hm, hs⟩

theorem chartOf_mem {ig : Bool} {patient : Option String} {req : Json} {ms : List MedReq} {m : MedReq}
    (h : chartOf ig patient req = some ms) (hm : m ∈ ms) :
    ∃ mr ∈ orderResources req, ∃ meds, medReqOfJson ig patient (priorRefs (orderResources req)) meds mr = some m := by
  unfold chartOf at h
  unfold orderResources
  split at h
  · rename_i b hb
    cases h
    simp only [hb]
    obtain ⟨mr, hmr, hm'⟩ := List.mem_filterMap.mp (by unfold chartFrom at hm; exact hm)
    exact ⟨mr, hmr, medicationEntries req, hm'⟩
  · rename_i hb b
    cases h
    simp only [hb]
    obtain ⟨mr, hmr, hm'⟩ := List.mem_filterMap.mp (by unfold chartFrom at hm; exact hm)
    exact ⟨mr, hmr, [], hm'⟩
  · simp at h

end DoseGate
