from datetime import datetime, timezone
import logging

from app import db
from app.email_service import send_invoice_reminder
from app.models import Invoice, EmailSchedule, EmailLog

logger = logging.getLogger(__name__)


def process_due_emails(app=None):
    """Send all due email schedules. Works both from APScheduler and cron endpoint."""
    if app is None:
        from flask import current_app
        app = current_app._get_current_object()

    with app.app_context():
        now = datetime.now(timezone.utc)
        due_schedules = (
            EmailSchedule.query
            .join(Invoice)
            .filter(
                EmailSchedule.sent == False,
                EmailSchedule.send_at <= now,
                Invoice.status == "pending",
            )
            .order_by(EmailSchedule.send_at)
            .all()
        )

        sent_count = 0
        for schedule in due_schedules:
            invoice = schedule.invoice
            if not invoice or invoice.status != "pending":
                schedule.sent = True
                db.session.commit()
                continue

            success, message_id, error = send_invoice_reminder(invoice, schedule.stage)
            log = EmailLog(
                invoice_id=invoice.id,
                stage=schedule.stage,
                subject=None,
                sendgrid_message_id=message_id,
                error=error,
                success=success,
            )
            db.session.add(log)
            if success:
                schedule.sent = True
                sent_count += 1
            db.session.commit()

        logger.info(f"process_due_emails: {sent_count}/{len(due_schedules)} sent")
        return sent_count, len(due_schedules)


def start_scheduler(app):
    """Start APScheduler for local dev. On Railway, the cron endpoint handles this."""
    import os
    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("USE_CRON_ENDPOINT"):
        logger.info("Scheduler: using cron endpoint mode (APScheduler disabled)")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler()
        scheduler.configure(job_defaults={"coalesce": True, "max_instances": 1})
        scheduler.add_job(
            func=process_due_emails,
            trigger=IntervalTrigger(minutes=1),
            args=[app],
            id="process_due_emails",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
        logger.info("APScheduler started (local dev mode)")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")
