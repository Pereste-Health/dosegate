import DoseGate
open DoseGate
def met : MedReq where
  id := "m1".toList
  active := true
  drug := "metformin".toList
  dose := some ⟨⟨500, 0⟩, DoseUnit.mg⟩
  timing := some ⟨2, 1, PeriodUnit.d⟩
  route := some Route.oral
  asNeeded := false
def show' (e : Except Block (List Char)) : String := match e with
  | .ok s => "OK: " ++ String.ofList s | .error b => "BLOCK: " ++ reprStr b
#eval String.ofList (fmtDec ⟨1250, 3⟩)
#eval String.ofList (fmtDec ⟨5, 1⟩)
#eval String.ofList (fmtDec ⟨100, 2⟩)
#eval String.ofList (fmtDec ⟨5, 4⟩)
#eval parseDec? "0.0005".toList
#eval show' (render {} [met] "Take {{dose:m1}} {{route:m1}} {{frequency:m1}}.".toList)
#eval show' (render {} [met] "Your plan: {{sig:m1}}.".toList)
#eval show' (render {} [met] "Take 2 tablets {{frequency:m1}}.".toList)
#eval show' (render {} [met] "Take 1{{dose:m1}}.".toList)
#eval show' (render {} [met] "Take {{dose:m2}}.".toList)
#eval show' (render {} [met] "Take {dose:m1}.".toList)
#eval show' (render {allow := ["911".toList]} [met] "Call 911 if faint.".toList)
#eval show' (render {} [met] "Take ５００ mg.".toList)
