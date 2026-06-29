"""
Prediction service: wraps the trained scikit-learn pipeline and turns a raw
model probability into the rich, human-readable output the UI needs
(risk level, confidence, contributing factors, recommendations).
"""
import json
import os

import joblib
import numpy as np

_model = None
_meta = None


def _load(app):
    global _model, _meta
    if _model is None:
        _model = joblib.load(app.config["ML_MODEL_PATH"])
    if _meta is None:
        with open(app.config["ML_META_PATH"]) as f:
            _meta = json.load(f)
    return _model, _meta


FEATURE_LABELS = {
    "age": "Age",
    "gender": "Gender",
    "total_bilirubin": "Total Bilirubin",
    "direct_bilirubin": "Direct Bilirubin",
    "alkaline_phosphotase": "Alkaline Phosphatase",
    "alt": "Alamine Aminotransferase (ALT)",
    "ast": "Aspartate Aminotransferase (AST)",
    "total_proteins": "Total Protein",
    "albumin": "Albumin",
    "ag_ratio": "Albumin/Globulin Ratio",
}


def _risk_level(probability: float) -> str:
    if probability < 0.35:
        return "Low"
    if probability < 0.65:
        return "Medium"
    return "High"


def _abnormal_factors(payload: dict, meta: dict):
    """Compare submitted values against clinical normal ranges and return
    a list of plain-English contributing factors, sorted by how far out of
    range + model feature importance they are."""
    ranges = meta["normal_ranges"]
    importances = meta.get("feature_importances", {})
    factors = []

    for key, (low, high, unit) in ranges.items():
        value = payload.get(key)
        if value is None:
            continue
        label = FEATURE_LABELS.get(key, key)
        if value > high:
            pct_over = (value - high) / max(high, 0.0001)
            factors.append({
                "text": f"Elevated {label} ({value:g} {unit}, normal up to {high})",
                "weight": importances.get(key, 0.05) * (1 + min(pct_over, 3)),
            })
        elif value < low:
            factors.append({
                "text": f"Low {label} ({value:g} {unit}, normal range {low}-{high})",
                "weight": importances.get(key, 0.05),
            })

    # Age as a soft factor
    age = payload.get("age")
    if age is not None and age >= 60:
        factors.append({
            "text": f"Age {int(age)} (increased baseline risk over 60)",
            "weight": importances.get("age", 0.05) * 0.6,
        })

    factors.sort(key=lambda f: f["weight"], reverse=True)
    return [f["text"] for f in factors]


def _recommendations(risk_level: str, factors: list) -> list:
    base = {
        "Low": [
            "Maintain a balanced diet and limit alcohol intake.",
            "Continue routine annual liver function screening.",
            "Stay physically active and maintain a healthy body weight.",
        ],
        "Medium": [
            "Schedule a follow-up liver function panel within 4-6 weeks.",
            "Reduce or eliminate alcohol consumption.",
            "Avoid unnecessary use of hepatotoxic medications (consult your doctor).",
            "Discuss results with a physician for further evaluation.",
        ],
        "High": [
            "Seek prompt medical consultation with a hepatologist or physician.",
            "Request a comprehensive liver panel, ultrasound, and viral hepatitis screening.",
            "Avoid alcohol and hepatotoxic substances entirely until evaluated.",
            "Monitor for symptoms: jaundice, abdominal pain, fatigue, or swelling.",
        ],
    }
    recs = list(base.get(risk_level, base["Medium"]))
    if any("Bilirubin" in f for f in factors):
        recs.append("Track jaundice symptoms (yellowing of skin/eyes) and report changes promptly.")
    if any("ALT" in f or "AST" in f for f in factors):
        recs.append("Limit fatty/processed foods, which can add strain to liver enzyme levels.")
    return recs


def _interpretation(risk_level: str, probability: float, prediction_label: str) -> str:
    if prediction_label == "Disease Detected":
        if risk_level == "High":
            return (
                "The model identified multiple abnormal liver markers consistent with "
                "significant hepatic stress. This pattern is strongly associated with "
                "liver disease in the training population and warrants prompt clinical attention."
            )
        return (
            "The model detected a pattern of liver markers associated with disease, "
            "though the signal is moderate. Clinical correlation and follow-up testing "
            "are recommended to confirm the finding."
        )
    else:
        if risk_level == "Low":
            return (
                "Liver function markers fall largely within expected ranges. The model "
                "found no strong pattern associated with liver disease in this profile."
            )
        return (
            "Most markers appear within range, but the overall profile shows some "
            "borderline values. Periodic monitoring is advisable."
        )


def predict(app, payload: dict) -> dict:
    """
    payload keys (floats unless noted): age, gender (1=Male/0=Female),
    total_bilirubin, direct_bilirubin, alkaline_phosphotase, alt, ast,
    total_proteins, albumin, ag_ratio
    """
    model, meta = _load(app)
    order = meta["feature_order"]
    medians = meta["medians"]

    row = []
    clean_payload = {}
    for key in order:
        val = payload.get(key)
        if val is None or val == "":
            val = medians.get(key, 0)
        val = float(val)
        row.append(val)
        clean_payload[key] = val

    import pandas as pd
    row_df = pd.DataFrame([dict(zip(order, row))])
    proba_disease = float(model.predict_proba(row_df)[0][1])
    risk_level = _risk_level(proba_disease)
    prediction_label = "Disease Detected" if proba_disease >= 0.5 else "No Disease Detected"
    confidence = round((proba_disease if proba_disease >= 0.5 else 1 - proba_disease) * 100, 1)

    factors = _abnormal_factors(clean_payload, meta)
    if not factors:
        factors = ["All submitted values fall within typical clinical reference ranges."]

    recommendations = _recommendations(risk_level, factors)
    interpretation = _interpretation(risk_level, proba_disease, prediction_label)

    return {
        "prediction": prediction_label,
        "risk_level": risk_level,
        "confidence": confidence,
        "probability_disease": round(proba_disease * 100, 1),
        "factors": factors[:6],
        "recommendations": recommendations,
        "interpretation": interpretation,
        "model_name": meta.get("best_model"),
    }


def get_meta(app) -> dict:
    _, meta = _load(app)
    return meta
