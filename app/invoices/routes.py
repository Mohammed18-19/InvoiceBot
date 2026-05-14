from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from app import db
from app.models import Invoice, EmailSchedule, EmailLog
from app.invoices.forms import InvoiceForm

invoices_bp = Blueprint("invoices", __name__)


def _create_email_schedules(invoice):
    """Create the 3-stage email schedule based on due date + delay config."""
    from datetime import date, time

    base_date = invoice.due_date
    delays = [invoice.stage1_delay, invoice.stage2_delay, invoice.stage3_delay]

    for stage, delay in enumerate(delays, start=1):
        send_date = base_date + timedelta(days=delay)
        # Send at 09:00 UTC
        send_at = datetime.combine(send_date, time(9, 0), tzinfo=timezone.utc)
        schedule = EmailSchedule(
            invoice_id=invoice.id,
            stage=stage,
            send_at=send_at,
            sent=False,
        )
        db.session.add(schedule)


@invoices_bp.route("/")
@login_required
def list_invoices():
    status_filter = request.args.get("status", "all")
    query = Invoice.query.filter_by(user_id=current_user.id)
    if status_filter in ("pending", "paid", "cancelled"):
        query = query.filter_by(status=status_filter)
    invoices = query.order_by(Invoice.created_at.desc()).all()
    return render_template("invoices/list.html", invoices=invoices, status_filter=status_filter)


@invoices_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_invoice():
    if not current_user.can_add_invoice:
        flash(
            f"You've reached the {current_user.invoice_limit} active invoice limit on the {current_user.plan.title()} plan. "
            "Upgrade to add more.",
            "warning",
        )
        return redirect(url_for("billing.upgrade"))

    form = InvoiceForm()
    if form.validate_on_submit():
        invoice = Invoice(
            user_id=current_user.id,
            client_name=form.client_name.data.strip(),
            client_email=form.client_email.data.lower().strip(),
            invoice_number=form.invoice_number.data.strip() if form.invoice_number.data else None,
            amount=form.amount.data,
            currency=form.currency.data,
            due_date=form.due_date.data,
            description=form.description.data,
            payment_link=form.payment_link.data.strip() if form.payment_link.data else None,
            tone=form.tone.data,
            stage1_delay=form.stage1_delay.data,
            stage2_delay=form.stage2_delay.data,
            stage3_delay=form.stage3_delay.data,
        )
        db.session.add(invoice)
        db.session.flush()  # get invoice.id before creating schedules
        _create_email_schedules(invoice)
        db.session.commit()
        flash(f"Invoice for {invoice.client_name} added. Reminders scheduled.", "success")
        return redirect(url_for("invoices.detail", invoice_id=invoice.id))

    return render_template("invoices/new.html", form=form)


@invoices_bp.route("/<invoice_id>")
@login_required
def detail(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    schedules = invoice.email_schedules.order_by(EmailSchedule.stage).all()
    logs = invoice.email_logs.order_by(EmailLog.sent_at.desc()).all()
    return render_template("invoices/detail.html", invoice=invoice, schedules=schedules, logs=logs)


@invoices_bp.route("/<invoice_id>/mark-paid", methods=["POST"])
@login_required
def mark_paid(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    invoice.status = "paid"
    invoice.marked_paid_at = datetime.now(timezone.utc)
    # Cancel unsent schedules
    invoice.email_schedules.filter_by(sent=False).update({"sent": True})
    db.session.commit()
    flash(f"Invoice marked as paid. No more reminders will be sent.", "success")
    return redirect(url_for("invoices.detail", invoice_id=invoice_id))


@invoices_bp.route("/<invoice_id>/cancel", methods=["POST"])
@login_required
def cancel_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    invoice.status = "cancelled"
    invoice.email_schedules.filter_by(sent=False).update({"sent": True})
    db.session.commit()
    flash("Invoice cancelled. Reminders stopped.", "info")
    return redirect(url_for("invoices.list_invoices"))


@invoices_bp.route("/<invoice_id>/delete", methods=["POST"])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    db.session.delete(invoice)
    db.session.commit()
    flash("Invoice deleted.", "info")
    return redirect(url_for("invoices.list_invoices"))
