import DoseGate.Template

namespace DoseGate

theorem unparse_parseTemplate {s : List Char} {segs : List Seg} (h : parseTemplate s = some segs) :
    unparse segs = s := sorry

theorem parseTemplate_text_no_braces {s t : List Char} {segs : List Seg}
    (h : parseTemplate s = some segs) (ht : Seg.text t ∈ segs) : '{' ∉ t ∧ '}' ∉ t := sorry

theorem parseTemplate_text_nonempty {s t : List Char} {segs : List Seg}
    (h : parseTemplate s = some segs) (ht : Seg.text t ∈ segs) : t ≠ [] := sorry

end DoseGate
