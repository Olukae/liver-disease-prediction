import json
import os
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    current_app, send_file, abort
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import PredictionRecord
from app.forms import PredictionForm
from ml.predictor import predict
from utils.pdf_report import generate_pdf_report

prediction_bp = Blueprint("prediction", __name__, url_prefix="/prediction")


@prediction_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = PredictionForm()
    if form.validate_on_submit():
        gender_label = "Male" if form.gender.data == "1" else "Female"
        payload = {
            "age": form.age.data,
            "gender": int(form.gender.data),
            "total_bilirubin": form.total_bilirubin.data,
            "direct_bilirubin": form.direct_bilirubin.data,
            "alkaline_phosphotase": form.alkaline_phosphotase.data,
            "alt": form.alt.data,
            "ast": form.ast.data,
            "total_proteins": form.total_proteins.data,
            "albumin": form.albumin.data,
            "ag_ratio": form.ag_ratio.data,
        }
        result = predict(current_app, payload)

        record = PredictionRecord(
            user_id=current_user.id,
            age=payload["age"], gender=gender_label,
            total_bilirubin=payload["total_bilirubin"],
            direct_bilirubin=payload["direct_bilirubin"],
            alkaline_phosphotase=payload["alkaline_phosphotase"],
            alt=payload["alt"], ast=payload["ast"],
            total_proteins=payload["total_proteins"],
            albumin=payload["albumin"], ag_ratio=payload["ag_ratio"],
            prediction=result["prediction"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            probability_disease=result["probability_disease"],
            contributing_factors=json.dumps(result["factors"]),
            recommendations=json.dumps(result["recommendations"]),
            interpretation=result["interpretation"],
        )
        db.session.add(record)
        db.session.commit()
        return redirect(url_for("prediction.result", record_id=record.id))

    return render_template("prediction/form.html", form=form)


@prediction_bp.route("/result/<int:record_id>")
@login_required
def result(record_id):
    record = PredictionRecord.query.get_or_404(record_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("prediction/result.html", record=record)


@prediction_bp.route("/history")
@login_required
def history():
    query = current_user.predictions

    search = request.args.get("q", "").strip()
    risk_filter = request.args.get("risk", "")
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")

    records = query.all()

    if search:
        records = [r for r in records if search.lower() in (r.prediction or "").lower()
                   or search.lower() in (r.interpretation or "").lower()]
    if risk_filter:
        records = [r for r in records if r.risk_level == risk_filter]
    if date_from:
        try:
            d = datetime.strptime(date_from, "%Y-%m-%d")
            records = [r for r in records if r.created_at >= d]
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, "%Y-%m-%d")
            records = [r for r in records if r.created_at.date() <= d.date()]
        except ValueError:
            pass

    return render_template(
        "prediction/history.html", records=records,
        search=search, risk_filter=risk_filter, date_from=date_from, date_to=date_to,
    )


@prediction_bp.route("/report/<int:record_id>")
@login_required
def download_report(record_id):
    record = PredictionRecord.query.get_or_404(record_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    filename = f"liver_report_{record.id}_{int(datetime.utcnow().timestamp())}.pdf"
    output_path = os.path.join(current_app.config["REPORTS_DIR"], filename)
    generate_pdf_report(record, record.user, output_path)

    record.report_filename = filename
    db.session.commit()

    return send_file(output_path, as_attachment=True,
                      download_name=f"LiverPredict_Report_{record.id}.pdf")
