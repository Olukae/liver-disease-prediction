"""
Seed script: populates the database with demo patients and predictions.
Run:  python seed.py
"""
import json
import random
from datetime import datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import User, PredictionRecord
from ml.predictor import predict

app = create_app()

PATIENTS = [
    ("Adeola Okonkwo", "adeola@example.com", "+234-802-123-4567", 38, "Female"),
    ("Chidi Eze", "chidi@example.com", "+234-703-987-6543", 54, "Male"),
    ("Priya Sharma", "priya@example.com", "+91-9876-543210", 43, "Female"),
    ("James Osei", "james@example.com", "+233-244-111-222", 60, "Male"),
    ("Fatima Al-Hassan", "fatima@example.com", "+234-814-000-111", 29, "Female"),
]

CASE_PROFILES = [
    # (total_bil, direct_bil, alkphos, alt, ast, proteins, albumin, ag_ratio)
    (0.7, 0.1, 187, 16, 18, 6.8, 3.3, 0.9),   # healthy
    (10.9, 5.5, 699, 64, 100, 7.5, 3.2, 0.74), # diseased
    (3.9, 2.0, 195, 27, 59, 7.3, 2.4, 0.4),    # moderate
    (1.0, 0.4, 182, 14, 20, 6.8, 3.4, 1.0),    # healthy
    (7.3, 4.1, 490, 60, 68, 7.0, 3.3, 0.89),   # diseased
    (0.9, 0.2, 200, 22, 28, 6.5, 3.6, 1.1),    # healthy
    (5.5, 2.8, 350, 80, 110, 6.2, 2.8, 0.65),  # diseased
]


def seed():
    with app.app_context():
        for name, email, phone, age, gender in PATIENTS:
            if not User.query.filter_by(email=email).first():
                u = User(full_name=name, email=email, phone=phone, age=age, gender=gender, role="patient")
                u.set_password("Demo@12345")
                db.session.add(u)
        db.session.commit()
        print("Patients seeded.")

        patients = User.query.filter_by(role="patient").all()
        if PredictionRecord.query.count() < 10:
            for i in range(25):
                u = random.choice(patients)
                p = random.choice(CASE_PROFILES)
                gender_val = 1 if u.gender == "Male" else 0
                payload = {
                    "age": u.age + random.randint(-3, 3),
                    "gender": gender_val,
                    "total_bilirubin": p[0], "direct_bilirubin": p[1],
                    "alkaline_phosphotase": p[2], "alt": p[3], "ast": p[4],
                    "total_proteins": p[5], "albumin": p[6], "ag_ratio": p[7],
                }
                result = predict(app, payload)
                offset_days = random.randint(0, 60)
                created = datetime.utcnow() - timedelta(days=offset_days, hours=random.randint(0, 23))

                rec = PredictionRecord(
                    user_id=u.id,
                    age=payload["age"], gender=u.gender,
                    total_bilirubin=p[0], direct_bilirubin=p[1],
                    alkaline_phosphotase=p[2], alt=p[3], ast=p[4],
                    total_proteins=p[5], albumin=p[6], ag_ratio=p[7],
                    prediction=result["prediction"], risk_level=result["risk_level"],
                    confidence=result["confidence"], probability_disease=result["probability_disease"],
                    contributing_factors=json.dumps(result["factors"]),
                    recommendations=json.dumps(result["recommendations"]),
                    interpretation=result["interpretation"],
                    created_at=created,
                )
                db.session.add(rec)
            db.session.commit()
            print(f"Seeded 25 demo predictions.")
        else:
            print("Predictions already seeded — skipping.")

        print("\nDemo credentials:")
        print(f"  Admin  : admin@liverpredict.ai / Admin@12345")
        print(f"  Patient: adeola@example.com / Demo@12345")


if __name__ == "__main__":
    seed()
