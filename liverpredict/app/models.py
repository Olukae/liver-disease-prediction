import json
import secrets
from datetime import datetime, timedelta

from flask_login import UserMixin

from app.extensions import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="patient")  # 'patient' or 'admin'
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)

    predictions = db.relationship(
        "PredictionRecord", backref="user", lazy="dynamic",
        cascade="all, delete-orphan", order_by="desc(PredictionRecord.created_at)"
    )

    # --- password helpers ------------------------------------------------
    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    # --- password reset ----------------------------------------------
    def generate_reset_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return token

    def verify_reset_token(self, token: str) -> bool:
        return (
            self.reset_token == token
            and self.reset_token_expiry is not None
            and self.reset_token_expiry > datetime.utcnow()
        )

    def clear_reset_token(self):
        self.reset_token = None
        self.reset_token_expiry = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def initials(self) -> str:
        parts = self.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.full_name[:2].upper() if self.full_name else "U"

    def __repr__(self):
        return f"<User {self.email}>"


class PredictionRecord(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Test parameters
    age = db.Column(db.Float)
    gender = db.Column(db.String(10))
    total_bilirubin = db.Column(db.Float)
    direct_bilirubin = db.Column(db.Float)
    alkaline_phosphotase = db.Column(db.Float)
    alt = db.Column(db.Float)
    ast = db.Column(db.Float)
    total_proteins = db.Column(db.Float)
    albumin = db.Column(db.Float)
    ag_ratio = db.Column(db.Float)

    # Result
    prediction = db.Column(db.String(20))       # 'Disease Detected' / 'No Disease Detected'
    risk_level = db.Column(db.String(20))        # Low / Medium / High
    confidence = db.Column(db.Float)              # 0-100
    probability_disease = db.Column(db.Float)     # raw model probability
    contributing_factors = db.Column(db.Text)     # JSON list
    recommendations = db.Column(db.Text)          # JSON list
    interpretation = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    report_filename = db.Column(db.String(255))

    def factors_list(self):
        try:
            return json.loads(self.contributing_factors) if self.contributing_factors else []
        except (TypeError, ValueError):
            return []

    def recommendations_list(self):
        try:
            return json.loads(self.recommendations) if self.recommendations else []
        except (TypeError, ValueError):
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "age": self.age,
            "gender": self.gender,
            "total_bilirubin": self.total_bilirubin,
            "direct_bilirubin": self.direct_bilirubin,
            "alkaline_phosphotase": self.alkaline_phosphotase,
            "alt": self.alt,
            "ast": self.ast,
            "total_proteins": self.total_proteins,
            "albumin": self.albumin,
            "ag_ratio": self.ag_ratio,
            "prediction": self.prediction,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "factors": self.factors_list(),
            "recommendations": self.recommendations_list(),
            "interpretation": self.interpretation,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

    def __repr__(self):
        return f"<PredictionRecord {self.id} user={self.user_id} risk={self.risk_level}>"
