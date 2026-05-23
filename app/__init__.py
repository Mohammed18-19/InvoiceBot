from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from config import config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.before_request
    def enforce_account_status():
        if current_user.is_authenticated and getattr(current_user, "is_blocked", False):
            logout_user()
            flash("Your account has been blocked. Contact the admin.", "danger")
            return redirect(url_for("auth.login"))
    if config_name == "production":
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            session_cookie_secure=True,
            content_security_policy=False,
        )

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.invoices.routes import invoices_bp
    from app.billing.routes import billing_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(invoices_bp, url_prefix="/invoices")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Start background scheduler
    from app.scheduler.jobs import start_scheduler
    start_scheduler(app)

    return app
