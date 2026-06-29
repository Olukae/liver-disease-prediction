import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- Database -----------------------------------------------------
    # Defaults to local SQLite so the app runs out-of-the-box with zero
    # setup. To use MySQL in production, set DATABASE_URL, e.g.:
    #   mysql+pymysql://user:password@localhost:3306/liver_predict
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'liverpredict.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth / sessions -------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_TIME_LIMIT = None

    # --- Mail (optional, used for password reset / result notifications) -
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "1") == "1"

    # --- App paths ---------------------------------------------------
    _ml_dir = os.path.join(BASE_DIR, "ml")
    ML_MODEL_PATH = os.path.join(_ml_dir, "liver_model.joblib")
    ML_META_PATH = os.path.join(_ml_dir, "model_meta.json")
    REPORTS_DIR = os.path.join(BASE_DIR, "instance", "reports")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@liverpredict.ai")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
