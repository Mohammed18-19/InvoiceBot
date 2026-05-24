# app/debug_routes.py  ← TEMPORARY, delete after confirming emails work
from flask import Blueprint, jsonify, current_app
from flask_login import login_required, current_user
from app.email_service import send_mail

debug_bp = Blueprint("debug", __name__)

@debug_bp.route("/debug/test-email")
@login_required
def test_email():
    ok, provider, err = send_mail(
        to_address=current_user.email,
        subject="InvoiceBot email test",
        body="If you see this, emails are working!",
        from_name=current_app.config.get("MAIL_FROM_NAME", "InvoiceBot"),
        from_email=current_app.config.get("MAIL_FROM", ""),
        email_type="debug",
    )
    return jsonify({
        "success": ok,
        "provider": provider,
        "error": err,
        "email_mode": current_app.config.get("EMAIL_MODE"),
        "mail_server": current_app.config.get("MAIL_SERVER"),
        "mail_from": current_app.config.get("MAIL_FROM"),
    })