"""
Train Model - Intelligent Liver Disease Prediction System
------------------------------------------------------------
Trains a classifier on the Indian Liver Patient Dataset (ILPD, UCI Repository)
and exports the fitted pipeline (imputer + scaler + model) plus metadata
needed by the Flask app at runtime (feature order, medians, accuracy, etc).

Run:  python ml/train_model.py
"""
import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "ilpd_dataset.csv")
MODEL_OUT = os.path.join(BASE_DIR, "liver_model.joblib")
META_OUT = os.path.join(BASE_DIR, "model_meta.json")

COLUMNS = [
    "Age", "Gender", "Total_Bilirubin", "Direct_Bilirubin",
    "Alkaline_Phosphotase", "Alamine_Aminotransferase",
    "Aspartate_Aminotransferase", "Total_Protiens", "Albumin",
    "Albumin_and_Globulin_Ratio", "Dataset",
]

# Friendly names exposed to the rest of the app (also used as form field names)
FEATURE_ORDER = [
    "age", "gender", "total_bilirubin", "direct_bilirubin",
    "alkaline_phosphotase", "alt", "ast",
    "total_proteins", "albumin", "ag_ratio",
]

NORMAL_RANGES = {
    "total_bilirubin": (0.1, 1.2, "mg/dL"),
    "direct_bilirubin": (0.0, 0.3, "mg/dL"),
    "alkaline_phosphotase": (44, 147, "IU/L"),
    "alt": (7, 56, "IU/L"),
    "ast": (5, 40, "IU/L"),
    "total_proteins": (6.0, 8.3, "g/dL"),
    "albumin": (3.5, 5.0, "g/dL"),
    "ag_ratio": (1.0, 2.5, "ratio"),
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, names=COLUMNS)
    df["Gender"] = df["Gender"].map({"Male": 1, "Female": 0})
    # Dataset: 1 = liver patient (disease), 2 = no disease -> convert to 1/0
    df["target"] = (df["Dataset"] == 1).astype(int)
    df = df.drop(columns=["Dataset"])
    df = df.rename(columns={
        "Age": "age", "Gender": "gender", "Total_Bilirubin": "total_bilirubin",
        "Direct_Bilirubin": "direct_bilirubin", "Alkaline_Phosphotase": "alkaline_phosphotase",
        "Alamine_Aminotransferase": "alt", "Aspartate_Aminotransferase": "ast",
        "Total_Protiens": "total_proteins", "Albumin": "albumin",
        "Albumin_and_Globulin_Ratio": "ag_ratio",
    })
    return df


def build_pipeline(model) -> Pipeline:
    return Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", model),
    ])


def main():
    df = load_data()
    X = df[FEATURE_ORDER]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=400, max_depth=8, min_samples_leaf=3,
            class_weight="balanced", random_state=42, n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=42),
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
    }

    best_name, best_pipe, best_score = None, None, -1
    report = {}
    for name, model in candidates.items():
        pipe = build_pipeline(model)
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1")
        pipe.fit(X_train, y_train)
        preds = pipe.predict(X_test)
        proba = pipe.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        auc = roc_auc_score(y_test, proba)
        report[name] = {
            "cv_f1_mean": round(float(cv_scores.mean()), 4),
            "test_accuracy": round(float(acc), 4),
            "test_f1": round(float(f1), 4),
            "test_roc_auc": round(float(auc), 4),
        }
        print(f"{name}: cv_f1={cv_scores.mean():.4f} acc={acc:.4f} f1={f1:.4f} auc={auc:.4f}")
        if cv_scores.mean() > best_score:
            best_name, best_pipe, best_score = name, pipe, cv_scores.mean()

    # Refit the winning pipeline on the FULL dataset for production use
    final_model = candidates[best_name].__class__(**candidates[best_name].get_params())
    final_pipe = build_pipeline(final_model)
    final_pipe.fit(X, y)

    joblib.dump(final_pipe, MODEL_OUT)

    # Feature importance (only meaningful for tree models; fallback to coef for LR)
    importances = {}
    fitted_model = final_pipe.named_steps["model"]
    if hasattr(fitted_model, "feature_importances_"):
        for feat, imp in zip(FEATURE_ORDER, fitted_model.feature_importances_):
            importances[feat] = round(float(imp), 4)
    elif hasattr(fitted_model, "coef_"):
        coefs = np.abs(fitted_model.coef_[0])
        coefs = coefs / coefs.sum()
        for feat, imp in zip(FEATURE_ORDER, coefs):
            importances[feat] = round(float(imp), 4)

    meta = {
        "best_model": best_name,
        "feature_order": FEATURE_ORDER,
        "feature_importances": importances,
        "normal_ranges": NORMAL_RANGES,
        "medians": {f: float(df[f].median()) for f in FEATURE_ORDER},
        "evaluation": report,
        "n_samples": int(len(df)),
        "n_positive": int(df["target"].sum()),
        "n_negative": int((df["target"] == 0).sum()),
        "trained_on": "Indian Liver Patient Dataset (ILPD), UCI Machine Learning Repository",
    }
    with open(META_OUT, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nBest model: {best_name} (cv f1={best_score:.4f})")
    print(f"Saved model -> {MODEL_OUT}")
    print(f"Saved metadata -> {META_OUT}")


if __name__ == "__main__":
    main()
