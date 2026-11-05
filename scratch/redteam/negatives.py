from raw import *
import json
CH = json.load(open("chart.json"))
cases = [
 ("N1 half a tablet", "Take {{drug:m1}} {{dose:m1}}, half a tablet more."),
 ("N2 a couple", "Take a couple of {{drug:m1}}."),
 ("N3 fraction slash", "Take {{drug:m1}} 1/2 more."),
 ("N4 vulgar half", "Take {{drug:m1}} ½ more."),
 ("N5 x2", "Take {{drug:m1}} x2."),
 ("N6 q8h", "Take {{drug:m1}} q8h."),
 ("N7 fullwidth digits", "Take {{drug:m1}} ５００ more."),
 ("N8 zero width in mg", "Take {{drug:m1}} {{dose:m1}} m​g more."),
 ("N9 combining mark", "Take {{drug:m1}} ḿg."),
 ("N10 cyrillic homoglyph in word", "Тake {{drug:m1}} {{dose:m1}}."),
 ("N11 another one", "Take {{drug:m1}} another one."),
 ("N12 IU", "Take {{drug:m2}} IU."),
 ("N13 units per kg", "Take {{drug:m2}} units/kg."),
 ("N14 mL's", "Take {{drug:m1}} mL's."),
 ("N15 braces", "Take {{drug:m1}} {{dose:m1}} {note}."),
 ("N16 unknown field name", "Take {{dosage:m1}}."),
 ("N17 unknown id", "Take {{drug:m9}}."),
 ("N18 sig with route missing", "{{drug:m5}} {{sig:m5}}."),
 ("N19 two drugs one sentence", "Take {{drug:m1}} and {{drug:m2}}."),
 ("N20 dose slot without drug", "Take {{dose:m1}}."),
 ("N21 adjacent slots", "{{drug:m1}}{{dose:m1}}."),
 ("N22 stopped drug slot", "Take {{drug:m3}} {{dose:m3}}."),
 ("N23 frequency zero period 0.5 (chart fields)", "Take {{drug:m1}} {{dose:m1}} {{frequency:m1}}."),
 ("N24 negative ids", "Take {{drug:m1}} {{dose:m1}} {{drug:-1}}."),
]
for name, out in cases:
    rc, o, err, t = run(json.dumps({"bundle": CH, "output": out}, ensure_ascii=False))
    print(f"[{name}] rc={rc} {o[:160]}")
