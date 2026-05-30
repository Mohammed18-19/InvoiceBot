import logging
from flask import Blueprint, jsonify, request, current_app
from app import csrf

cron_bp = Blueprint("cron", __name__)
logger = logging.getLogger(__name__)


@cron_bp.route("/cron/process-emails", methods=["POST", "GET"])
@csrf.exempt
def process_emails():
    """
    Protected cron endpoint.
    Railway Cron calls: POST /cron/process-emails
    Secured by CRON_SECRET header.
    """
    secret = current_app.config.get("CRON_SECRET", "")
    if secret:
        provided = request.headers.get("X-Cron-Secret", "") or request.args.get("secret", "")
        if provided != secret:
            logger.warning("Cron endpoint: invalid secret")
            return jsonify({"error": "Unauthorized"}), 401

    try:
        from app.scheduler.jobs import process_due_emails
        sent, total = process_due_emails(current_app._get_current_object())
        logger.info(f"Cron: processed {total} schedules, sent {sent}")
        return jsonify({"status": "ok", "sent": sent, "total": total}), 200
    except Exception as e:
        logger.exception("Cron endpoint error")
        return jsonify({"error": str(e)}), 500
