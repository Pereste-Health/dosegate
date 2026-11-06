# Response to the seventeenth round of review

Section names refer to paper/paper.md. The math reviewer accepted the manuscript. The health literacy and computer science reviewers each asked for one required change, and both are made.

## Health literacy review

Required item:

- Reading grades for the Claude runs: confirmed from eval/data/describe.json. The Model dependence paragraph now gives the median Flesch-Kincaid grade of released slot text for all five runs (3.6, 3.1, 3.4, 3.9, and 4.0) and of their free daily text (3.8, 5.5, 6.0, 3.5, and 3.3), and says that released text read at a lower grade than free text for the three open models, by only 0.2 grade for Qwen3.5-4B, and at a higher grade for both Claude runs, so the layer does not by itself make text easier to read. The sentence on the formula's instability for short texts is kept.

Recommended items are noted for a later revision.

## Computer science review

Required item:

- Reference 7 in Related work: confirmed from the arXiv abstract of 2602.20064, which presents a lambda calculus with a noninterference theorem and a verified interpreter that is itself the harness that calls the model, not a check of each action. The sentence now says that one system (reference 6) checks each agent action against a formal compliance policy before it runs, and another (reference 7) proves information-flow guarantees about a verified interpreter that runs the agent. The next sentence now says "differs from these systems", since it follows a list of five.

Recommended items are noted for a later revision.

## Math review (accept)

No required items. Recommended items are noted for a later revision.

## Changes made

- paper/paper.md: Results, Model dependence (reading grades); Related work, Verified guards paragraph.
