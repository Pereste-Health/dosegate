# Drug-name lexicon

`rxnorm_names.txt` holds every RxNorm ingredient (IN), precise ingredient (PIN), multiple ingredient (MIN), and brand name (BN), one name per line, lowercased and sorted. The input reader prints a drug name only if, lowercased, it equals one of these lines; the proved structural rule and the stop list still apply on top of this check.

Source: the RxNav REST API of the National Library of Medicine, `https://rxnav.nlm.nih.gov/REST/allconcepts.json?tty=IN+PIN+MIN+BN`, downloaded on 2026-11-07. RxNav reported RxNorm release 02-Nov-2026 (API version 3.1.357). The response held 27,369 concepts (IN 14,718; BN 5,114; MIN 3,849; PIN 3,688) with 27,369 distinct lowercased names. RxNorm names created by the National Library of Medicine are in the public domain; use of RxNav is subject to the NLM terms of service at `https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html`, and RxNorm itself to `https://www.nlm.nih.gov/research/umls/rxnorm/docs/termsofservice.html`.

`python3 data/build_rxnorm_names.py` downloads the current names again and rewrites the file; it prints the release and the counts. The file is embedded in the binary when `DoseGate/Lexicon.lean` is compiled, so run `lake build` after changing it.

`openfda-labels/` is unrelated to the lexicon.
