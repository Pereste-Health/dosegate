from raw import *
import json
CH = json.load(open("chart.json"))
def go(out):
    req = json.dumps({"bundle": CH, "output": out}, ensure_ascii=False)
    rc, o, err, t = run(req)
    return rc, o
cases = [
 # frequency words
 ("F1 nightly for m1 (chart: twice a day)", "Take {{drug:m1}} {{dose:m1}} nightly."),
 ("F2 qd for m1", "Take {{drug:m1}} {{dose:m1}} qd."),
 ("F3 qod for m1", "Take {{drug:m1}} {{dose:m1}} qod."),
 ("F4 every other day for m1", "Take {{drug:m1}} {{dose:m1}} every other day."),
 ("F5 weekly for m1 (chart: twice a day)", "Take {{drug:m1}} {{dose:m1}} weekly."),
 ("F6 hourly for m4 (chart: every 4 hours as needed)", "Take {{drug:m4}} {{dose:m4}} hourly."),
 ("F7 as needed added to m2 (chart: scheduled daily)", "Take {{drug:m2}} {{dose:m2}} as needed."),
 ("F8 at bedtime for m1", "Take {{drug:m1}} {{dose:m1}} at bedtime."),
 ("F9 with meals for m2", "Take {{drug:m2}} {{dose:m2}} with every meal."),
 ("F10 m8 weekly as daily", "Take {{drug:m8}} {{dose:m8}} {{route:m8}} every day."),
 ("F11 m8 weekly as twice", "Take {{drug:m8}} {{dose:m8}} {{route:m8}}, bid."),
 ("F12 m2 qhs", "Take {{drug:m2}} {{dose:m2}} qhs."),
 # route words
 ("R1 insulin intravenously", "Take {{drug:m2}} {{dose:m2}} intravenously."),
 ("R2 insulin orally", "Take {{drug:m2}} {{dose:m2}} orally."),
 ("R3 insulin PO", "Take {{drug:m2}} {{dose:m2}} PO."),
 ("R4 insulin as a pill", "Take {{drug:m2}} {{dose:m2}} as a pill."),
 ("R5 metformin injection", "Take {{drug:m1}} {{dose:m1}} as an injection."),
 ("R6 warfarin injected", "Take {{drug:m5}} {{dose:m5}} injected."),
 ("R7 metformin via feeding tube", "Take {{drug:m1}} {{dose:m1}} via feeding tube."),
 ("R8 metformin under tongue", "Take {{drug:m1}} {{dose:m1}} under the tongue."),
 ("R9 heparin by mouth", "Take {{drug:m6}} {{dose:m6}} by mouth."),
 ("R10 heparin subcut via text no route", "Give {{drug:m6}} {{dose:m6}}, IM."),
 # amount words
 ("A1 tripled", "Take {{drug:m1}} {{dose:m1}}, tripled at night."),
 ("A2 twofold", "Take {{drug:m1}} {{dose:m1}}, twofold on Sunday."),
 ("A3 gms", "Take {{drug:m1}} {{dose:m1}} gms."),
 ("A4 mgs", "Take {{drug:m1}} mgs."),
 ("A5 IUs", "Take {{drug:m2}} IUs."),
 ("A6 ampoules", "Take {{drug:m2}} ampoules."),
 ("A7 fourth", "Take {{drug:m1}} {{dose:m1}}, plus a fourth more."),
 ("A8 onehalf", "Take {{drug:m1}} onehalf."),
 ("A9 semi", "Take {{drug:m1}} semi."),
 ("A10 several", "Take several {{drug:m1}}."),
 ("A11 pinch", "Take a pinch of {{drug:m1}}."),
 ("A12 the whole bottle", "Take the whole bottle of {{drug:m1}}."),
 ("A13 spoonful", "Take a spoonful of {{drug:m2}}."),
 ("A14 dose word", "Take a full dose of {{drug:m1}}."),
 ("A15 multiple word", "Take {{drug:m1}} {{dose:m1}} and then sixfold."),
 ("A16 glued unit caps", "Take {{drug:m1}} {{dose:m1}}, TWOmg more."),
 ("A17 glued 'ten'mg in one token", "Take {{drug:m1}} {{dose:m1}} and tenunits."),
 # drug name in text
 ("D1 Coumadin before slot", "Take Coumadin {{drug:m1}} {{dose:m1}}."),
 ("D2 Warfarin in text, metformin slot", "Take warfarin {{drug:m1}} {{dose:m1}}."),
 ("D3 negation", "Do not take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."),
 ("D4 stop instruction", "Stop taking {{drug:m1}}."),
]
for name, out in cases:
    rc, o = go(out)
    print(f"[{name}] rc={rc} {o}")
