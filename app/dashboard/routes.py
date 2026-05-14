from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Invoice, EmailLog
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    invoices = (
        Invoice.query
        .filter_by(user_id=current_user.id)
        .order_by(Invoice.created_at.desc())
        .all()
    )

    stats = {
        "total": len(invoices),
        "pending": sum(1 for i in invoices if i.status == "pending"),
        "paid": sum(1 for i in invoices if i.status == "paid"),
        "overdue": sum(1 for i in invoices if i.days_overdue > 0),
        "emails_sent": (
            db.session.query(func.count(EmailLog.id))
            .join(Invoice)
            .filter(Invoice.user_id == current_user.id, EmailLog.success == True)
            .scalar() or 0
        ),
        "total_outstanding": sum(
            float(i.amount) for i in invoices if i.status == "pending"
        ),
    }

    recent_logs = (
        EmailLog.query
        .join(Invoice)
        .filter(Invoice.user_id == current_user.id)
        .order_by(EmailLog.sent_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        invoices=invoices[:5],
        stats=stats,
        recent_logs=recent_logs,
    )
