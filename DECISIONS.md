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
**Limitation we accept.** Where C falls back to the lowest `resultId` (mostly car swaps), the data does not say which car a driver started in. One 1950s race still has four podium rows (1955 Argentine GP: Farina and Maglioli are both credited with the 3rd-placed car). Official records credit a shared result to both drivers (Ascari's shared 2nd place in 1951); we count the car the driver started in. All affected rows are before 1965. They lie inside the training window (D17), so the rule matters for the model too: rules A and B differ in 15 podium labels, B and C in 1 (Ascari, 1951), and C is the rule that keeps those labels right.
**Evidence.** §3.5 (Moss/Brooks example, resultId-block check, comparison table and plot, table of the four pairs where C and B differ).

### D5 — Exclude the Indianapolis 500 (1950–1960) **[DOMAIN + EDA]**
**Decision.** Drop races named exactly "Indianapolis 500" (381 rows). The unrelated Indian Grand Prix (2011–2013) stays.
**Why.** It counted for the championship, but it was a separate competition: an American oval race run to different rules, with its own drivers. Of 107 Indy drivers only 4 ever started another championship race (2 of its 24 podium finishers), so its rows say nothing about Grand Prix podiums. Keeping it would also distort the data in two ways:
* **It inflates field sizes.** `results.csv` lists 55 entries for the 1954 Indianapolis 500 (35 on average over its 11 editions), against 22 on average at the other championship races of 1950–1960 (largest 36). Bigger fields lower every podium rate and change `field_size` and `grid_pct` for the 1950s.
* **It would distort the home-race analysis (Q2) for American drivers.** 380 of its 381 rows are American drivers racing in the USA, more than three times the 120 such rows at every other race in 75 seasons. With it, "American driver at home" would mostly mean "an Indy specialist at Indianapolis", not a Grand Prix driver at his home Grand Prix.

Since the model trains from 1950 (D17), the 1950–1960 editions lie inside the training seasons, so the exclusion also keeps 381 oval-race rows out of training.
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
**Decision.** Front row by *grid* (slot 1–2, cars that did not start count as failed conversions) and by *qualifying* (1st–2nd) are both computed and ranked. Grid ≠ qualifying cases are split into penalties and **2021–22 sprint weekends** (where the sprint set the grid). Periods 2003–2013 vs 2014–2024; circuits need ≥ 8 front-row starts in both periods. Every rate has a 95% Wilson interval; chi-square tests check whether circuits differ at all and whether the overall rate changed; Spearman's rank correlation (with its p-value) measures whether the order carries over.
**Why.** The brief asks to distinguish qualifying from grid and to say whether the ranking changes, with an answer, a plot and a short justification. 2003 is the first season with complete qualifying data, so both definitions use the same rows. With 8–24 starts per circuit, intervals and tests are needed to know whether a ranking difference is real. An earlier version also bootstrapped the rank correlation and re-ran the ranking with other periods and minimum sizes; none of these changed the answer, so they were removed to keep the analysis to what the question needs.
**Why a minimum of 8 starts.** Every race has 2 front-row cars, so 8 starts means the circuit hosted at least 4 races in that period. A rate from very few starts is mostly luck: with 2 starts it can only be 0%, 50% or 100%. The value is a judgement call between keeping more circuits and having steadier rates. 8 keeps 17 circuits; 10 (our stage-A notebook) keeps 14.
**How to read a rank change ("Monza from joint 1st to 12th").** Each period ranks the circuits by their conversion rate.
* **Monza:** in 2003–2013, 17 of its 22 front-row cars finished on the podium (77%), tied with Monaco for the best rate, so it was joint 1st. In 2014–2024, 16 of 22 did (73%) and 11 circuits did better, so it was 12th. It fell 11 places because of **one podium fewer**: all circuits sit between 58% and 89%, so a single result reorders the list.
* **Yas Marina:** went from 6 of 10 (60%, 13th) to 19 of 22 (86%, 3rd).
**Result.** Overall conversion rose 68.0% → 75.9% (p = 0.013); circuits are not distinguishable in either period (p = 0.99 / 0.80), ρ = 0.21 (p = 0.42), so a real change in the circuit ranking cannot be shown. Penalised front-row qualifiers podium 28%, front-row starters 73%.
**Evidence.** §5 Q1.

### D10 — Q2 set-up **[DOMAIN + EDA]**
**Decision.** Explicit nationality → country mapping; home = the country the circuit is in (not the race name). A driver with two nationalities (American-Italian, Argentine-Italian) is at home in **either** country. The same rule builds the `home_race` feature. Control: home vs away within grid bucket (1 / 2–3 / 4–6 / 7–10 / 11+) × era (1950–79 / 1980–2013 / 2014–24), shown as a pivot-table heatmap (as in Lab 1) and averaged with weights = home starts. The test: one logistic regression `podium ~ home + grid slot + era` with race-clustered standard errors.
**Why.** A driver with two nationalities can be at home in both countries; mapping him to the first one only would call a home race "away". In this dataset that changes one start (Alfonso Thiele, American-Italian, 1960 Italian GP). The brief asks to compare drivers from similar grid positions. Era is added because podium rates per grid slot differ by era (§4). The heatmap shows "drivers who started from similar grid positions" directly; the regression gives one estimate with an interval, and clustering by race respects that rows from one race are not independent. An earlier version added a race bootstrap and three robustness rows; they gave the same answer and were removed.
**Result.** Raw −2.1 pp (one-off local entrants: 13.1% of home starts vs 1.4% of away starts come from drivers with ≤ 5 career starts) → −0.6 pp within grid bucket → −0.8 pp within grid bucket × era; heatmap cells range from −15.0 to +7.7 pp with no consistent sign; odds ratio 0.93 (95% CI 0.79–1.11, p = 0.43). No evidence of a home advantage.
**Evidence.** §5 Q2.

### D11 — Q3 set-up **[DOMAIN]**
**Decision.** Rate = mechanical retirements ÷ **race starts** per **team lineage** and period; cars that did not take the start are not race starts. A hand-written dictionary joins renamed teams: Toro Rosso → AlphaTauri → RB, Force India → Racing Point → Aston Martin, Lotus F1 → Renault → Alpine, Sauber ↔ Alfa Romeo, Marussia → Manor. Strict (`mechanical`) and broad (+ `ambiguous`) rates; only lineages with ≥ 30 starts; 95% Wilson intervals; chi-square test of team differences per period.
**Why.** The brief's definition ("a race start that ended early because a component failed"). A renamed team keeps its factory, staff and car design,, so comparing a lineage with itself is what "the same constructor in two periods" means. Four renames straddle the period boundary (Racing Point → Aston Martin and Renault → Alpine in 2021, AlphaTauri → RB and Alfa Romeo → Sauber in 2024), so by `constructorId` "Alpine 2014–2021" was one season (44 starts) and "RB 2022–2024" only 2024 (48 starts), and the cross-period correlation came out −0.49 only because identities were mixed. Below 30 starts one or two failures swing the rate too much.
**Result.** 8.9% → 5.5% of starts. Top 2014–2021: Caterham 21.2%, Toro Rosso → AlphaTauri → RB 14.4%, Lotus F1 → Renault → Alpine 13.2%, McLaren 13.0% (teams differ, p < 0.001). Top 2022–2024: Lotus F1 → Renault → Alpine 10.4%, Sauber ↔ Alfa Romeo 8.8% (team differences not significant, p = 0.18). Cross-period rank correlation of the 10 lineages +0.27 (p = 0.45). The broad rate keeps the same top four (2014–2021) and top three (2022–2024). The "after lap 1" rate of the first version was dropped: it never changed the answer.
**Evidence.** §5 Q3.

---

## Features

### D12 — Sprint results are not used as features **[DOMAIN]**
**Decision.** No feature from `sprint_results`, except as the reference slot for `grid_penalty` on 2021–22 sprint weekends (D15).
**Why.** Technically pre-race, but sprints exist only from 2021: they are absent from every training season (1950–2019), so the model could learn nothing from them. In 2021–22 the sprint result *was* the grid, which `grid_pos` already holds. The standings we use (from the previous race) already include earlier weekends' sprint points.
**Evidence.** §6.4.

### D13 — Standings come from *before* the race **[DOMAIN]**
**Decision.** For race N, join the standings published after the **previous race of the same season** via an explicit `raceId → prev_raceId` table; for a season opener use the **previous season's final standings**. Features: points as a share of the leader's points, rank, and wins as a share of the races run so far. Entries missing from the previous table get 0 points, no wins and the rank after the last ranked entry. Championship exclusions (Schumacher 1997, McLaren constructors 2007) were decided at or after the end of the season, although the data flags McLaren as excluded in every 2007 table. So in-season tables are used as published (McLaren was leading in mid-2007); only a previous season's **final** table used for an opener applies the exclusion (0 points, never the leader).
**Why.** The standings row for race N already contains race N's points: leakage (Verstappen, 2023 Belgian GP: 314 points after vs 281 before). An explicit lookup handles drivers who skipped a race. Points systems (8, 9, 10, 25 for a win) and season lengths (7–24 races) changed, so shares and ranks compare across eras where raw points and win counts do not.
**Why there is no `season_opener` feature.** At an opener the six standings features come from a whole-season table rather than from a few races, so we first gave the model a flag `season_opener` to tell the two cases apart. We removed it, because it cannot help a podium prediction:
* **It carries no signal by itself.** Every race has exactly three podiums, opener or not, so knowing that a race is the first of the season does not change anyone's chance (in an earlier version of the notebook its standalone AUC was 0.500).
* **The standings mean the same thing in both cases.** Whether they come from last season's final table or from this season's table, they describe how strong the driver and the team are. If anything the full-season table is the more reliable summary, so the model has no reason to read them differently.
* **A linear model could not use it anyway.** A logistic regression can only add the same constant to every opener's log-odds; it cannot use the flag to re-weight the standings features unless an explicit interaction is built.
* **There is little to learn from.** Openers are 70 of the 1,007 training races (about 1 in 14), too few for a flexible model to learn a reliable opener-specific pattern; a tree model could instead split on the flag by chance and overfit.
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
**Why a gap and not raw lap times or a circuit category.** A gap inside one race normalises circuit, season and weather at once; it is the same reference the FIA uses for its 107% rule. A per-circuit category has nothing to learn: every race has exactly 3 podiums, Q1 found the circuits statistically indistinguishable (chi-square p = 0.99 and 0.80), and a circuit new in the test seasons (Miami, first raced in 2022) has no training rows at all. `grid_penalty` carries what Q1 did find: front-row qualifiers sent back by a penalty podium 28.1% of the time, against 72.5%.
**Evidence.** §6.3 (gap distribution and cutoff), §6.7, §5.1.

### D16 — Five feature groups **[EDA]**
**Decision.** grid (3), qualifying (3), standings (6), form (5), context (4) = 21 candidate features. (A seventh standings column, `season_opener`, was removed; see D13.) The three candidates without signal (`pit_lane_start` in grid, `home_race` and `field_size` in context) are not model inputs (D30), so the models use **18 features**: grid (2), qualifying (3), standings (6), form (5), context (2).
**Why.** Each group answers a different question (where does he start? how fast was he? how strong is the car/driver this season? recently? anything else?), and the ablation needs named groups.
**Evidence before training** (§6.7, training seasons 1950–2019): starting position 0.883 standalone AUC on all training rows, and grid and qualifying position practically identical on the rows that have both (0.904 vs 0.905); most standings and form features 0.79–0.83, constructor versions mostly at or above the driver versions (rank is the exception); win shares 0.72–0.77; context, flags and `con_mech_rate_last10` 0.50–0.66 (`pit_lane_start` 0.501, `home_race` 0.508, `field_size` 0.544).
**Evidence after training** (§10, all five models): only "grid group only" loses clearly in every model (−0.084 to −0.100 on validation); single groups mostly substitute for each other.

### D17 — Training window 1950–2019: every season before validation **[EXP + DOMAIN]**
**Decision.** Train on all seasons from 1950 to 2019. A later start year would only be used if it clearly beat 1950 on the validation seasons.
**Why.** Leaving seasons out throws data away, so it needs evidence that a shorter window predicts better, not only a domain argument (bigger fields, frequent breakdowns and no qualifying data before 1994 are not enough on their own). Missing qualifying does not stop the older seasons from being used: the grid position exists for every season and carries almost the same information as the qualifying position (standalone AUC 0.904 vs 0.905 on the rows that have both, §6.7); missing qualifying values are filled and flagged by the preprocessing (D19).
**Check (§8.4).** Six start years (1950, 1960, 1970, 1980, 1994, 2003), each trained up to 2019 with the logistic regression and default gradient boosting and scored on the validation seasons 2020–2021; each compared with 1950 by the paired race bootstrap (D23). 1950 has the highest mean PR-AUC (0.7230) and every later start is lower (1970: −0.0073, 1994: −0.0266, 2003: −0.0275); no gain interval lies above 0, and for 1960, 1994 and 2003 the interval lies entirely below 0 (1994: −0.044 to −0.010), so starting in 1994 is significantly worse. The logistic regression is nearly insensitive to the start year (0.7226 from 1950, 0.7274 from 1994), while gradient boosting loses clearly when seasons are dropped (0.7235 from 1950 vs 0.6655 from 1994). On two earlier validation periods no start year is best everywhere, and 2003 is the lowest in all three.
**Known cost.** Qualifying is missing for every row before 1994, so its "was missing" indicator also marks the old era. A modern record without qualifying is therefore read partly like an old-era row (D27).
**Evidence.** §6 (constants and D17 callout), §6.7 (grid vs qualifying on the same rows), §8.4 (table, intervals and plot).

---

## Splitting, metrics and preprocessing

### D18 — Split by season **[DOMAIN]**
**Decision.** Train 1950–2019, validation 2020–2021, test 2022–2024. Models are fitted once on the training seasons and frozen.
**Why.** A random split would put rows from the same race and from the future into training. A time split copies real use (predict the next race from the past) and tests the 2022 rule change. 2020 was an unusual COVID season (17 races, repeated venues) and validation is used for several choices, so validation scores are slightly optimistic; test is the only unbiased number.
**Evidence.** §7 split summary (train 22,576 rows / 1,007 races, podium rate 13.4%; validation 780 / 39 and test 1,359 / 68, both 15.0%).

### D19 — Median imputation + missing indicators; scaling for LR/NN; split first, derive before impute **[EXP + DOMAIN]**
**Decision.** `SimpleImputer(median, add_indicator=True)`, which turns the 18 model features into 32 columns (14 missing indicators); `StandardScaler` for logistic regression and the network; order impute → scale; all fitted on the training set inside a `Pipeline`; derived features (`grid_penalty`) computed from real values before imputation.
**Why.** Missing values are structural (no qualifying before 1994 and patchy until 2002, no constructors' championship before 1958, no history for a debutant), so an indicator lets the model learn from "missing". The median is robust to skew. Linear models and neural networks need comparable scales; trees do not.
**Experiments (§8.1–8.3, §8.5).**
* **E1, split → fit vs fit → split:** scores practically identical (validation PR-AUC 0.7226 vs 0.7230), but medians and means shift when future seasons are included (e.g. `experience` median 41 → 45), so the second order uses information unavailable in 2019. Correct order kept.
* **E2, impute → scale vs scale → impute, for LR and the NN (32 → 16):** visibly different `quali_gap_pct` distribution; validation PR-AUC practically the same for LR (0.7226 vs 0.7214); for the NN 0.7158 vs 0.7227 on validation but reversed on test (0.7112 vs 0.7034), a gap of the size of the network's seed spread (0.7158–0.7207), so neither order is better. Impute → scale kept: the standard order, and the model sees exactly mean 0 / std 1.
* **E3, derive → impute vs impute → derive:** imputing first invents 14,228 penalty values; validation PR-AUC, ROC-AUC and log-loss all slightly worse (0.7208 vs 0.7226, 0.9296 vs 0.9324, 0.2268 vs 0.2245). Derive first.
* **E4, how to fill missing qualifying (§8.5):** since training starts in 1950, qualifying is missing for 63% of training rows. Median + indicator (LR 0.7226, GB 0.7235) beats median without indicator (LR 0.7103, significantly worse: −0.023 to −0.003; GB 0.7017) and a "fall back to grid" option (quali position = grid slot; LR 0.7154, −0.014 to −0.001; GB 0.6633, −0.087 to −0.013, both significant). The median value is only a placeholder; the indicator lets the model treat rows without qualifying as their own group. Filling with the grid slot erases the penalty signal Q1 found.
**Evidence.** §8 (effect table and plot), §8.1–8.5.

### D20 — Class imbalance: no class weights for any model **[DOMAIN + EXP]**
**Decision.** All five models (logistic regression, random forest, both gradient-boosting models and the network) are trained **unweighted**. The imbalance is handled by the threshold (D22) and by PR-AUC as the primary metric (D21).
**Why.** Weights make the rare class count more but inflate every probability, and the inference function returns a probability. For the forest we checked on validation whether weights would help: the best unweighted forest scores 0.7334, the best weighted (`balanced_subsample`) 0.7310, so weights bring no gain. Unweighted, all models except tuned gradient boosting have low validation Brier scores (§9.4): logistic regression and random forest 0.067, network 0.068, default gradient boosting 0.070 (tuned gradient boosting 0.094, D28).
**Evidence.** §9 (D20 callout), §9.1 (forest grid, weighted vs unweighted), §9.4 (validation Brier; the calibration plot is on test, for reference only).

### D21 — Metrics **[DOMAIN]**
**Decision.** The five metrics of the brief: ROC-AUC, PR-AUC, F1, precision and recall; plus Brier score and log-loss (calibration), race top-3 hit rate and predicted podiums per race, on train, validation and test. Primary: PR-AUC. Secondary: ROC-AUC.
**Why.** Podiums are rare; PR-AUC focuses on the top of the ranking and its random level is the base rate (0.15) rather than 0.5. Accuracy is not used: a model that always says "no podium" has accuracy 0.850 on validation and test (1 − the base rate of 0.150) and recall 0. ROC-AUC shows overall separation. The inference functions return a probability, so calibration is checked too. The model tables in §9.4 show the Brier score; log-loss is computed for every model and saved in `model_comparison.csv` in the output folder, and the §8 experiment tables show it.
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

### D24 — Model comparison: rank on validation, compare each model with the baseline; the logistic regression is recommended **[DOMAIN, checked by EXP]**
**Decision.** Rank the five learned models by validation PR-AUC (mean over 3 seeds for the forest and the network). For each model, the paired bootstrap interval of *model − baseline* decides whether it is better than the logistic-regression baseline (only if the interval lies entirely above 0). If none is better, the **logistic regression is the recommended model**. All five models are still explained and keep their own inference function (D26, D27, D30), so they can be compared on the same inputs.
**Result.** Validation: tuned gradient boosting 0.7361, random forest 0.7276, default gradient boosting 0.7235, logistic regression 0.7226, network 0.7190; every interval against the baseline includes 0 (tuned gradient boosting −0.023 to +0.040, random forest −0.010 to +0.024), so no model is better than the baseline. Test: logistic regression 0.722 and random forest 0.722, network 0.711, tuned gradient boosting 0.696, default gradient boosting 0.693, all within each other's intervals. The baseline beats the grid rule significantly (interval 0.031 to 0.144).
**Why.** The brief asks to justify complex models against the baseline, and with 39 validation races a ranking alone reacts to noise. No model beats the logistic regression; it ties the forest for the best test score, is deterministic, readable and well calibrated (validation Brier 0.067), so it is the one we recommend.
**Evidence.** §9.4 (tables, ranking with intervals, calibration and confusion matrices), §9.5.

### D25 — Shallow neural network: 2 hidden layers (32 → 16), built with Keras **[DOMAIN]**
**Decision.** Input: the 32 imputed and scaled columns (18 features + 14 missing indicators) → Dense 32 ReLU → Dense 16 ReLU → 1 sigmoid output (the podium probability). Each hidden layer has dropout 20% and an L2 penalty of 1e-4. Loss: binary cross-entropy, unweighted (D20). Optimiser: Adam, learning rate 0.001, batches of 128. Training stops when validation PR-AUC has not improved for 15 epochs, and the best epoch's weights are kept. Trained 3 times (seeds 42, 1, 2); the seed-42 network is the one reported.
**Why.** The brief asks for a shallow network (roughly 1–2 hidden layers) and allows a standard library such as Keras. Two small layers give only 1,601 weights, small compared with 22,576 training rows. Dropout (switching off 20% of the units at random while training), L2 (large weights cost extra) and early stopping all limit overfitting. The 3 seeds show how much the result depends on the random starting weights: validation PR-AUC 0.716–0.721.
**Evidence.** §9.3 (weight count, learning curves, seed table).

### D26 — Explain all five models on the test seasons **[DOMAIN]**
**Decision.** For every learned model, the logistic regression (the recommended model, D24) first: permutation importance per feature and per feature group; SHAP with **one model-agnostic explainer for all five models** (`PermutationExplainer` on each model's `predict_proba`, original 18 features, 300 random test rows plus the rows explained one by one), so every SHAP value is a change in **podium probability**; beeswarm, mean-|SHAP| bars and group shares; a SHAP waterfall and LIME (5 seeds, plus LIME's own view) for Verstappen, 2023 Belgian GP; each model's most confident wrong prediction. Computed on 2022–2024.
**Background.** 100 training rows from **2003–2019**, the training seasons with complete qualifying data, like every row we explain. The base value then describes a typical driver at prediction time (base values 0.140–0.157). With a background from all training seasons, 63% of it would have no qualifying data, and the qualifying contributions would mix "this driver's value" with "having qualifying data at all".
**Why one explainer.** The five models are explained in the same unit and on the same features, which makes them comparable. The model-specific explainers (`LinearExplainer`, `TreeExplainer`) are exact but explain each model's internal score on the preprocessed columns (log-odds for the logistic regression and gradient boosting, probability for the random forest), and there is none for the network. The contributions still add up exactly to each model's probability (checked in §11.2).
**Why.** Each model has an inference function, so any of their predictions could be shown to a user; comparing the models also shows whether very different models rely on the same information. Explaining chooses nothing, so the test set can be used. LIME's local fit is reported (mean R² 0.34–0.70 for four of the models), which is why SHAP is the main local explanation. Explanations describe what a model relies on, **not causes**.
**Result.** Grid dominates every model (group permutation drop 0.217–0.363; largest SHAP share in every model, 34.3–58.8%). After grid the tree models rely on standings; the logistic regression and the network use qualifying much more than the tree models. For Verstappen at Spa 2023 the logistic regression's two largest contributions are `grid_pos` (+0.118) and `quali_position` (+0.117).
**Evidence.** §11.

### D27 — One inference function per model **[DOMAIN]**
**Decision.** `predict_podium_lr`, `predict_podium_rf`, `predict_podium_gb_default`, `predict_podium_gb_tuned` and `predict_podium_nn`, each using its own fitted model (with that model's preprocessing) and its own validation-tuned threshold (D22). The logistic regression (recommended, D24) is shown first, with both demos printed in full. They share one input check (`prepare_record`): `grid_pos` and `field_size` are required (`field_size` is not a model feature, but `grid_pct` is computed from it), raw grid 0 becomes a pit-lane start in the last slot (D7), `grid_pct` and `grid_penalty` are derived, other missing values are filled through the model's own pipeline (median + indicator), ranges are validated, unknown feature names are rejected, and the missing features are reported.
**Demos.** Complete record: Verstappen, Spa 2023 (logistic regression 0.735, "podium"; he won). Partially-missing record: a real debutant, Guanyu Zhou at the 2022 Bahrain GP, whose own form is missing as for every debutant in training (logistic regression 0.004, "no"; he did not podium). Third demo: the same debutant from the pit lane.
**Why.** The brief asks for a demo on complete and partially-missing records, and every model gets one so that each can be used and compared on the same inputs. Reusing each training pipeline guarantees the same treatment as in training; the checks stop typos and impossible values from being silently accepted.
**Documented limitation.** A breakdown table removes blocks of Verstappen's features. The logistic regression falls step by step (0.735 → 0.603 without qualifying → 0.539 without form → 0.391 without both), but the network *rises* (0.513 → 0.833 without both): a 2023 record without qualifying looks like a pre-1994 row, a pattern that never occurred for a championship leader in training. Missing-value patterns never seen in training make the models disagree, which is why every function lists the missing features.
**Evidence.** §12 (demos for all five functions and the breakdown table).

### D28 — Gradient boosting: early stopping off; hyperparameters by grid search **[EXP]**
**Decision.** `early_stopping=False` for every gradient-boosting model; tuned model chosen from 54 combinations (learning rate 0.01/0.03/0.1 × trees 50/100/300 × leaves 7/15/31 × min leaf 20/80) on validation PR-AUC → learning rate 0.01, 50 trees, 7 leaves, min leaf 20.
**Why.** scikit-learn's default turns early stopping on above 10,000 rows and holds out a *random* 10% of rows, mixing drivers of the same race (against D18) and making results depend on the seed and the exact number of rows. Without it, the model is deterministic. Default gradient boosting overfits (train PR-AUC 0.765 vs validation 0.724); the tuned model does not (0.574 vs 0.736). The best point is at the corner of the grid (slowest, fewest and simplest trees), consistent with a simple model being enough; with so little learning its predictions stay near the average podium rate (validation Brier 0.094), so its outputs rank well but are not probabilities.
**Evidence.** §8 (`make_hgb`), §9.2 (grid search heatmap, learning curve).

### D29 — Random forest and logistic-regression settings **[EXP / DOMAIN]**
**Decision.** Random forest: 400 trees, `max_features="sqrt"`, `min_samples_leaf` chosen on validation from 5 options among unweighted forests → 100 (validation PR-AUC 0.7334); weighted forests are shown next to them only to check D20 (best 0.7310). The training score reported is the out-of-bag estimate (0.573; in-sample 0.599). Logistic regression: scikit-learn default L2 strength (C = 1).
**Why.** Leaf size controls memorisation; small leaves (5) score worse on validation (0.704 unweighted, 0.708 weighted) than 100 (0.733 and 0.729). The in-sample training score of a forest is misleading, the out-of-bag score is honest. With 22,576 rows the default L2 penalty is mild and the baseline needs no tuning to make the point.
**What the settings mean.**
* `n_estimators = 400`: the number of decision trees in the forest. The forest's probability is the average of the 400 trees.
* `min_samples_leaf`: the smallest number of training rows a leaf (an end point of a tree) may hold; a split that would leave fewer rows on either side is not made. The leaf predicts the share of podiums among its rows. Small leaves (5) hold a handful of rows, often from the same few races, so the tree memorises noise; large leaves (100) average many rows, so predictions are smoother but less detailed. 100 was best on validation.
* `max_features = "sqrt"`: at every split a tree may only look at a random subset of the columns, of size √(number of columns). The forest sees 32 columns (18 features + 14 missing indicators), so each split chooses among 5 random columns. This makes the trees different from each other (otherwise every tree would split on `grid_pos` first), and averaging different trees is what reduces the variance.
* `class_weight = None`: no class weights (D20). The alternative tried, `"balanced_subsample"`, would make podium rows count more in each tree's training sample so that both classes weigh the same.
* `C` (logistic regression): the inverse of the penalty strength, C = 1 / λ. The model minimises log-loss plus an L2 penalty that pulls the weights toward 0. A small C (e.g. 0.01) means a strong penalty, small weights and a simpler model; a large C (e.g. 100) means almost no penalty, so the weights fit the training data freely. C = 1 is scikit-learn's default.
**Evidence.** §9.1.

### D30 — Which features the models use: no signal, no input; remove a feature only if that significantly improves validation **[EDA + EXP]**
**Decision.** (1) A candidate feature with no signal in the EDA is not a model input: `pit_lane_start`, `home_race` and `field_size` (standalone AUC 0.501, 0.508 and 0.544 on the training seasons, §6.7) are built and shown in the evidence, but the models use the other **18 features**. Their information is either already elsewhere (a pit-lane start is the last slot in `grid_pos`; field size is inside `grid_pct`) or absent (Q2 found no home advantage). (2) A group or single feature is removed from a model only if removing it raises that model's validation PR-AUC with a 95% interval entirely above 0. The ablation is run for all five models; the random forest and the network are averaged over 3 seeds per variant. To confirm (1), §10 also **adds back** each of the three candidates, and all three together, to every model.
**Result.** No add-back improves any model significantly (every interval includes 0). No group or feature qualifies for removal in any model, so every model keeps all 18 features. "Grid group only" loses clearly in every model (−0.084 to −0.100 on validation). Single-group removals that hurt significantly on validation: grid for the random forest, qualifying and standings for default gradient boosting, standings for tuned gradient boosting, context for the logistic regression; removing `experience` alone also hurts the logistic regression (−0.009). Form shows no measurable contribution as a group, which we report.
**Why.** A feature without signal adds noise and makes the models harder to explain; the add-back check shows that leaving them out costs nothing. Decisions are taken on validation only. With 39 validation races, a rule with an interval prevents reacting to noise.
**Evidence.** §6.7 (standalone AUC), §10 (group ablation, drop-one and add-back table).
