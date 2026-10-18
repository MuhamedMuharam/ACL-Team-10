# F1 Podium Prediction — Milestone 1

Predict, for every driver on the starting grid of a Formula 1 race, whether he finishes on the podium (top 3), using only information known after qualifying and before the race starts.

Kaggle notebook: [ACL Project – Team 10](https://www.kaggle.com/code/muhamedmuharam/notebook699276446c)

Dataset: [Formula 1 World Championship (1950–2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) (Kaggle / Ergast), 14 relational tables.

## Files

| file | what it is |
|---|---|
| `F1_Podium_Prediction.ipynb` | the run-all notebook (saved with all outputs): audit, cleaning, EDA, data-engineering questions, features, split, preprocessing experiments, models, ablation, explainability, inference |
| `DECISIONS.md` | every decision we made (D1–D30), why, and where the evidence is in the notebook |
| `requirements.txt` | Python packages (minimum versions; the exact versions of the saved run are listed in it and printed in the notebook's first cell) |
| `outputs/` (created on run) | cleaned tables, modeling table, model comparison, ablation results, all figures |

## How to run

**On Kaggle:** create a notebook, add the dataset above as input, upload `F1_Podium_Prediction.ipynb`, turn **Internet on** (Settings → Internet; the first cell installs `lime`, `shap` or `statsmodels` if they are missing and stops with a clear message if it cannot), and press **Run All**. The notebook finds the data under `/kaggle/input/` and writes outputs to `/kaggle/working/`.

**Locally:** put the 14 CSV files in a folder called `data/` next to the notebook, `pip install -r requirements.txt`, then run all cells. Outputs go to `outputs/`.

A full run takes about 40 minutes on a cloud CPU (most of it in retraining the neural network for the ablation, the network's SHAP values and the bootstrap intervals).

The cleaning, the data-engineering answers, the logistic regression and gradient boosting are deterministic. Random forest and the neural networks can move slightly under other library versions; the notebook reports their spread over random seeds.
