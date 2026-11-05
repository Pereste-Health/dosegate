import DoseGate.Fhir

namespace DoseGate

theorem toQty_dim {d : Dec} {u : DoseUnit} {q : Qty} (h : toQty d u = some q) : q.dim = u.dim := sorry

theorem toQty_exact {d : Dec} {u : DoseUnit} {q : Qty} (h : toQty d u = some q) :
    q.base * 10 ^ d.scale = d.mant * u.factor := sorry

theorem toQty_eqv {a b : Dec} (u : DoseUnit) (h : Dec.Eqv a b) : toQty a u = toQty b u := sorry

theorem toQty_mcg_mg {d : Dec} {q : Qty} (h : toQty d .mcg = some q) :
    toQty d .mg = some ⟨.mass, 1000 * q.base⟩ := sorry

theorem toQty_mg_g {d : Dec} {q : Qty} (h : toQty d .mg = some q) :
    toQty d .g = some ⟨.mass, 1000 * q.base⟩ := sorry

theorem toQty_mL_L {d : Dec} {q : Qty} (h : toQty d .mL = some q) :
    toQty d .L = some ⟨.volume, 1000 * q.base⟩ := sorry

theorem toQty_mg_total {d : Dec} (h : d.scale ≤ 6) : (toQty d .mg).isSome = true := sorry

theorem le?_cross_dim {a b : Qty} (h : a.dim ≠ b.dim) : a.le? b = none := sorry

theorem le?_same_dim {a b : Qty} (h : a.dim = b.dim) : a.le? b = some (decide (a.base ≤ b.base)) := sorry

theorem name_inj {u v : DoseUnit} {o o' : Bool} (h : u.name o = v.name o') : u = v := sorry

theorem fmtDose_inj {a b : Dose} (h : fmtDose a = fmtDose b) :
    Dec.Eqv a.amount b.amount ∧ a.unit = b.unit := sorry

theorem fmtTiming_inj {a b : Timing} {s : List Char}
    (ha : fmtTiming a = some s) (hb : fmtTiming b = some s) : a = b := sorry

theorem route_phrase_inj {a b : Route} (h : a.phrase = b.phrase) : a = b := sorry

end DoseGate
