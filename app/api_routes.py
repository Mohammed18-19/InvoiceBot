"""
REST API routes consumed by the React dashboard (frontend/).
All routes require login and return JSON.
"""
from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timezone
from app import db, csrf
from app.models import Invoice, EmailSchedule, EmailLog

api_bp = Blueprint("api", __name__, url_prefix="/api")
csrf.exempt(api_bp)


def invoice_to_dict(inv: Invoice) -> dict:
    schedules = inv.email_schedules.order_by(EmailSchedule.send_at).all()
    logs = inv.email_logs.order_by(EmailLog.sent_at.desc()).all()
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number or f"INV-{inv.id[:8].upper()}",
        "client_name": inv.client_name,
        "client_email": inv.client_email,
        "amount": str(inv.amount),
        "currency": inv.currency,
        "due_date": inv.due_date.isoformat(),
        "status": inv.status,
        "description": inv.description,
        "payment_link": inv.payment_link,
        "tone": inv.tone,
        "stage1_delay": inv.stage1_delay,
        "stage2_delay": inv.stage2_delay,
        "stage3_delay": inv.stage3_delay,
        "created_at": inv.created_at.isoformat(),
        "marked_paid_at": inv.marked_paid_at.isoformat() if inv.marked_paid_at else None,
        "days_overdue": inv.days_overdue,
        "sent_emails_count": inv.sent_emails_count,
        "schedules": [{"id": s.id, "stage": s.stage, "send_at": s.send_at.isoformat(), "sent": s.sent} for s in schedules],
        "logs": [{"id": l.id, "stage": l.stage, "subject": l.subject, "sent_at": l.sent_at.isoformat(), "success": l.success} for l in logs],
    }


@api_bp.route("/invoices", methods=["GET"])
@login_required
def list_invoices():
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()
    return jsonify([invoice_to_dict(inv) for inv in invoices])


@api_bp.route("/invoices/<inv_id>", methods=["GET"])
@login_required
def get_invoice(inv_id):
    inv = Invoice.query.filter_by(id=inv_id, user_id=current_user.id).first_or_404()
    return jsonify(invoice_to_dict(inv))


@api_bp.route("/invoices/<inv_id>/mark-paid", methods=["POST"])
@login_required
def mark_paid(inv_id):
    inv = Invoice.query.filter_by(id=inv_id, user_id=current_user.id).first_or_404()
    if inv.status != "paid":
        inv.status = "paid"
        inv.marked_paid_at = datetime.now(timezone.utc)
        EmailSchedule.query.filter_by(invoice_id=inv.id, sent=False).delete()
        db.session.commit()
    return jsonify({"ok": True, "invoice": invoice_to_dict(inv)})


@api_bp.route("/stats", methods=["GET"])
@login_required
def stats():
    invoices = Invoice.query.filter_by(user_id=current_user.id).all()
    today = date.today()
    pending = [i for i in invoices if i.status == "pending"]
    overdue = [i for i in pending if i.due_date < today]
    paid = [i for i in invoices if i.status == "paid"]
    emails_sent = EmailLog.query.join(Invoice).filter(Invoice.user_id == current_user.id).count()
    return jsonify({
        "total": len(invoices),
        "pending": len(pending),
        "overdue": len(overdue),
        "paid": len(paid),
        "total_outstanding": sum(float(i.amount) for i in pending),
        "emails_sent": emails_sent,
        "plan": current_user.plan,
        "name": current_user.name or current_user.email.split("@")[0],
        "language": current_user.language,
    })
