from raw import *
import json
CH = json.load(open("chart.json"))
def go(out, chart=CH):
    rc, o, err, t = run(json.dumps({"bundle": chart, "output": out}, ensure_ascii=False))
    return rc, o
cases = [
 ("T1 tid", "Take {{drug:m1}} {{dose:m1}} tid."),
 ("T2 roman ii times a day for daily m2", "Take {{drug:m2}} {{dose:m2}} ii times a day."),
 ("T3 roman ii before dose", "Take {{drug:m1}} ii {{dose:m1}}."),
 ("T4 iv roman", "Take {{drug:m1}} {{dose:m1}}, iv."),
 ("T5 SC route abbreviation for m1", "Take {{drug:m1}} {{dose:m1}} SC."),
 ("T6 IM for metformin", "Take {{drug:m1}} {{dose:m1}} IM."),
 ("T7 gm", "Take {{drug:m1}} {{dose:m1}} gm."),
 ("T8 hyphen split mil-ligrams", "Take {{drug:m1}} {{dose:m1}} mil-ligrams."),
 ("T9 up to", "Take up to {{drug:m1}} {{dose:m1}}."),
 ("T10 x prefix", "Take x {{dose:m1}} of {{drug:m1}}."),
 ("T11 resume stopped lisinopril", "Restart lisinopril as before, then {{drug:m1}} {{dose:m1}}."),
 ("T12 stopped drug revived with slot id of active", "Resume lisinopril {{drug:m1}}."),
 ("T13 fractional glued fourths", "Take {{drug:m5}} {{dose:m5}}, two fourths."),
 ("T14 dbl with slot", "Take {{drug:m5}} {{dose:m5}}, dbl."),
 ("T15 doubles", "Take {{drug:m1}} {{dose:m1}} and doubles on Sunday."),
 ("T16 tripling", "Take {{drug:m1}} {{dose:m1}}, tripling it on Sunday."),
 ("T17 at most", "Take at most {{drug:m1}} {{dose:m1}}."),
 ("T18 more", "Take {{drug:m1}} {{dose:m1}} and more if needed."),
 ("T19 approximately", "Take approximately {{drug:m1}} {{dose:m1}}."),
 ("T20 no-slot amount-free but misleading qualifier", "Take {{drug:m1}} {{dose:m1}}, as much as you like."),
 ("T21 drug with dose slot from another id", "Take {{drug:m1}} {{dose:m2}}."),
 ("T22 negation do not", "Do not take {{drug:m2}} {{dose:m2}}."),
 ("T23 multi sentence cross attribution", "Take {{drug:m1}} {{dose:m1}}. Coumadin: take {{drug:m5}} {{dose:m5}}."),
 ("T24 stopped med sig", "Resume {{drug:m3}}."),
 ("T25 warfarin with IV text", "Give {{drug:m5}} {{dose:m5}} IV."),
 ("T26 approx. split", "Take {{drug:m1}} approx. {{dose:m1}}."),
 ("T27 frequency missing from chart m5 but text", "Take {{drug:m5}} {{dose:m5}} every hour."),
 ("T28 heparin by mouth (route missing from chart? no: SC)", "Take {{drug:m6}} {{dose:m6}} by mouth."),
 ("T29 'on' route word", "Take {{drug:m2}} {{dose:m2}} into the vein."),
 ("T30 hlf", "Take hlf {{drug:m1}} {{dose:m1}}."),
]
for name, out in cases:
    rc, o = go(out)
    print(f"[{name}] rc={rc} {o}")
