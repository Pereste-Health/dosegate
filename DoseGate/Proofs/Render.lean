import DoseGate.Spec

namespace DoseGate

theorem tokens_append_of_separated {a b : List Char} (h : separated a b = true) :
    tokens (a ++ b) = tokens a ++ tokens b := sorry

theorem tokens_flatten {ps : List (List Char)} (h : allSeparated ps = true) :
    tokens ps.flatten = ps.flatMap tokens := sorry

theorem render_fidelity {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧ r = pieces.flatten := sorry

theorem render_dose_tokens_from_chart {p : Policy} {chart : List MedReq} {out r : List Char}
    (h : render p chart out = .ok r) :
    ∃ segs pieces, parseTemplate out = some segs ∧
      Forall₂ (SegRendersTo chart) segs pieces ∧
      (tokens r).filter (blockedToken p) = slotDoseTokens p segs pieces := sorry

theorem render_text_clean {p : Policy} {chart : List MedReq} {out r t : List Char} {segs : List Seg}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs) (ht : Seg.text t ∈ segs) :
    (tokens t).all (fun tok => !blockedToken p tok) = true ∧ t.all (·.toNat < 128) = true := sorry

theorem render_malformed {p : Policy} {chart : List MedReq} {out : List Char}
    (h : parseTemplate out = none) : ∃ b, render p chart out = .error b := sorry

theorem render_no_active_order {p : Policy} {chart : List MedReq} {out id : List Char}
    {segs : List Seg} {f : Field}
    (hp : parseTemplate out = some segs) (hs : Seg.slot f id ∈ segs)
    (hn : ∀ m ∈ chart, m.id = id → m.active = false) :
    ∃ b, render p chart out = .error b := sorry

theorem render_missing_field {p : Policy} {chart : List MedReq} {out id : List Char}
    {segs : List Seg} {f : Field}
    (hp : parseTemplate out = some segs) (hs : Seg.slot f id ∈ segs)
    (hm : ∀ m ∈ chart, m.id = id → fmtField f m = none) :
    ∃ b, render p chart out = .error b := sorry

theorem render_duplicate_ids {p : Policy} {chart : List MedReq} {out : List Char}
    (h : ¬ (chart.map (·.id)).Nodup) : ∃ b, render p chart out = .error b := sorry

theorem render_binding {p : Policy} {chart : List MedReq} {out r : List Char} {segs : List Seg}
    (h : render p chart out = .ok r) (hp : parseTemplate out = some segs) :
    ∀ g ∈ sentenceGroups segs [], groupBound g = true := sorry

end DoseGate
