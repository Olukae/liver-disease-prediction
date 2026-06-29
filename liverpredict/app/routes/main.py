from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import PredictionRecord

main_bp = Blueprint("main", __name__)

HEALTH_TIPS = [
    {"icon": "fa-glass-water", "title": "Limit Alcohol", "text": "Excess alcohol is one of the leading causes of liver damage. Keep intake moderate or avoid it entirely."},
    {"icon": "fa-carrot", "title": "Eat Liver-Friendly Foods", "text": "Leafy greens, garlic, citrus fruits, and whole grains support healthy liver function."},
    {"icon": "fa-weight-scale", "title": "Maintain a Healthy Weight", "text": "Obesity increases the risk of non-alcoholic fatty liver disease (NAFLD)."},
    {"icon": "fa-syringe", "title": "Get Vaccinated", "text": "Hepatitis A and B vaccines protect against major causes of liver infection."},
    {"icon": "fa-pills", "title": "Use Medication Carefully", "text": "Avoid overuse of over-the-counter painkillers; always follow dosage instructions."},
    {"icon": "fa-droplet", "title": "Stay Hydrated", "text": "Adequate water intake helps the liver flush toxins more efficiently."},
]


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard") if current_user.is_admin else url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    recent = current_user.predictions.limit(5).all()
    total = current_user.predictions.count()
    high_risk = current_user.predictions.filter_by(risk_level="High").count()
    last = current_user.predictions.first()

    return render_template(
        "dashboard.html",
        recent=recent, total=total, high_risk=high_risk, last=last,
        tips=HEALTH_TIPS[:3],
    )


@main_bp.route("/health-tips")
@login_required
def health_tips():
    return render_template("health_tips.html", tips=HEALTH_TIPS)
