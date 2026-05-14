import hmac
import hashlib
import logging
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User

billing_bp = Blueprint("billing", __name__)
logger = logging.getLogger(__name__)


@billing_bp.route("/upgrade")
@login_required
def upgrade():
    return render_template(
        "billing/upgrade.html",
        starter_url=current_app.config.get("LS_STARTER_URL", "#"),
        pro_url=current_app.config.get("LS_PRO_URL", "#"),
    )


@billing_bp.route("/webhook", methods=["POST"])
def webhook():
    """Lemon Squeezy webhook — verify signature, update user plan."""
    secret    = current_app.config.get("LS_WEBHOOK_SECRET", "")
    signature = request.headers.get("X-Signature", "")
    payload   = request.data

    if secret:
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            logger.warning("Lemon Squeezy webhook: invalid signature")
            return jsonify({"error": "Invalid signature"}), 400

    try:
        data       = json.loads(payload)
        event_name = data.get("meta", {}).get("event_name", "")
        attrs      = data.get("data", {}).get("attributes", {})
        meta       = data.get("meta", {}).get("custom_data", {})
    except Exception as e:
        logger.error(f"Webhook parse error: {e}")
        return jsonify({"error": "Bad payload"}), 400

    logger.info(f"Lemon Squeezy event: {event_name}")

    if event_name in ("subscription_created", "subscription_updated"):
        _handle_subscription_active(attrs, meta)
    elif event_name in ("subscription_cancelled", "subscription_expired"):
        _handle_subscription_downgrade(attrs, meta)

    return jsonify({"status": "ok"}), 200


def _get_user(meta):
    user_id = meta.get("user_id")
    email   = meta.get("user_email")
    if user_id:
        return User.query.get(user_id)
    if email:
        return User.query.filter_by(email=email).first()
    return None


def _handle_subscription_active(attrs, meta):
    user = _get_user(meta)
    if not user:
        logger.warning(f"Webhook: user not found — meta={meta}")
        return
    status       = attrs.get("status", "")
    variant_name = attrs.get("variant_name", "").lower()
    sub_id       = str(attrs.get("id", ""))
    if status == "active":
        user.plan = "pro" if "pro" in variant_name else "starter"
        user.stripe_subscription_id = sub_id
        db.session.commit()
        logger.info(f"User {user.email} → plan: {user.plan}")


def _handle_subscription_downgrade(attrs, meta):
    user = _get_user(meta)
    if user:
        user.plan = "free"
        user.stripe_subscription_id = None
        db.session.commit()
        logger.info(f"User {user.email} → free (subscription ended)")
