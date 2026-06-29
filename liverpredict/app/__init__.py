import os

from flask import Flask

from config import config_map
from app.extensions import db, login_manager, bcrypt, mail, csrf  # add csrf

def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map.get(env, config_map["default"]))

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["REPORTS_DIR"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)      
    

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Blueprints ----------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.prediction import prediction_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # --- Template helpers -----------------------------------------------
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year, "app_name": "LiverPredict AI"}

    @app.template_filter("riskcolor")
    def riskcolor(level):
        return {"Low": "success", "Medium": "warning", "High": "danger"}.get(level, "secondary")

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    with app.app_context():
        db.create_all()
        _ensure_admin(app)

    return app


def _ensure_admin(app):
    """Create a default admin account on first run, if none exists."""
    from app.models import User

    if not User.query.filter_by(role="admin").first():
        admin = User(
            full_name="System Administrator",
            email=app.config["ADMIN_EMAIL"],
            phone="",
            age=None,
            gender="Other",
            role="admin",
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        app.logger.info(
            f"Created default admin account: {app.config['ADMIN_EMAIL']} / "
            f"{app.config['ADMIN_PASSWORD']} (change this immediately)"
        )
