from urllib.parse import quote
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db, limiter
from app.models import User
from app.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.email_service import send_mail
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _send_verification_email(user):
    s = _get_serializer()
    token = s.dumps(user.email, salt="email-verify")
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    ok, _, err = send_mail(
        to_address=user.email,
        subject="Verify your InvoiceBot email",
        body=f"""Hi {user.name or "there"},

Please verify your email address by clicking the link below.
This link expires in 24 hours.

{verify_url}

If you did not create an account, ignore this email.

— InvoiceBot · AINTORA SYSTEMS
""",
        from_name=current_app.config.get("MAIL_FROM_NAME", "InvoiceBot"),
        from_email=current_app.config.get("MAIL_FROM", ""),
        email_type="verify",
    )
    return ok


def _send_reset_email(user_email, reset_url):
    ok, _, err = send_mail(
        to_address=user_email,
        subject="Reset your InvoiceBot password",
        body=f"""Hi,

You requested a password reset. This link expires in 30 minutes.

{reset_url}

If you did not request this, ignore this email.

— InvoiceBot · AINTORA SYSTEMS
""",
        from_name=current_app.config.get("MAIL_FROM_NAME", "InvoiceBot"),
        from_email=current_app.config.get("MAIL_FROM", ""),
        email_type="password_reset",
    )
    return ok


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            email_verified=False,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        _send_verification_email(user)
        from app.email_service import send_welcome_email
        send_welcome_email(user)
        login_user(user)
        flash("Welcome! Check your email to verify your account.", "success")
        return redirect(url_for("dashboard.home"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    try:
        s = _get_serializer()
        email = s.loads(token, salt="email-verify", max_age=86400)
    except SignatureExpired:
        flash("Verification link expired. Request a new one.", "danger")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash("Email verified! You are all set.", "success")
    return redirect(url_for("dashboard.home"))


@auth_bp.route("/resend-verification")
@login_required
def resend_verification():
    if current_user.email_verified:
        flash("Your email is already verified.", "info")
        return redirect(url_for("dashboard.home"))
    _send_verification_email(current_user)
    flash("Verification email sent. Check your inbox.", "info")
    return redirect(url_for("dashboard.home"))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if user.is_blocked:
                flash("This account has been blocked. Contact support.", "danger")
                return render_template("auth/login.html", form=form)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.home"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.landing"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user:
            s = _get_serializer()
            token = s.dumps([email, user.password_hash], salt="password-reset")
            reset_url = f"{url_for('auth.reset_password', _external=True)}?token={quote(token)}"
            logger.info(f"PASSWORD RESET LINK -> {reset_url}")
            _send_reset_email(email, reset_url)
        flash("If that email exists, a reset link has been sent.", "info")
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    token = (token or "").strip()
    if not token:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    try:
        s = _get_serializer()
        email, token_hash = s.loads(token, salt="password-reset", max_age=1800)
    except SignatureExpired:
        flash("Reset link expired.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except (BadSignature, ValueError):
        flash("Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    user = User.query.filter_by(email=email).first()
    if not user or user.password_hash != token_hash:
        flash("Invalid or already used reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        logout_user()
        flash("Password updated. Sign in with your new password.", "success")
        return redirect(url_for("auth.login"))
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
