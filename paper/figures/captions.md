# Figure captions and placement for the JAMIA draft

These are ready to go into `paper/dosegate_jamia.md` after Parker's Word edits come back. Nothing here is in the draft yet.

## Placement

Figure 1 is cited at the end of the first sentence of Materials and Methods, "The layer" paragraph: "... stands for one field of the order with identifier `id` (Figure 1)".

Figure 2 is cited in the first sentence of Results, "Held-out and adversarial rounds": "Version 1 released 74 of 113 round h1 requests, and 38 misstated an order (Figure 2; Supplementary Table S5)."

The two citations add 3 words to the main text, which is at the 4,000-word limit. Planned cuts (3 words):

- "The model writes plain text in which" becomes "The model writes text in which" (1 word).
- "Three open models ran on one Apple M2 Max computer" becomes "Three open models ran on an Apple M2 Max" (1 word).
- "Each case received six generations from each open model" becomes "Each case received six generations per open model" (1 word).

## Figure 1 caption

Figure 1. How the layer handles one model output. The model writes words and slots; the layer fills each slot from the active order it names and releases the text only when every check passes. Otherwise it blocks, no model text reaches the patient, and a fallback command prints one line per active order through the same proved formatting code. The figure lists five of the layer's checks; Supplementary Table S1 lists the proved properties. Solid outlines mark code whose behavior is proved in Lean 4; the dashed outline marks the FHIR reader, which is tested but not proved.

## Figure 2 caption

Figure 2. Released outputs that misstate an order, by request set and filter. Version 1 was revised during the development requests, so its development count is not a held-out estimate; round h1 was written against version 1 after it was frozen, and round h2 against version 2 after it was frozen. Version 2.1 bars replay the saved requests after the later changes and are not held-out estimates. Comparison filter counts are from stored runs. Labels are from two Claude instances, with a third deciding disagreements; no clinician labeled any output. Table 2 gives the released totals and the other labels.

Source: `eval/data/labels_summary.json` (misstates_order for layer and baseline in development, h1, and h2); version 2.1 zeros from `eval/data/replay_v21/*_results.jsonl` as reported in Table 2.
