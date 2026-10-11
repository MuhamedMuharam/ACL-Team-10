# ACL Project – Team 10: Formula 1 Podium Prediction

Predicting Formula 1 podium finishes from pre-race data (1950–2024): data cleaning, EDA, leakage-safe
feature engineering, ML/neural-network models and explainable AI (SHAP, LIME).

- **Dataset:** [Formula 1 World Championship (1950–2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) (Kaggle / Ergast), 14 relational CSVs
- **Target:** `podium = positionOrder <= 3`, one row per (raceId, driverId)
- **Prediction cutoff:** after qualifying, before the race starts
- **Kaggle notebook:** [ACL Project – Team 10](https://www.kaggle.com/code/muhamedmuharam/notebook699276446c)
- **Team:** _names (A data lead, B data-engineering analyst, C feature engineer, D modeling lead)_

## Repository layout

| Path | Contents |
|---|---|
| `notebooks/` | development notebooks, one per section (pushed from Kaggle) |
| `notebooks/ACL_Project_Team10.ipynb` | final run-all notebook (submission) |
| `report/` | analytical report (PDF) and figures |
| `DECISIONS.md` | log of every cleaning / feature / modeling decision with its evidence (D1–D30, the IDs used in the notebook) |

Development notebooks: `01_audit_cleaning`, `02_de_questions`, `03_features`, `04_models`, `05_xai`.
Each member pushes only to their own file (Kaggle's GitHub sync overwrites the whole file).

## Reproducing

Open the Kaggle notebook (dataset attached as input) and click **Run All**. Raw CSVs are never modified.
