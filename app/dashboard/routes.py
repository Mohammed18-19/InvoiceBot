from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def home():
    from app.models import Invoice, EmailLog
    from app import db

    invoices = Invoice.query.filter_by(user_id=current_user.id).all()

    total    = len(invoices)
    pending  = [inv for inv in invoices if inv.status == "pending"]
    overdue  = [inv for inv in pending if inv.due_date < date.today()]
    paid     = [inv for inv in invoices if inv.status == "paid"]

    total_outstanding = sum(float(inv.amount) for inv in pending)
    emails_sent = EmailLog.query.join(Invoice).filter(Invoice.user_id == current_user.id).count()

    recent_invoices = Invoice.query.filter_by(user_id=current_user.id)        .order_by(Invoice.created_at.desc()).limit(5).all()

    recent_logs = EmailLog.query.join(Invoice)        .filter(Invoice.user_id == current_user.id)        .order_by(EmailLog.sent_at.desc()).limit(5).all()

    stats = {
        "total":             total,
        "pending":           len(pending),
        "overdue":           len(overdue),
        "paid":              len(paid),
        "total_outstanding": total_outstanding,
        "emails_sent":       emails_sent,
        "reminders_sent":    emails_sent,
    }

    return render_template("dashboard/index.html",
        stats=stats,
        recent_invoices=recent_invoices,
        recent_logs=recent_logs,
    )


@dashboard_bp.route("/landing")
def landing():
    return redirect(url_for("main.landing"))
