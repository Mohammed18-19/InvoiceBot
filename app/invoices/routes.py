from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, timezone

from app import db
from app.models import Invoice, EmailSchedule, EmailLog
from app.invoices.forms import InvoiceForm
from app.scheduler.jobs import process_due_emails

invoices_bp = Blueprint("invoices", __name__)


def _create_email_schedules(invoice):
    """Create the 3-stage email schedule based on due date + delay config."""
    from datetime import date, time

    base_date = invoice.due_date
    delays = [invoice.stage1_delay, invoice.stage2_delay, invoice.stage3_delay]

    for stage, delay in enumerate(delays, start=1):
        send_date = base_date + timedelta(days=delay)
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
        db.session.flush()
        _create_email_schedules(invoice)
        db.session.commit()

        overdue_schedules = invoice.email_schedules.filter(
            EmailSchedule.sent == False,
            EmailSchedule.send_at <= datetime.now(timezone.utc),
        ).count()

        if overdue_schedules:
            process_due_emails()
            flash(f"Invoice for {invoice.client_name} added. Overdue reminder is being sent now.", "success")
        else:
            flash(f"Invoice for {invoice.client_name} added. Reminders scheduled.", "success")

        return redirect(url_for("invoices.detail", invoice_id=invoice.id))

    if request.method == "GET" and current_user.default_payment_link:
        form.payment_link.data = current_user.default_payment_link
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


@invoices_bp.route("/<invoice_id>/preview-email/<int:stage>")
@login_required
def preview_email(invoice_id, stage):
    from app.email_service import _render_template, _build_payment_section
    from datetime import date
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()
    due_date_str = invoice.due_date.strftime("%B %d, %Y")
    days_overdue = max((date.today() - invoice.due_date).days, 0)
    sender_name = current_user.name or current_user.email
    if current_user.company:
        sender_name = f"{sender_name} — {current_user.company}"
    context = {
        "client_name":     invoice.client_name,
        "invoice_number":  invoice.invoice_number or invoice.id[:8].upper(),
        "amount":          f"{float(invoice.amount):,.2f}",
        "currency":        invoice.currency,
        "due_date":        due_date_str,
        "days_overdue":    days_overdue,
        "sender_name":     sender_name,
        "payment_section": _build_payment_section(invoice.payment_link),
    }
    language = getattr(current_user, "language", "en") or "en"
    subject, body = _render_template(invoice.tone, stage, context, language=language)
    return render_template("invoices/preview_email.html",
        invoice=invoice, stage=stage, subject=subject, body=body)


@invoices_bp.route("/report")
@login_required
def report():
    from datetime import date
    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()

    # Stats
    total_invoiced  = sum(float(inv.amount) for inv in invoices)
    total_collected = sum(float(inv.amount) for inv in invoices if inv.status == "paid")
    total_pending   = sum(float(inv.amount) for inv in invoices if inv.status == "pending")
    total_overdue   = sum(float(inv.amount) for inv in invoices if inv.status == "pending" and inv.due_date < date.today())
    overdue_count   = sum(1 for inv in invoices if inv.status == "pending" and inv.due_date < date.today())

    # Per-client breakdown
    clients = {}
    for inv in invoices:
        if inv.client_name not in clients:
            clients[inv.client_name] = {"invoiced": 0, "collected": 0, "count": 0}
        clients[inv.client_name]["invoiced"]  += float(inv.amount)
        clients[inv.client_name]["count"]     += 1
        if inv.status == "paid":
            clients[inv.client_name]["collected"] += float(inv.amount)

    # Pick most used currency
    from collections import Counter
    currencies = [inv.currency for inv in invoices]
    currency = Counter(currencies).most_common(1)[0][0] if currencies else "USD"

    return render_template("invoices/report.html",
        invoices=invoices,
        total_invoiced=total_invoiced,
        total_collected=total_collected,
        total_pending=total_pending,
        total_overdue=total_overdue,
        overdue_count=overdue_count,
        clients=clients,
        currency=currency,
        today=date.today(),
    )


@invoices_bp.route("/report/export/csv")
@login_required
def export_csv():
    import csv, io
    from datetime import date

    if not current_user.can_export_csv:
        flash("CSV export is available on the Starter plan and above. Upgrade to access this feature.", "warning")
        return redirect(url_for("invoices.report"))

    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice #", "Client", "Client Email", "Amount", "Currency",
                     "Due Date", "Status", "Days Overdue", "Payment Link", "Created At"])

    for inv in invoices:
        days_overdue = max((date.today() - inv.due_date).days, 0) if inv.status == "pending" and inv.due_date < date.today() else 0
        writer.writerow([
            inv.invoice_number or inv.id[:8].upper(),
            inv.client_name,
            inv.client_email,
            float(inv.amount),
            inv.currency,
            inv.due_date.strftime("%Y-%m-%d"),
            inv.status,
            days_overdue,
            inv.payment_link or "",
            inv.created_at.strftime("%Y-%m-%d"),
        ])

    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=invoices_{date.today()}.csv"}
    )


@invoices_bp.route("/report/export/pdf")
@login_required
def export_pdf():
    from datetime import date
    from flask import make_response

    if not current_user.can_export_pdf:
        flash("PDF reports are available on the Pro plan. Upgrade to access this feature.", "warning")
        return redirect(url_for("invoices.report"))

    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).all()

    total_invoiced  = sum(float(inv.amount) for inv in invoices)
    total_collected = sum(float(inv.amount) for inv in invoices if inv.status == "paid")
    total_pending   = sum(float(inv.amount) for inv in invoices if inv.status == "pending")
    total_overdue   = sum(float(inv.amount) for inv in invoices if inv.status == "pending" and inv.due_date < date.today())

    html = render_template("invoices/report_pdf.html",
        invoices=invoices,
        total_invoiced=total_invoiced,
        total_collected=total_collected,
        total_pending=total_pending,
        total_overdue=total_overdue,
        user=current_user,
        today=date.today(),
    )

    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=invoicebot-report-{date.today()}.pdf"
        return response
    except Exception as e:
        flash(f"PDF generation failed: {str(e)}", "danger")
        return redirect(url_for("invoices.report"))
