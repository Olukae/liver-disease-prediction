import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, PredictionRecord
from app.routes.admin import admin_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _last_n_days(n):
    today = datetime.utcnow().date()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


@api_bp.route("/charts/risk-distribution")
@login_required
@admin_required
def risk_distribution():
    data = {
        "Low": PredictionRecord.query.filter_by(risk_level="Low").count(),
        "Medium": PredictionRecord.query.filter_by(risk_level="Medium").count(),
        "High": PredictionRecord.query.filter_by(risk_level="High").count(),
    }
    return jsonify(labels=list(data.keys()), values=list(data.values()))


@api_bp.route("/charts/predictions-trend")
@login_required
@admin_required
def predictions_trend():
    days = _last_n_days(14)
    counts = []
    for d in days:
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        counts.append(
            PredictionRecord.query.filter(
                PredictionRecord.created_at >= start, PredictionRecord.created_at < end
            ).count()
        )
    return jsonify(labels=[d.strftime("%b %d") for d in days], values=counts)


@api_bp.route("/charts/user-activity")
@login_required
@admin_required
def user_activity():
    days = _last_n_days(14)
    counts = []
    for d in days:
        start = datetime.combine(d, datetime.min.time())
        end = start + timedelta(days=1)
        counts.append(
            User.query.filter(
                User.created_at >= start, User.created_at < end, User.role == "patient"
            ).count()
        )
    return jsonify(labels=[d.strftime("%b %d") for d in days], values=counts)


@api_bp.route("/charts/parameter-analysis")
@login_required
@admin_required
def parameter_analysis():
    fields = ["total_bilirubin", "alkaline_phosphotase", "alt", "ast", "albumin"]
    labels = ["Total Bilirubin", "Alk. Phosphatase", "ALT", "AST", "Albumin"]
    disease_avgs, healthy_avgs = [], []
    for f in fields:
        col = getattr(PredictionRecord, f)
        d_avg = db.session.query(db.func.avg(col)).filter(
            PredictionRecord.prediction == "Disease Detected"
        ).scalar() or 0
        h_avg = db.session.query(db.func.avg(col)).filter(
            PredictionRecord.prediction == "No Disease Detected"
        ).scalar() or 0
        disease_avgs.append(round(d_avg, 2))
        healthy_avgs.append(round(h_avg, 2))
    return jsonify(labels=labels, disease=disease_avgs, healthy=healthy_avgs)


@api_bp.route("/charts/my-history")
@login_required
def my_history():
    records = current_user.predictions.order_by(PredictionRecord.created_at.asc()).all()
    return jsonify(
        labels=[r.created_at.strftime("%b %d") for r in records],
        confidence=[r.confidence for r in records],
        risk=[r.risk_level for r in records],
    )


# --- AI Health Assistant (rule-based) -----------------------------------
RESPONSES = [
    (["bilirubin"], "Bilirubin is a yellow pigment produced when red blood cells break down. "
                     "Elevated levels can indicate the liver isn't processing it efficiently, which "
                     "may point to conditions like jaundice or hepatitis. Always confirm with a doctor."),
    (["alt", "sgpt"], "ALT (Alamine Aminotransferase) is an enzyme mostly found in the liver. High ALT "
                       "levels often signal liver cell damage or inflammation."),
    (["ast", "sgot"], "AST (Aspartate Aminotransferase) is found in the liver and other tissues. "
                       "When elevated alongside ALT, it strengthens the likelihood of liver stress."),
    (["albumin"], "Albumin is a protein made by the liver. Low albumin can suggest reduced liver "
                   "function or chronic liver disease."),
    (["risk", "high risk"], "A 'High Risk' result means the model found a strong pattern associated "
                             "with liver disease in your submitted values. It's not a diagnosis — please "
                             "follow up with a healthcare professional for confirmatory testing."),
    (["diet", "food", "eat"], "Liver-friendly eating generally means: more leafy greens, whole grains, "
                               "and lean protein; less alcohol, fried food, and added sugar."),
    (["accuracy", "confidence"], "The confidence score reflects how strongly the model's internal "
                                  "probability favored its prediction. Higher confidence means the "
                                  "submitted values matched a clearer pattern in the training data."),
    (["alcohol"], "Alcohol is processed by the liver and, in excess, is one of the most common causes "
                   "of liver damage over time, including fatty liver and cirrhosis."),
    (["report", "pdf"], "You can download a PDF report from any past prediction in your History page — "
                         "just click the download icon next to a record."),
    (["hello", "hi", "hey"], "Hi there! I'm your AI health assistant. Ask me about liver test "
                              "parameters, your risk level, or general liver health tips."),
]

FALLBACK = (
    "I can help explain liver test parameters (bilirubin, ALT, AST, albumin), your risk level, "
    "or general liver health tips. Could you rephrase your question? For medical decisions, "
    "please consult a licensed physician."
)


@api_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    message = (request.json or {}).get("message", "").lower().strip()
    if not message:
        return jsonify(reply=FALLBACK)

    for keywords, response in RESPONSES:
        if any(k in message for k in keywords):
            return jsonify(reply=response)

    last = current_user.predictions.first()
    if last and ("my result" in message or "my prediction" in message or "my risk" in message):
        return jsonify(reply=(
            f"Your most recent prediction was '{last.prediction}' with {last.confidence}% confidence "
            f"and a {last.risk_level} risk level, recorded on {last.created_at.strftime('%d %b %Y')}. "
            f"You can view the full breakdown on your History page."
        ))

    return jsonify(reply=FALLBACK)
