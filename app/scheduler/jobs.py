import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
_scheduler = None


def process_due_emails():
    """
    Runs every hour. Finds all unsent email schedules whose send_at <= now
    and fires them off. Skips invoices that are paid or cancelled.
    """
    from app import db
    from app.models import EmailSchedule, EmailLog, Invoice
    from app.email_service import send_invoice_reminder

    now = datetime.now(timezone.utc)
    logger.info(f"[Scheduler] Running email check at {now.isoformat()}")

    due_schedules = (
        EmailSchedule.query
        .join(Invoice)
        .filter(
            EmailSchedule.sent == False,
            EmailSchedule.send_at <= now,
            Invoice.status == "pending",
        )
        .all()
    )

    logger.info(f"[Scheduler] Found {len(due_schedules)} emails to send")

    for schedule in due_schedules:
        invoice = schedule.invoice
        success, msg_id, error = send_invoice_reminder(invoice, schedule.stage)

        log = EmailLog(
            invoice_id=invoice.id,
            stage=schedule.stage,
            subject=f"Stage {schedule.stage} reminder",
            sendgrid_message_id=msg_id,
            success=success,
            error=error,
        )
        db.session.add(log)

        if success:
            schedule.sent = True
            logger.info(f"[Scheduler] Sent stage {schedule.stage} for invoice {invoice.id}")
        else:
            logger.error(f"[Scheduler] Failed stage {schedule.stage} for invoice {invoice.id}: {error}")

    db.session.commit()


def start_scheduler(app):
    global _scheduler

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        func=lambda: app.app_context().__enter__() or process_due_emails(),
        trigger=IntervalTrigger(hours=1),
        id="process_due_emails",
        name="Process due invoice reminder emails",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    # Better pattern: use app context properly
    def run_with_context():
        with app.app_context():
            process_due_emails()

    _scheduler.add_job(
        func=run_with_context,
        trigger=IntervalTrigger(minutes=60),
        id="email_runner",
        name="Email runner",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    # Remove the broken lambda job
    _scheduler.remove_job("process_due_emails")

    _scheduler.start()
    logger.info("[Scheduler] Background scheduler started")
