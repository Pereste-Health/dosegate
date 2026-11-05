# Response to the second round of review

Code changes (commits 9f756f5 and d9cacde), all with regression tests, re-proved theorems, and a 20,000-request fuzz run in agreement:

- Sign rule: a slot is blocked when the model's text before it, with trailing spaces removed, ends in a minus or plus sign (`render_no_sign_before_slot` restated). "Take metformin - 500 mg" and "which is - 1000 mg a day" are now blocked.
- Vocabulary: "health", "important", and "plan" removed (67 words). "They are important for your health." is blocked.
- Completeness is now the default (`render_all_orders_named_default`); `--allow-omissions` turns it off. The one main-evaluation release that omitted an order (Qwen3.5-4B, slot daily, the hydrocodone case) is now blocked; no other decision on the 2,764 model outputs changed.
- The block reason `nonAscii` is renamed `disallowedCharacter`.
- A `dosegate fallback` command renders one instruction per active order through `render`, and returns an error when no order is active.

Health literacy reviewer:
1. Same-ingredient pairs: Table 3 has a new column counting faithful outputs that give two instructions for one ingredient (19 for version 2 and the comparison filter, 17 for version 2.1), the Abstract states the 17, the Daily totals paragraph uses the proposed wording, and the Limits paragraph names the pairs and their consequence. The rubric was not changed after labeling; the column was assessed afterwards from the requests, as the Labels paragraph says.
2. Omission: fixed in the code (completeness by default); Results report the version 2 omission and that version 2.1 blocks it.
3. Doses above common maxima: Results report 205 of 368 perturbed releases with the thresholds, and none of 499 natural releases.
4. Blocked output: the Design says the detail must never be shown to a patient; the fallback command exists; the Discussion paragraph is rewritten.
5. Vocabulary: fixed in the code.
6. "22 of 31": corrected.
Recommended items applied: Abstract free-text counts now give reader-confirmed numbers; "sliding" replaces "hold"; reading grades with sample sizes and caveats; as-needed orders, missing indication, missed-dose instruction, and brand name, and the chart-error example in Limits; the free-text rule was not exercised (Methods); decimal point sentence; N01 explained; sig defined.

Math reviewer:
1. Spaced sign: fixed in the code and proof.
2. "22 of 31": corrected.
3. Round-h1 first-reader labels: disclosed in Labels and Agreement.
Recommended items applied: related-name rule stated exactly; planted-error design; disclosure that version 1 outputs on both halves were examined before version 2; 41 repeated-instruction misstatements; intervals in every Table 2 cell; Llama reading grade only for 34 texts; value slot defined; dose code system wording; daily total rule restated; reason renamed; Abstract wording on version 1's development result; 251 distinct orders; rounding rule (the paper's percentages are now computed with half-up rounding in eval/models.py).

Computer science reviewer: the three fixes named in the summary (spaced sign, the double count, single-read labels) are addressed above.
