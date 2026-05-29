from urllib.parse import quote

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db
from app.models import User
from app.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
import logging
from app import limiter
from app.email_service import send_mail


logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _normalize_app_url(app_url):
    app_url = (app_url or "").strip()
    if not app_url.startswith(("http://", "https://")):
        app_url = f"https://{app_url}"
    return app_url.rstrip("/")


def _send_reset_email(user_email, reset_url):
    mail_user = current_app.config.get("MAIL_USERNAME", "")
    mail_from = current_app.config.get("MAIL_FROM", mail_user)
    mail_name = current_app.config.get("MAIL_FROM_NAME", "InvoiceBot")

    subject = "Reset your InvoiceBot password"
    body = f"""Hi,

You requested a password reset for your InvoiceBot account.

Click the link below to set a new password.
This link expires in 30 minutes.

{reset_url}

If you didn't request this, ignore this email.

— InvoiceBot · AINTORA SYSTEMS
"""

    ok, provider, err = send_mail(
        to_address=user_email,
        subject=subject,
        body=body,
        from_name=mail_name,
        from_email=mail_from,
        invoice_id=None,
        email_type="password_reset",
    )

    if not ok:
        logger.error(f"Reset email failed: {err}")
        return False
    return True


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        from app.email_service import send_welcome_email
        send_welcome_email(user)
        from app.email_service import send_welcome_email
        send_welcome_email(user)
        login_user(user)
        flash("Welcome to InvoiceBot! Add your first invoice and let us do the chasing.", "success")
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    from flask_login import current_user
    from flask import redirect, url_for
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.landing"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if user.is_blocked:
                flash("This account has been blocked. Contact the admin.", "danger")
                return render_template("auth/login.html", form=form)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.home"))
        flash("Invalid email or password. Please try again.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out. See you soon!", "info")
    return redirect("/landing")

    logout_user()
    flash("You have been logged out. See you soon!", "info")
    return redirect(url_for("dashboard.landing"))

    logout_user()
    return redirect(url_for("auth.login"))
    logout_user()
    flash("You've been logged out. See you soon!", "info")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user  = User.query.filter_by(email=email).first()
        if user:
            logger.info("Password reset requested for email=%s", email)
            s         = _get_serializer()
            token     = s.dumps([email, user.password_hash], salt="password-reset")
            reset_url = f"{url_for('auth.reset_password', _external=True)}?token={quote(token)}"

            logger.info(f"PASSWORD RESET LINK → {reset_url}")

            # Always attempt to send the reset email. In dev you can set
            # EMAIL_MODE=test to log instead of sending, or use real SMTP
            # credentials to test actual delivery.
            ok = _send_reset_email(email, reset_url)
            if not ok:
                logger.warning("Reset email could not be sent; link still logged for manual use")

        flash("If that email exists, a reset link has been sent. Check your inbox and spam.", "info")
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    token = (token or "").strip()

    if not token:
        flash("Invalid or already used reset link. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    logger.info("Reset password token received: %s", token)

    try:
        s                 = _get_serializer()
        email, token_hash = s.loads(token, salt="password-reset", max_age=1800)
    except SignatureExpired:
        flash("This reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except (BadSignature, ValueError):
        flash("Invalid or already used reset link. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.forgot_password"))

    # Single-use: if password already changed, token hash won't match
    if user.password_hash != token_hash:
        flash("This reset link has already been used. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        logout_user()
        flash("Password updated. Sign in with your new password.", "success")

    return render_template("auth/reset_password.html", form=form, email=email, token=token)


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    from app.auth.forms import SettingsForm
    form = SettingsForm(obj=current_user)
    if request.method == "GET":
        form.language.data = current_user.language or "en"
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.company = form.company.data.strip() if form.company.data else None
        current_user.default_payment_link = form.default_payment_link.data.strip() if form.default_payment_link.data else None
        current_user.language = form.language.data
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("auth.settings"))
    return render_template("auth/settings.html", form=form)
