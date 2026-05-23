from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app import db
from app.models import User
from app.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app import limiter


logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _send_reset_email(user_email, reset_url):
    config = current_app.config
    mail_server = config.get("MAIL_SERVER", "")
    mail_port   = config.get("MAIL_PORT", 587)
    mail_user   = config.get("MAIL_USERNAME", "")
    mail_pass   = config.get("MAIL_PASSWORD", "")
    mail_from   = config.get("MAIL_FROM", mail_user)
    mail_name   = config.get("MAIL_FROM_NAME", "InvoiceBot")

    if not mail_user or not mail_pass:
        logger.warning("SMTP not configured")
        return False

    subject = "Reset your InvoiceBot password"
    body = f"""Hi,

You requested a password reset for your InvoiceBot account.

Click the link below to set a new password.
This link expires in 30 minutes.

{reset_url}

If you didn't request this, ignore this email.

— InvoiceBot · AINTORA SYSTEMS
"""
    msg = MIMEMultipart()
    msg["From"]    = f"{mail_name} <{mail_from}>"
    msg["To"]      = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login(mail_user, mail_pass)
        server.sendmail(mail_from, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Reset email failed: {e}")
        return False


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to InvoiceBot! Add your first invoice and let us do the chasing.", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if user.is_blocked:
                flash("This account has been blocked. Contact the admin.", "danger")
                return render_template("auth/login.html", form=form)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Invalid email or password. Please try again.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out. See you soon!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user  = User.query.filter_by(email=email).first()
        if user:
            s         = _get_serializer()
            token     = s.dumps(email, salt="password-reset")
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            _send_reset_email(email, reset_url)
        flash("If that email exists, a reset link has been sent. Check your inbox and spam.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # FIX: do NOT redirect logged-in users — they may reset while still logged in
    try:
        s     = _get_serializer()
        email = s.loads(token, salt="password-reset", max_age=1800)
    except SignatureExpired:
        flash("This reset link has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid or already used reset link. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        logout_user()
        flash("Password updated. Sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, email=email)