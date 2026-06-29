import csv
import io
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    Response, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, PredictionRecord

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_users = User.query.filter_by(role="patient").count()
    total_predictions = PredictionRecord.query.count()
    high_risk = PredictionRecord.query.filter_by(risk_level="High").count()
    medium_risk = PredictionRecord.query.filter_by(risk_level="Medium").count()
    low_risk = PredictionRecord.query.filter_by(risk_level="Low").count()

    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago, User.role == "patient").count()
    predictions_week = PredictionRecord.query.filter(PredictionRecord.created_at >= week_ago).count()

    recent_predictions = PredictionRecord.query.order_by(PredictionRecord.created_at.desc()).limit(8).all()
    recent_users = User.query.filter_by(role="patient").order_by(User.created_at.desc()).limit(5).all()

    avg_confidence = db.session.query(db.func.avg(PredictionRecord.confidence)).scalar() or 0

    return render_template(
        "admin/dashboard.html",
        total_users=total_users, total_predictions=total_predictions,
        high_risk=high_risk, medium_risk=medium_risk, low_risk=low_risk,
        new_users_week=new_users_week, predictions_week=predictions_week,
        recent_predictions=recent_predictions, recent_users=recent_users,
        avg_confidence=round(avg_confidence, 1),
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    search = request.args.get("q", "").strip()
    query = User.query.filter_by(role="patient")
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(User.full_name.ilike(like), User.email.ilike(like)))
    all_users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, search=search)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f"{user.full_name} is now {'active' if user.is_active_account else 'deactivated'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin accounts cannot be deleted.", "danger")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash(f"{user.full_name}'s account and prediction history were deleted.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/predictions")
@login_required
@admin_required
def predictions():
    risk_filter = request.args.get("risk", "")
    query = PredictionRecord.query
    if risk_filter:
        query = query.filter_by(risk_level=risk_filter)
    records = query.order_by(PredictionRecord.created_at.desc()).limit(300).all()
    return render_template("admin/predictions.html", records=records, risk_filter=risk_filter)


@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    return render_template("admin/analytics.html")


@admin_bp.route("/export/predictions.csv")
@login_required
@admin_required
def export_predictions_csv():
    records = PredictionRecord.query.order_by(PredictionRecord.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Patient", "Email", "Age", "Gender", "Total Bilirubin", "Direct Bilirubin",
        "Alkaline Phosphatase", "ALT", "AST", "Total Protein", "Albumin", "A/G Ratio",
        "Prediction", "Risk Level", "Confidence (%)", "Date",
    ])
    for r in records:
        writer.writerow([
            r.id, r.user.full_name, r.user.email, r.age, r.gender, r.total_bilirubin,
            r.direct_bilirubin, r.alkaline_phosphotase, r.alt, r.ast, r.total_proteins,
            r.albumin, r.ag_ratio, r.prediction, r.risk_level, r.confidence,
            r.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    output = buf.getvalue()
    return Response(
        output, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=liverpredict_records.csv"},
    )


@admin_bp.route("/export/users.csv")
@login_required
@admin_required
def export_users_csv():
    users_list = User.query.filter_by(role="patient").all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Full Name", "Email", "Phone", "Age", "Gender", "Joined", "Total Predictions", "Active"])
    for u in users_list:
        writer.writerow([
            u.id, u.full_name, u.email, u.phone, u.age, u.gender,
            u.created_at.strftime("%Y-%m-%d"), u.predictions.count(), u.is_active_account,
        ])
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=liverpredict_users.csv"},
    )
