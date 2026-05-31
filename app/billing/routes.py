import hmac as _hmac
import hashlib
import logging
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db, csrf
from app.models import User

billing_bp = Blueprint("billing", __name__)
logger = logging.getLogger(__name__)


@billing_bp.route("/upgrade")
@login_required
def upgrade():
    # Append user metadata to checkout URLs so webhook can identify the user
    base_starter = current_app.config.get("LS_STARTER_URL", "#")
    base_pro     = current_app.config.get("LS_PRO_URL", "#")

    def ls_url(base):
        if base == "#":
            return base
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}checkout[custom][user_id]={current_user.id}&checkout[custom][user_email]={current_user.email}"

    return render_template(
        "billing/upgrade.html",
        starter_url=ls_url(base_starter),
        pro_url=ls_url(base_pro),
    )


@billing_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def webhook():
    """Lemon Squeezy webhook — verify HMAC signature, update user plan."""
    secret    = current_app.config.get("LS_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Signature", "")
    payload   = request.data

    if secret:
        expected = _hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(expected, signature):
            logger.warning("LS webhook: invalid signature")
            return jsonify({"error": "Invalid signature"}), 400

    try:
        data       = json.loads(payload)
        event_name = data.get("meta", {}).get("event_name", "")
        attrs      = data.get("data", {}).get("attributes", {})
        meta       = data.get("meta", {}).get("custom_data", {}) or {}
    except Exception as e:
        logger.error(f"Webhook parse error: {e}")
        return jsonify({"error": "Bad payload"}), 400

    logger.info(f"LS event: {event_name} | meta={meta}")

    if event_name in ("subscription_created", "subscription_updated"):
        _handle_subscription_active(attrs, meta)
    elif event_name in ("subscription_cancelled", "subscription_expired"):
        _handle_subscription_downgrade(attrs, meta)
    elif event_name == "order_created":
        _handle_order_created(attrs, meta)

    return jsonify({"status": "ok"}), 200


def _get_user(meta, attrs=None):
    """Find user by custom_data user_id, then email."""
    user_id = (meta or {}).get("user_id")
    email   = (meta or {}).get("user_email")

    # Also try attrs for email
    if not email and attrs:
        email = attrs.get("user_email") or attrs.get("email")

    if user_id:
        u = User.query.get(str(user_id))
        if u:
            return u
    if email:
        return User.query.filter_by(email=email.lower()).first()
    return None


def _handle_subscription_active(attrs, meta):
    user = _get_user(meta, attrs)
    if not user:
        logger.warning(f"LS webhook: user not found — meta={meta}")
        return
    status       = attrs.get("status", "")
    variant_name = (attrs.get("product_name") or attrs.get("variant_name") or "").lower()
    sub_id       = str(attrs.get("id", ""))
    if status in ("active", "on_trial"):
        user.plan = "pro" if "pro" in variant_name else "starter"
        user.stripe_subscription_id = sub_id
        db.session.commit()
        logger.info(f"LS: {user.email} -> {user.plan} (sub {sub_id})")
        _send_upgrade_email(user)


def _handle_subscription_downgrade(attrs, meta):
    user = _get_user(meta, attrs)
    if user:
        user.plan = "free"
        user.stripe_subscription_id = None
        db.session.commit()
        logger.info(f"LS: {user.email} -> free")


def _handle_order_created(attrs, meta):
    """Handle one-time orders if applicable."""
    user = _get_user(meta, attrs)
    if user:
        logger.info(f"LS order_created for {user.email}")


def _send_upgrade_email(user):
    from app.email_service import send_mail
    plan_label = user.plan.title()
    send_mail(
        to_address=user.email,
        subject=f"You are now on the {plan_label} plan — InvoiceBot",
        body=f"""Hi {user.name or "there"},

Your InvoiceBot account has been upgraded to the {plan_label} plan.

{"You can now add up to 20 active invoices and export CSV reports." if user.plan == "starter" else "You now have unlimited invoices, PDF reports, and priority support."}

Go to your dashboard:
{current_app.config.get("APP_URL", "http://localhost:5000")}/dashboard/

Thank you for subscribing.

— Mohammed
InvoiceBot · AINTORA SYSTEMS
""",
        from_name=current_app.config.get("MAIL_FROM_NAME", "InvoiceBot"),
        from_email=current_app.config.get("MAIL_FROM", ""),
        email_type="upgrade",
    )


@billing_bp.route("/cancel")
@login_required
def cancel():
    if current_user.plan == "free":
        flash("You are already on the free plan.", "info")
        return redirect(url_for("billing.upgrade"))
    return render_template("billing/cancel.html")


@billing_bp.route("/cancel/confirm", methods=["POST"])
@login_required
def cancel_confirm():
    import requests as req
    reason     = request.form.get("reason", "").strip()
    sub_id     = current_user.stripe_subscription_id
    ls_api_key = current_app.config.get("LS_API_KEY", "")

    if sub_id and ls_api_key:
        try:
            resp = req.delete(
                f"https://api.lemonsqueezy.com/v1/subscriptions/{sub_id}",
                headers={
                    "Authorization": f"Bearer {ls_api_key}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json",
                },
                timeout=10,
            )
            logger.info(f"LS cancel: {resp.status_code} for {current_user.email}")
        except Exception as e:
            logger.error(f"LS cancel API error: {e}")

    current_user.plan = "free"
    current_user.stripe_subscription_id = None
    db.session.commit()
    _send_cancellation_email(current_user)
    logger.info(f"Cancelled: {current_user.email} reason={reason}")
    flash("Your subscription has been cancelled.", "info")
    return redirect(url_for("billing.cancelled"))


@billing_bp.route("/cancelled")
@login_required
def cancelled():
    return render_template("billing/cancelled.html",
        starter_url=current_app.config.get("LS_STARTER_URL", "#"),
        pro_url=current_app.config.get("LS_PRO_URL", "#"),
    )


def _send_cancellation_email(user):
    from app.email_service import send_mail
    send_mail(
        to_address=user.email,
        subject="Your InvoiceBot subscription has been cancelled",
        body=f"""Hi {user.name or "there"},

Your subscription has been cancelled. You are now on the free plan.

What changes:
- Maximum 3 active invoices
- CSV export unavailable
- PDF reports unavailable

Your data is safe. Resubscribe anytime:
{current_app.config.get("APP_URL", "http://localhost:5000")}/billing/upgrade

— Mohammed
InvoiceBot · AINTORA SYSTEMS
""",
        from_name=current_app.config.get("MAIL_FROM_NAME", "InvoiceBot"),
        from_email=current_app.config.get("MAIL_FROM", ""),
        email_type="cancellation",
    )
