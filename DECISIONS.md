# Decision log — F1 Podium Prediction (Milestone 1)

Every choice we made, why we made it, and where the evidence is. Each decision has an ID. In the notebook the same ID appears as a 🔶 callout in the markdown and as `# DECISION Dx → see DECISIONS.md` in the code.

**How to use this file in the evaluation:** for any step an evaluator asks about, find the decision here, say the *why*, then open the notebook section listed under *Evidence* to show the plot or number.

Each decision is tagged:
* **[EDA]**: hypothesis-driven; an exploratory plot or table led to it.
* **[EXP]**: empirical; we tried alternatives and kept the one that scored better on **validation** (never test).
* **[DOMAIN]**: follows from how Formula 1 works or from the brief's rules.

A rule we followed everywhere: **the test seasons (2022–2024) never decide anything.** Test numbers are reported next to validation numbers for completeness only.

---

## Data cleaning

### D1 — Raw files are never modified **[DOMAIN]**
**Decision.** Raw CSVs are loaded as plain text into `raw`; every cleaning step works on copies in `df`. An MD5 fingerprint of each file is taken at the start and checked after cleaning.
**Why.** The brief requires raw files to stay immutable. Reading as text also lets the audit see `\N` exactly as written, before pandas guesses types. The fingerprint check proves immutability instead of just claiming it.
**Evidence.** §1, §2.1, §3.8 ("all 14 raw CSV files are byte-for-byte unchanged").

### D2 — Normalise spellings of nationalities and countries **[EDA]**
**Decision.** `"Argentinian "` (trailing space) → `"Argentine"`; circuit country `"United States"` → `"USA"`; HTML codes turned back into characters (constructor `"Lotus-Pratt &amp; Whitney"` → `"Lotus-Pratt & Whitney"`).
**Why.** A code check (not manual inspection) found one value with a trailing space and two spellings of the USA; a scan of every text column of every table found one HTML code. Left alone, they would split one country into two groups in the home-race question (Q2). Counts: nationalities 43 → 42, countries 35 → 34.
**Evidence.** §2.4 (detection), §3.2 (counts after cleaning).

### D3 — Explicit status → category mapping **[DOMAIN]**
**Decision.** Every one of the 139 `status` labels (Kaggle version of the dataset) is assigned to exactly one category by an explicit list (an assertion fails if a label is missing or listed twice): `finished` (incl. *Not classified*: running at the flag), `did_not_qualify`, `withdrawn`, `mechanical`, `accident_driver`, `regulation`, `team_operational` (Wheel nut, Fuel rig, Refuelling) and `ambiguous`.
**Why.** The brief defines mechanical as "a component of the car failed", excluding crashes, driver causes and regulation decisions. A label is `mechanical` only if it names a failed component. Damage that is usually caused by contact or by the pit crew (tyres, wheels, wings, undertray, debris, punctures) is `ambiguous`, so tyre, wheel and wing labels are treated consistently. "Withdrew" is decided per row (D6): if the car took the start it is an unknown in-race retirement (`ambiguous`), otherwise `did_not_start`.
**Alternatives considered.** A catch-all "everything else is mechanical" (our first version) — rejected, because it silently classified 70 labels nobody reviewed, and put rear wings in a different group from front wings.
**Evidence.** §3.4 prints the full mapping with row counts; Q3 shows the answer with the strict and the broad (+ ambiguous) definition.

### D4 — Duplicate (raceId, driverId) rows: keep the car the driver started in (the car only he is recorded in), else the lowest `resultId` **[EXP]**
**Decision.** When a driver has two rows in one race (shared drives, 1950–1978), keep the car **only he** is recorded in, if exactly one of his cars is like that; otherwise keep the row with the lowest `resultId`.
**Why.** In a mid-race takeover the driver gets a second row for the team-mate's car, a copy of that car's grid slot and result. That car also lists its original driver, while the car he started in lists only him. When this does not single out one car (team-mates who swapped cars, so both cars list two drivers), the lower `resultId` is the best guess: for every non-Indy pair it lies inside the race's normal block of entries (the driver's own car), while the second row was often appended later (co-driver credit). We compared three rules on integrity checks a clean table must pass:

| rule | races with > 3 podium rows | drivers sharing one car (affected races) |
|---|---|---|
| A: keep best `positionOrder` (team's first version) | 15 | 121 |
| B: keep own entry (lowest `resultId`) | 2 | 36 |
| **C: car only he is recorded in, else B** | **1** | **30** |

All rules remove the same rows (67 outside the Indianapolis 500; 91 in total with it); they differ in which row survives. Rule A credits a shared car's result to both drivers (1957 British GP: Moss *and* Brooks "won"); A and B differ in 15 podium labels. C differs from B in four pairs: Ascari (1951 French GP), González (1954 Belgian GP) and Moss (1961 British GP) took over a team-mate's car after their own failed, and B kept the taken-over car with the team-mate's grid slot and result (Ascari "started 6th and finished 2nd" instead of starting 3rd and retiring); Greene (1962 British GP) started in neither car and is removed by D6 either way. One podium label changes (Ascari's).
**Alternatives considered.** Keep the row with the **lowest grid slot** (our stage-A notebook), on the idea that the best grid slot is the car the driver started in. Rejected: `grid`, `laps` and the result belong to the **car**, not the driver. In a car swap both drivers have a row in both cars (1957 British GP: Moss and Brooks each have a row in car #18 from grid 1 and in car #20 from grid 3), so "lowest grid" can give a driver his team-mate's car (Brooks 1957).
**Limitation we accept.** Where C falls back to the lowest `resultId` (mostly car swaps), the data does not say which car a driver started in. One 1950s race still has four podium rows (1955 Argentine GP: Farina and Maglioli are both credited with the 3rd-placed car). Official records credit a shared result to both drivers (Ascari's shared 2nd place in 1951); we count the car the driver started in. All affected rows are before 1965, outside the training window.
**Evidence.** §3.5 (Moss/Brooks example, resultId-block check, comparison table and plot, table of the four pairs where C and B differ).

### D5 — Exclude the Indianapolis 500 (1950–1960) **[DOMAIN + EDA]**
**Decision.** Drop races named exactly "Indianapolis 500" (381 rows). The unrelated Indian Grand Prix (2011–2013) stays.
**Why.** It counted for the championship, but it was a separate competition: an American oval race run to different rules, with its own drivers. Of 107 Indy drivers only 4 ever started another championship race (2 of its 24 podium finishers), so its rows say nothing about Grand Prix podiums. Keeping it would also distort the data in two ways:
* **It inflates field sizes.** `results.csv` lists 55 entries for the 1954 Indianapolis 500 (35 on average over its 11 editions), against 22 on average at the other championship races of 1950–1960 (largest 36). Bigger fields lower every podium rate and change `field_size` and `grid_pct` for the 1950s.
* **It would distort the home-race analysis (Q2) for American drivers.** 380 of its 381 rows are American drivers racing in the USA, more than three times the 120 such rows at every other race in 75 seasons. With it, "American driver at home" would mostly mean "an Indy specialist at Indianapolis", not a Grand Prix driver at his home Grand Prix.

No effect on the model (trains from 1994).
**Evidence.** §3.6 (overlap statistics, entry-list sizes, American drivers racing in the USA).

### D6 — Keep exactly the cars that were on the grid at the prediction cutoff **[DOMAIN + EDA]**
**Decision.** Remove (a) drivers who **failed to qualify** (status Did not qualify / Did not prequalify / 107% Rule, or `positionText` F, with 0 laps) — 1,365 rows; and (b) entries **never on the grid** (no grid slot, no qualifying row, 0 laps) — 207 rows. **Keep everyone else**, including drivers who qualified but did not take the start (e.g. Leclerc on pole at Monaco 2021; the 14 cars that withdrew after the formation lap at the 2005 US GP) and drivers labelled "Withdrew" who actually raced.
**Why.** The unit of analysis is "one driver entering one race" and the prediction is made **after qualifying**. At that moment failed qualifiers are already out, but a qualified car that later fails to start is still a car we must predict for. Our first version dropped every "Withdrew" and every `W`: that used information from **after** the cutoff and removed exactly the "pole-sitter does not podium" cases, and it also dropped drivers who raced. Now kept: 137 cars that were on the grid but did not take the start (76 of them from 1994 on), and 23 rows labelled "Withdrew" that completed laps (e.g. Magnussen, 2020 Turkey, 55 laps).
**Evidence.** §2.2 plot (c) (what grid-0 rows are, per era); §3.6 (counts, the kept non-starters listed).

### D7 — Starting position: re-rank the grid; pit-lane start = behind the last slot + flag **[EDA]**
**Decision.** `grid_clean` = rank of the grid slot among the cars kept in that race (1 … number of cars). Pit-lane starters (raw grid 0 and took the start) are all set to the last slot (= `field_size`) and flagged `pit_lane_start = 1`; a qualified car without a grid slot (did not start) gets its qualifying position. `field_size` = number of cars on the grid.
**Why.** Raw grid 0 for a driver who raced means a pit-lane start; left as 0, every model reads it as "better than pole". And in old seasons the raw grid numbers have holes and ties (1981 German GP: no slots 19, 20, 24, 25, 27, two cars on 17, the last of 24 starters on grid 28; in a few races the holes are slots of cars removed in D6), so a car could have a slot beyond the number of cars actually on the grid (13 raw rows even exceed the number of entries). After re-ranking, `grid_pct` is always within 0–1 (asserted). Caveat: for raw grid 0, telling a pit-lane starter from a car that never started uses the laps column, which is post-race information; this affects a handful of rows.
**Evidence.** §3.7 (assert `1 ≤ grid_clean ≤ field_size`), §4 grid histogram before/after, 73 pit-lane starts flagged.

### D8 — Target = `positionOrder ≤ 3` **[DOMAIN]**
**Decision.** `podium = 1` if `positionOrder ≤ 3`; `positionOrder` is excluded from features.
**Why.** The brief's definition; `positionOrder` is filled for every row (`position` is empty for unclassified drivers).
**Known limitation.** In a few old races a disqualified driver's position was left vacant (1983 Brazilian GP: 2nd place vacant), so the officially 4th-placed driver has `positionOrder = 3`.
**Evidence.** §3.7 (1,113 races with exactly 3 podium rows, 1 with 4 — the D4 limitation).

---

## Data-engineering questions

### D9 — Q1 set-up **[DOMAIN + EDA]**
**Decision.** Front row by *grid* (slot 1–2, cars that did not start count as failed conversions) and by *qualifying* (1st–2nd) are both computed and ranked. Grid ≠ qualifying cases are split into penalties and **2021–22 sprint weekends** (where the sprint set the grid). Periods 2003–2013 vs 2014–2024; circuits need ≥ 8 front-row starts in both periods. Every rate has a 95% Wilson interval; a chi-square test checks whether circuits differ at all; the rank correlation gets a bootstrap interval; a sensitivity check uses 1950–2013 as the earlier period.
**Why.** The brief asks to distinguish qualifying from grid and to say whether the ranking changes. 2003 is the first season with complete qualifying data, so both definitions use the same rows. With 8–24 starts per circuit, intervals and tests are needed to know whether a ranking difference is real.
**Why a minimum of 8 starts.** Every race has 2 front-row cars, so 8 starts means the circuit hosted at least 4 races in that period. A rate from very few starts is mostly luck: with 2 starts it can only be 0%, 50% or 100%. The value is a judgement call between keeping more circuits and having steadier rates. 8 keeps 17 circuits; 10 (our stage-A notebook) keeps 14. The rank correlation between the periods depends on that choice: 0.08 with 4, 0.21 with 8, 0.35 with 10 and 0.49 with 12. That instability is itself evidence that the circuit order is not solid.
**How to read a rank change ("Monza from joint 1st to 12th").** Each period ranks the circuits by their conversion rate.
* **Monza:** in 2003–2013, 17 of its 22 front-row cars finished on the podium (77%), tied with Monaco for the best rate, so it was joint 1st. In 2014–2024, 16 of 22 did (73%) and 11 circuits did better, so it was 12th. It fell 11 places because of **one podium fewer**: all circuits sit between 58% and 89%, so a single result reorders the list.
* **Yas Marina:** went from 6 of 10 (60%, 13th) to 19 of 22 (86%, 3rd).
**Result.** Overall conversion rose 68.0% → 75.9% (p = 0.013); circuits are not distinguishable in either period (p = 0.99 / 0.80), ρ = 0.21 (CI −0.40 to 0.50), so a real change in the circuit ranking cannot be shown. Penalised front-row qualifiers podium 28%, front-row starters 73%.
**Evidence.** §5 Q1.

### D10 — Q2 set-up **[DOMAIN + EDA]**
**Decision.** Explicit nationality → country mapping; home = the country the circuit is in (not the race name). A driver with two nationalities (American-Italian, Argentine-Italian) is at home in **either** country. The same rule builds the `home_race` feature. Main estimate: home vs away within grid bucket (1 / 2–3 / 4–6 / 7–10 / 11+) × era (1950–79 / 1980–2013 / 2014–24), weighted by home starts, 95% interval from 1,000 race resamples. Robustness: grid-only control, logistic regression `podium ~ home + grid slot + era` with race-clustered standard errors, front of grid only, modern era only.
**Why.** A driver with two nationalities can be at home in both countries; mapping him to the first one only would call a home race "away". In this dataset that changes one start (Alfonso Thiele, American-Italian, 1960 Italian GP). The brief asks to compare drivers from similar grid positions. Era is added because podium rates per grid slot differ by era (§4). Resampling races respects that rows from one race are not independent.
**Result.** Raw −2.1 pp (one-off local entrants: 13.1% of home starts vs 1.4% of away starts come from drivers with ≤ 5 career starts) → −0.8 pp (CI −2.1 to +0.3) controlled; odds ratio 0.93 (0.79–1.11). No evidence of a home advantage; for 2014–2024 alone the interval is wide (−5.9 to +2.8).
**Evidence.** §5 Q2.

### D11 — Q3 set-up **[DOMAIN]**
**Decision.** Rate = mechanical retirements ÷ **race starts** per `constructorId` and period; cars that did not take the start are not race starts. Strict (`mechanical`) and broad (+ `ambiguous`) rates; only constructors with ≥ 30 starts; 95% Wilson intervals; chi-square test of team differences per period.
**Why.** The brief's definition ("a race start that ended early because a component failed"). A renamed team is a new entry in the data, so it appears separately. Below 30 starts one or two failures swing the rate too much.
**Result.** 8.9% → 5.5% of starts. Top 2014–2021: Caterham 21.2%, Lotus F1 17.3%, Toro Rosso 16.1% (teams differ, p < 0.001). Top 2022–2024: Alfa Romeo 12.5%, Alpine 10.4% (team differences borderline, p = 0.052). The broad rate keeps the 2014–2021 top five and Alfa Romeo's first place; below that the 2022–2024 order depends on labelling. A second check counts only failures after at least one lap, because the data codes some pre-start failures as 0-lap retirements; the top two in both periods stay the same.
**Evidence.** §5 Q3.

---

## Features

### D12 — Sprint results are not used as features **[DOMAIN]**
**Decision.** No feature from `sprint_results`, except as the reference slot for `grid_penalty` on 2021–22 sprint weekends (D15).
**Why.** Technically pre-race, but sprints exist only from 2021: they are absent from every training season (1994–2019), so the model could learn nothing from them. In 2021–22 the sprint result *was* the grid, which `grid_pos` already holds. The standings we use (from the previous race) already include earlier weekends' sprint points.
**Evidence.** §6.4.

### D13 — Standings come from *before* the race **[DOMAIN]**
**Decision.** For race N, join the standings published after the **previous race of the same season** via an explicit `raceId → prev_raceId` table; for a season opener use the **previous season's final standings**. Features: points as a share of the leader's points, rank, and wins as a share of the races run so far. Entries missing from the previous table get 0 points, no wins and the rank after the last ranked entry. Championship exclusions (Schumacher 1997, McLaren constructors 2007) were decided at or after the end of the season, although the data flags McLaren as excluded in every 2007 table. So in-season tables are used as published (McLaren was leading in mid-2007); only a previous season's **final** table used for an opener applies the exclusion (0 points, never the leader).
**Why.** The standings row for race N already contains race N's points: leakage (Verstappen, 2023 Belgian GP: 314 points after vs 281 before). An explicit lookup handles drivers who skipped a race. Points systems (8, 9, 10, 25 for a win) and season lengths (7–24 races) changed, so shares and ranks compare across eras where raw points and win counts do not.
**Why there is no `season_opener` feature.** At an opener the six standings features come from a whole-season table rather than from a few races, so we first gave the model a flag `season_opener` to tell the two cases apart. We removed it, because it cannot help a podium prediction:
* **It carries no signal by itself.** Every race has exactly three podiums, opener or not, so knowing that a race is the first of the season does not change anyone's chance (in an earlier version of the notebook its standalone AUC was 0.500).
* **The standings mean the same thing in both cases.** Whether they come from last season's final table or from this season's table, they describe how strong the driver and the team are. If anything the full-season table is the more reliable summary, so the model has no reason to read them differently.
* **Our inference model could not use it anyway.** A logistic regression can only add the same constant to every opener's log-odds; it cannot use the flag to re-weight the standings features unless an explicit interaction is built.
* **There is little to learn from.** Openers are about 1 race in 20 (about 26 of the 470 training races), too few for a flexible model to learn a reliable opener-specific pattern; a tree model could instead split on the flag by chance and overfit.
* **It describes our pipeline, not the race.** The flag records *where a feature value came from*, not anything about the driver, the car or the race. Such bookkeeping belongs in the code (it still decides which table is joined), not in the model's inputs, where it only adds an extra column to explain.
* **The measurement agreed.** It was measured in an earlier version of the notebook: with the flag in the model, removing it changed validation PR-AUC by +0.0001 (95% interval −0.001 to +0.002) and its permutation importance was 0.0001. The flag was then removed, so no cell of the current notebook reruns this test; the reasons above stand on their own.
**Evidence.** §6.4: the Verstappen check and an assertion that every `prev_raceId` is strictly earlier.

### D14 — Form = rolling windows over past races **[EDA + DOMAIN]**
**Decision.** Driver: podium rate and average finish (rank among the cars on the grid, as a fraction of the field) over the previous 5 races. Constructor: the same over its previous 5 races (both cars), plus mechanical-failure rate over its previous 10 races. `shift(1)` before `rolling()`; windows carry across seasons; constructor form follows `constructorId`, so a renamed team starts with no history (the dataset description's rule: renames reset history).
**Why.** §4 showed one constructor often dominates a season; Q3 showed reliability differs by team. `shift(1)` keeps the current race out of its own window. Constructor features are computed per (constructor, race) first, so a teammate's *current* result never leaks in. 5 races smooths one bad weekend but still reacts within a season; failures are rarer, hence 10.
**Result after training.** The ablation (§10) finds no measurable contribution of form once standings are present; it is kept because removing it does not improve validation either (D30).
**Evidence.** §6.5: a hand-recomputed value matches the feature (assertion).

### D15 — Qualifying features **[DOMAIN]**
**Decision.** `quali_position`; `quali_gap_pct` = the driver's **Q1** lap vs the fastest Q1 lap of that race, in % (laps more than 20% off are not a real attempt and become missing: 10 of 10,338); `grid_penalty` = grid slot − reference slot, where the reference is the qualifying position, or the **sprint result** on 2021–22 sprint weekends. Missing qualifying stays NaN in the table; the pipeline imputes it with a missing indicator (D19). Raw lap times are not features.
**Why.** Raw lap times depend on the circuit length (Monaco ~70 s vs Spa ~105 s). Q1 is the only session every driver ran; "best lap of any session" mixed track conditions and, in 2006–09, race-fuel Q3 laps. Q1 showed penalised front-row qualifiers podium far less often (28% vs 73%), so the penalty is its own feature; measuring it against the sprint result stops sprint overtakes from looking like penalties.
**Evidence.** §6.3 (gap distribution and cutoff), §6.7.

### D16 — Five feature groups **[EDA]**
**Decision.** grid (3), qualifying (3), standings (6), form (5), context (4) = 21 features. (A seventh standings column, `season_opener`, was removed; see D13.)
**Why.** Each group answers a different question (where does he start? how fast was he? how strong is the car/driver this season? recently? anything else?), and the ablation needs named groups.
**Evidence before training** (§6.7, training window 1994–2019): starting position 0.905 standalone AUC; most standings and form features 0.85–0.88, constructor versions mostly at or above the driver versions (rank is the exception); win shares 0.75–0.82; context, flags and `con_mech_rate_last10` 0.50–0.69.
**Evidence after training** (§10): only "grid group only" loses clearly (−0.06 to −0.10); single groups substitute for each other; grid is irreplaceable on test.

### D17 — Training window 1994–2019 **[DOMAIN, checked by EXP]**
**Decision.** Train on seasons 1994–2019 only.
**Why.** 1994 is the first season with qualifying data, and the sport before it differs strongly (bigger fields, frequent breakdowns, weaker grid effect, §4). The empirical check (§8.4) on three validation periods finds no consistent winner: 1980 is best for 2016–17 and 2018–19 and 1950 for 2020–21, with 1994 within about 0.001 of the best in the first two periods and 0.014 behind in 2020–21, where the lead comes from gradient boosting alone (differences within the noise of a 39-race validation set); 2003 is worst in all three. Differences between 1950, 1980 and 1994 are within noise, so the choice rests on the domain argument.
**Note.** Our first version chose the window from one validation period and one gradient-boosting run; a reviewer showed that result flipped with the random seed (because of scikit-learn's automatic early stopping on a random 10% split). Early stopping is now off (D28) and the check uses three periods.
**Evidence.** §6 (constants), §8.4 table and plot.

---

## Splitting, metrics and preprocessing

### D18 — Split by season **[DOMAIN]**
**Decision.** Train 1994–2019, validation 2020–2021, test 2022–2024. Models are fitted once on the training seasons and frozen.
**Why.** A random split would put rows from the same race and from the future into training. A time split copies real use (predict the next race from the past) and tests the 2022 rule change. 2020 was an unusual COVID season (17 races, repeated venues) and validation is used for several choices, so validation scores are slightly optimistic; test is the only unbiased number.
**Evidence.** §7 split summary (train 10,156 rows / 470 races, podium rate 13.9%; validation 780 / 39 and test 1,359 / 68, both 15.0%).

### D19 — Median imputation + missing indicators; scaling for LR/NN; split first, derive before impute **[EXP + DOMAIN]**
**Decision.** `SimpleImputer(median, add_indicator=True)`; `StandardScaler` for logistic regression and the network; order impute → scale; all fitted on the training set inside a `Pipeline`; derived features (`grid_penalty`) computed from real values before imputation.
**Why.** Missing values are structural, so an indicator lets the model learn from "missing". The median is robust to skew. Linear models and neural networks need comparable scales; trees do not.
**Experiments (§8.1–8.3).**
* **E1, split → fit vs fit → split:** scores practically identical, but medians and means shift when future seasons are included (e.g. `experience` median 62 → 71), so the second order uses information unavailable in 2019. Correct order kept.
* **E2, impute → scale vs scale → impute, for LR and the NN (32 → 16):** visibly different `quali_gap_pct` distribution; LR validation PR-AUC moves by < 0.001 (0.7233 vs 0.7230); for the NN impute → scale is higher on validation (0.7290 vs 0.7204; test, for reference only: 0.7054 vs 0.6943), a single run per order. Impute → scale kept: the standard order, and the model sees exactly mean 0 / std 1.
* **E3, derive → impute vs impute → derive:** imputing first invents 1,808 penalty values; validation PR-AUC +0.002 (noise), ROC-AUC and log-loss worse. Derive first.
**Evidence.** §8 (effect table and plot), §8.1–8.3.

### D20 — Class weights: unweighted except the random forest **[DOMAIN + EXP]**
**Decision.** Logistic regression, gradient boosting and the network: **unweighted**. Random forest: weighted (`balanced_subsample`), chosen together with leaf size on validation, but the best weighted and unweighted forests are only 0.002 apart, inside the forest's seed spread, so that part is noise.
**Why.** Weights make the rare class count more but inflate every probability, and the inference function returns a probability. The validation Brier scores (§9.4) show it: 0.106 for the weighted forest against 0.067 for the unweighted logistic regression (lower is better). The calibration plot in §9.4, drawn on test for reference only, shows the same: the weighted forest predicts far above the real podium rates, the logistic regression lies close to the diagonal. (Our first version justified weights with test results; that was removed.)
**Evidence.** §9 (D20 callout), §9.1 (forest grid), §9.4 (validation Brier; the calibration plot is on test, for reference only).

### D21 — Metrics **[DOMAIN]**
**Decision.** ROC-AUC, PR-AUC, F1, precision, recall ("five metrics"), plus Brier score and log-loss (calibration), race top-3 hit rate and predicted podiums per race, on train, validation and test. Primary: PR-AUC. Secondary: ROC-AUC.
**Why.** Podiums are rare; PR-AUC focuses on the top of the ranking and its random level is the base rate (0.15) rather than 0.5. ROC-AUC shows overall separation. The inference function returns a probability, so calibration is checked too. The model tables in §9.4 show the Brier score; log-loss is computed for every model and saved in `model_comparison.csv` in the output folder, and the §8 experiment tables show it.
**Evidence.** §7.1, §9.4.

### D22 — Threshold = maximum F1 on validation **[DOMAIN]**
**Decision.** Each model's threshold maximises F1 on 2020–2021 and is applied unchanged to train and test.
**Why.** The brief forbids choosing thresholds on test. F1 balances missed podiums against false alarms.
**Evidence.** `best_f1_threshold` (§7.1); threshold column in the §9.4 tables.

### D23 — Uncertainty: race-level bootstrap **[DOMAIN]**
**Decision.** Every important comparison gets a 95% interval from 1,000 resamples of the races of a split (paired: both models scored on the same resampled races).
**Why.** Validation has 39 races; a difference of 0.01 PR-AUC can be luck. Resampling races (not rows) respects that rows from one race are not independent.
**Evidence.** §7.1 (`race_bootstrap`), used in §9.4 and §10.

---

## Modeling

### D24 — Model selection: best on validation, but only if it beats the baseline significantly **[DOMAIN, checked by EXP]**
**Decision.** Rank candidates by validation PR-AUC (mean over seeds for the forest and the network). Use the best one only if the paired bootstrap interval of *best − baseline* lies entirely above 0; otherwise use the baseline.
**Result.** Best on validation: tuned gradient boosting 0.736 (random forest 0.734, seed mean); baseline logistic regression 0.723; difference interval −0.022 to +0.043 → **the logistic regression is used for inference and explanations.** On test: LR 0.709, RF 0.712, GBM 0.712 — all within each other's intervals.
**Why.** The brief asks to justify complex models against the baseline. Our first version picked the random forest because it was 0.0004 ahead, a margin that flipped with the random seed. The rule makes the choice robust and follows "complexity must earn its place". A bonus: logistic regression is deterministic and well calibrated, so its results do not change between environments.
**Evidence.** §9.4.

### D25 — Shallow neural network: 2 hidden layers (32 → 16), built with Keras **[DOMAIN]**
**Decision.** Input: the 29 imputed and scaled columns → Dense 32 ReLU → Dense 16 ReLU → 1 sigmoid output (the podium probability). Each hidden layer has dropout 20% and an L2 penalty of 1e-4. Loss: binary cross-entropy, unweighted (D20). Optimiser: Adam, learning rate 0.001, batches of 128. Training stops when validation PR-AUC has not improved for 15 epochs, and the best epoch's weights are kept. Trained 3 times (seeds 42, 1, 2); the seed-42 network is the one reported.
**Why.** The brief asks for a shallow network (roughly 1–2 hidden layers) and allows a standard library such as Keras. Two small layers give only 1,505 weights, small compared with ~10,000 training rows. Dropout (switching off 20% of the units at random while training), L2 (large weights cost extra) and early stopping all limit overfitting. The 3 seeds show how much the result depends on the random starting weights: validation PR-AUC 0.726–0.729.
**Evidence.** §9.3 (weight count, learning curves, seed table).

### D26 — Explain the inference model on the test seasons; cross-check with a tree model **[DOMAIN]**
**Decision.** Permutation importance (per feature and per group) and SHAP (exact LinearExplainer) for the logistic regression; mean-|SHAP| cross-check for tuned gradient boosting; local SHAP waterfall + LIME (5 seeds) for Verstappen, 2023 Belgian GP; SHAP for the most confident wrong prediction. Computed on 2022–2024.
**Why.** We explain the model whose predictions a user sees. Explaining chooses nothing, so the test set can be used. LIME's poor local fit here (R² ≈ 0.3, local prediction 0.25–0.28 vs model 0.81) is reported, which is why SHAP is the main local explanation. Explanations describe what the model relies on, **not causes**.
**Evidence.** §11.

### D27 — Inference function **[DOMAIN]**
**Decision.** `predict_podium(record)` requires `grid_pos` and `field_size`, maps raw grid 0 to a pit-lane start (D7), derives `grid_pct` and `grid_penalty`, fills other missing values through the trained pipeline (median + indicator for the 8 columns that had missing values in training), validates ranges, rejects unknown feature names, and reports the missing features.
**Why.** The brief asks for a demo on complete and partially-missing records. Reusing the training pipeline guarantees the same treatment as in training; checks stop typos and impossible values from being silently accepted. The demo shows honestly that missing-value patterns never seen in training (form missing for a veteran) give unreliable outputs.
**Evidence.** §12 (demos and the breakdown table).

### D28 — Gradient boosting: early stopping off; hyperparameters by grid search **[EXP]**
**Decision.** `early_stopping=False` for every gradient-boosting model; tuned model chosen from 54 combinations (learning rate 0.01/0.03/0.1 × trees 50/100/300 × leaves 7/15/31 × min leaf 20/80) on validation PR-AUC → learning rate 0.01, 100 trees, 7 leaves, min leaf 80.
**Why.** scikit-learn's default turns early stopping on above 10,000 rows and holds out a *random* 10% of rows, mixing drivers of the same race (against D18) and making results depend on the seed and the exact number of rows. Without it, the model is deterministic. The best point is at the edge of the grid (slowest, simplest), consistent with a simple model being enough.
**Evidence.** §8 (`make_hgb`), §9.2 (grid search heatmap, learning curve).

### D29 — Random forest and logistic-regression settings **[EXP / DOMAIN]**
**Decision.** Random forest: 400 trees, `max_features="sqrt"`, `min_samples_leaf` and class weights chosen on validation from 5 × 2 options → 50 and `balanced_subsample`; the training score reported is the out-of-bag estimate. Logistic regression: scikit-learn default L2 strength (C = 1).
**Why.** Leaf size controls memorisation; small leaves (5) score worse on validation (0.703–0.707) than 50 (0.728–0.732). The in-sample training score of a forest is misleading, the out-of-bag score is honest. With ~10,000 rows and 29 columns the default L2 penalty is mild and the baseline needs no tuning to make the point.
**What the settings mean.**
* `n_estimators = 400`: the number of decision trees in the forest. The forest's probability is the average of the 400 trees.
* `min_samples_leaf`: the smallest number of training rows a leaf (an end point of a tree) may hold; a split that would leave fewer rows on either side is not made. The leaf predicts the share of podiums among its rows. Small leaves (5) hold a handful of rows, often from the same few races, so the tree memorises noise; large leaves (100) average many rows, so predictions are smoother but less detailed. 50 was best on validation.
* `max_features = "sqrt"`: at every split a tree may only look at a random subset of the columns, of size √(number of columns). The forest sees 29 columns (21 features + 8 missing indicators), so each split chooses among 5 random columns. This makes the trees different from each other (otherwise every tree would split on `grid_pos` first), and averaging different trees is what reduces the variance.
* `class_weight = "balanced_subsample"`: podium rows count more in each tree's training sample, so that both classes weigh the same (see D20).
* `C` (logistic regression): the inverse of the penalty strength, C = 1 / λ. The model minimises log-loss plus an L2 penalty that pulls the weights toward 0. A small C (e.g. 0.01) means a strong penalty, small weights and a simpler model; a large C (e.g. 100) means almost no penalty, so the weights fit the training data freely. C = 1 is scikit-learn's default.
**Evidence.** §9.1.

### D30 — Ablation rule: remove a group or feature only if that significantly improves validation **[EXP]**
**Decision.** After the ablation, a group or single feature is removed from the inference model only if removing it raises validation PR-AUC with a 95% interval entirely above 0.
**Result.** No group or feature qualifies, so all 21 features stay. Removing `experience` alone even hurts significantly (−0.008), while removing the whole context group does not (age and experience carry opposite-signed weights that cancel). Form and context show no measurable contribution as groups, which we report.
**Why.** Decisions are taken on validation only (our first version kept form because of a *test* number; that was removed). With 39 validation races, a rule with an interval prevents reacting to noise.
**Evidence.** §10.
