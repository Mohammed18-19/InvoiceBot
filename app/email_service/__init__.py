import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To
from flask import current_app

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Email templates: 3 tones × 3 stages = 9 emails
# ──────────────────────────────────────────────

TEMPLATES = {
    # ── POLITE ──────────────────────────────────
    "polite": {
        1: {
            "subject": "Friendly reminder: Invoice #{invoice_number} is due",
            "body": """Hi {client_name},

I hope you're doing well! I wanted to send a quick, friendly reminder that invoice #{invoice_number} for {amount} {currency} was due on {due_date}.

If you've already sent the payment, please ignore this message — and thank you!

If not, I'd really appreciate it if you could process it at your earliest convenience.

{payment_section}

Please let me know if you have any questions about the invoice.

Warm regards,
{sender_name}""",
        },
        2: {
            "subject": "Following up: Invoice #{invoice_number} — {days_overdue} days overdue",
            "body": """Hi {client_name},

I'm following up on invoice #{invoice_number} for {amount} {currency}, which was due on {due_date} and is now {days_overdue} days past due.

I understand things get busy — I just want to make sure this hasn't slipped through the cracks.

{payment_section}

Could you let me know the status when you get a chance?

Thanks so much,
{sender_name}""",
        },
        3: {
            "subject": "Final reminder: Invoice #{invoice_number} — action required",
            "body": """Hi {client_name},

This is my final reminder regarding invoice #{invoice_number} for {amount} {currency}, now {days_overdue} days overdue (original due date: {due_date}).

I'd really appreciate prompt payment or a brief message about when I can expect it.

{payment_section}

If there's an issue I'm not aware of, please reach out and we can discuss.

Thank you for your attention to this,
{sender_name}""",
        },
    },

    # ── PROFESSIONAL ────────────────────────────
    "professional": {
        1: {
            "subject": "Payment reminder: Invoice #{invoice_number}",
            "body": """Dear {client_name},

This is a reminder that invoice #{invoice_number} for {amount} {currency} was due on {due_date}.

Please process your payment at your earliest convenience.

{payment_section}

If you have questions about the invoice, feel free to reply to this email.

Best regards,
{sender_name}""",
        },
        2: {
            "subject": "Second notice: Invoice #{invoice_number} — {days_overdue} days past due",
            "body": """Dear {client_name},

I am following up on invoice #{invoice_number} for {amount} {currency}, which remains unpaid {days_overdue} days past its due date of {due_date}.

Prompt payment would be greatly appreciated.

{payment_section}

If you are experiencing difficulties, please contact me directly so we can discuss payment arrangements.

Regards,
{sender_name}""",
        },
        3: {
            "subject": "Urgent: Invoice #{invoice_number} — immediate payment required",
            "body": """Dear {client_name},

Invoice #{invoice_number} for {amount} {currency} is now seriously overdue ({days_overdue} days past {due_date}).

This is my final notice before I consider further action. I strongly encourage you to resolve this matter immediately.

{payment_section}

Please contact me urgently if you need to discuss this.

Regards,
{sender_name}""",
        },
    },

    # ── FIRM ─────────────────────────────────────
    "firm": {
        1: {
            "subject": "Invoice #{invoice_number} — payment due",
            "body": """Hi {client_name},

Invoice #{invoice_number} for {amount} {currency} was due on {due_date} and has not been paid.

Please arrange payment immediately.

{payment_section}

{sender_name}""",
        },
        2: {
            "subject": "OVERDUE: Invoice #{invoice_number} — {days_overdue} days past due",
            "body": """Hi {client_name},

Invoice #{invoice_number} for {amount} {currency} is {days_overdue} days overdue.

I expect immediate payment or a clear commitment with a payment date.

{payment_section}

This matter requires your immediate attention.

{sender_name}""",
        },
        3: {
            "subject": "FINAL NOTICE: Invoice #{invoice_number} — {days_overdue} days past due",
            "body": """Hi {client_name},

This is my final notice for invoice #{invoice_number} for {amount} {currency}, now {days_overdue} days past due.

If payment or a satisfactory response is not received within 48 hours, I will be forced to consider formal debt recovery options.

{payment_section}

{sender_name}""",
        },
    },
}


def _build_payment_section(payment_link):
    if payment_link:
        return f"Pay now: {payment_link}"
    return ""


def _render_template(tone, stage, context):
    template = TEMPLATES.get(tone, TEMPLATES["polite"]).get(stage, TEMPLATES["polite"][1])
    subject = template["subject"].format(**context)
    body = template["body"].format(**context)
    return subject, body


def send_invoice_reminder(invoice, stage):
    """
    Send a reminder email for the given invoice and stage.
    Returns (success: bool, message_id: str | None, error: str | None)
    """
    from datetime import date

    api_key = current_app.config.get("SENDGRID_API_KEY", "")
    if not api_key:
        logger.warning("SendGrid API key not configured — skipping email send")
        return False, None, "SendGrid API key not configured"

    due_date_str = invoice.due_date.strftime("%B %d, %Y")
    amount_str = f"{float(invoice.amount):,.2f}"
    days_overdue = (date.today() - invoice.due_date).days if date.today() > invoice.due_date else 0

    context = {
        "client_name": invoice.client_name,
        "invoice_number": invoice.invoice_number or invoice.id[:8].upper(),
        "amount": amount_str,
        "currency": invoice.currency,
        "due_date": due_date_str,
        "days_overdue": days_overdue,
        "sender_name": invoice.owner.name or invoice.owner.email,
        "payment_section": _build_payment_section(invoice.payment_link),
    }

    subject, body = _render_template(invoice.tone, stage, context)

    message = Mail(
        from_email=From(
            current_app.config["MAIL_FROM"],
            current_app.config.get("MAIL_FROM_NAME", "InvoiceNudge"),
        ),
        to_emails=To(invoice.client_email),
        subject=subject,
        plain_text_content=body,
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        message_id = response.headers.get("X-Message-Id", "")
        logger.info(f"Email sent: invoice={invoice.id} stage={stage} status={response.status_code}")
        return True, message_id, None
    except Exception as e:
        logger.error(f"SendGrid error: invoice={invoice.id} stage={stage} error={str(e)}")
        return False, None, str(e)
