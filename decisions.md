# Decisions log

One line per decision: **what we did → evidence (plot / number) → notebook section → owner**.
"An AI tool suggested it" is not evidence.

| # | Area | Decision | Evidence | Section | Owner |
|---|---|---|---|---|---|
| 1 | Loading | `\N` read as missing (`na_values=[r"\N"]`, `keep_default_na=False`) so strings like "NA" aren't swallowed | null counts with/without default NA list | §0 Setup | A |
| 2 | Reproducibility | global seed `SEED = 42` for numpy / random / sklearn / TensorFlow | — | §0 Setup | A |
