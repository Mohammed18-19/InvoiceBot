from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app import db
from app.email_service import send_invoice_reminder
from app.models import Invoice, EmailSchedule, EmailLog

scheduler = BackgroundScheduler()
scheduler_started = False


def process_due_emails(app=None):
    """Send all due email schedules and create logs."""
    if app is None:
        from flask import current_app
        app = current_app

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

        for schedule in due_schedules:
            invoice = schedule.invoice
            if not invoice or invoice.status != "pending":
                schedule.sent = True
                db.session.commit()
                continue

            success, message_id, error = send_invoice_reminder(invoice, schedule.stage)
            email_log = EmailLog(
                invoice_id=invoice.id,
                stage=schedule.stage,
                subject=None,
                sendgrid_message_id=message_id,
                error=error,
                success=success,
            )
            db.session.add(email_log)

            if success:
                schedule.sent = True
            db.session.commit()

    return len(due_schedules)


def start_scheduler(app):
    """Start APScheduler to process due invoice emails every minute."""
    global scheduler_started
    if scheduler_started:
        return

    scheduler.configure(job_defaults={"coalesce": False, "max_instances": 1})
    scheduler.add_job(
        func=process_due_emails,
        trigger=IntervalTrigger(minutes=1),
        args=[app],
        id="process_due_emails",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    scheduler_started = True
