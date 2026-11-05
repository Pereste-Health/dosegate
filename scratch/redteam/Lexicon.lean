import DoseGate.Tokens
open DoseGate

def tok (s : String) : List Char := s.toList

#eval isDoseToken (tok "fivemg")
#eval isDoseToken (tok "tenmg")
#eval isDoseToken (tok "tenunits")
#eval isDoseToken (tok "onehalf")
#eval isDoseToken (tok "mg")
#eval isDoseToken (tok "ten")
#eval isDoseToken (tok "dbl")
#eval isDoseToken (tok "doubled")
#eval isDoseToken (tok "tripled")
#eval isDoseToken (tok "ii")
#eval isDoseToken (tok "gms")
#eval isDoseToken (tok "ampoules")
#eval isDoseToken (tok "iv")
#eval isDoseToken (tok "daily")
#eval (tokens "Take 5 fivemg, tenmg; mil-ligrams.".toList).map String.ofList
