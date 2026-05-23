import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

TEMPLATES = {
    "polite": {
        1: {
            "subject": "Friendly reminder: Invoice #{invoice_number} is due",
            "body": """Hi {client_name},

I hope you're doing well! I wanted to send a quick friendly reminder that invoice #{invoice_number} for {amount} {currency} was due on {due_date}.

If you've already sent the payment, please ignore this — and thank you!

If not, I'd appreciate it if you could process it at your earliest convenience.

{payment_section}

Please let me know if you have any questions.

Warm regards,
{sender_name}""",
        },
        2: {
            "subject": "Following up: Invoice #{invoice_number} — {days_overdue} days overdue",
            "body": """Hi {client_name},

I'm following up on invoice #{invoice_number} for {amount} {currency}, which was due on {due_date} and is now {days_overdue} days past due.

I just want to make sure this hasn't slipped through the cracks.

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

If there's an issue I'm not aware of, please reach out.

Thank you,
{sender_name}""",
        },
    },
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

If you are experiencing difficulties, please contact me directly.

Regards,
{sender_name}""",
        },
        3: {
            "subject": "Urgent: Invoice #{invoice_number} — immediate payment required",
            "body": """Dear {client_name},

Invoice #{invoice_number} for {amount} {currency} is now seriously overdue ({days_overdue} days past {due_date}).

This is my final notice before I consider further action.

{payment_section}

Please contact me urgently if you need to discuss this.

Regards,
{sender_name}""",
        },
    },
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

If payment is not received within 48 hours, I will be forced to consider formal debt recovery options.

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
    from datetime import date

    email_mode = current_app.config.get("EMAIL_MODE", "smtp")
    mail_username = current_app.config.get("MAIL_USERNAME", "")
    mail_password = current_app.config.get("MAIL_PASSWORD", "")
    mail_server   = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    mail_port     = current_app.config.get("MAIL_PORT", 587)
    mail_use_tls  = current_app.config.get("MAIL_USE_TLS", True)
    mail_use_ssl  = current_app.config.get("MAIL_USE_SSL", False)
    mail_from     = current_app.config.get("MAIL_FROM", mail_username)
    mail_name     = current_app.config.get("MAIL_FROM_NAME", "InvoiceBot")

    due_date_str = invoice.due_date.strftime("%B %d, %Y")
    amount_str   = f"{float(invoice.amount):,.2f}"
    days_overdue = (date.today() - invoice.due_date).days if date.today() > invoice.due_date else 0

    context = {
        "client_name":     invoice.client_name,
        "invoice_number":  invoice.invoice_number or invoice.id[:8].upper(),
        "amount":          amount_str,
        "currency":        invoice.currency,
        "due_date":        due_date_str,
        "days_overdue":    days_overdue,
        "sender_name":     invoice.owner.name or invoice.owner.email,
        "payment_section": _build_payment_section(invoice.payment_link),
    }

    subject, body = _render_template(invoice.tone, stage, context)

    # Test/Log mode: just log to console instead of sending
    if email_mode == "test":
        logger.info(f"\n{'='*60}\nTEST EMAIL MODE - Invoice Reminder\nTo: {invoice.client_email}\nSubject: {subject}\n{body}\n{'='*60}\n")
        return True, "test-logged", None

    if not mail_username or not mail_password:
        logger.warning("SMTP credentials not configured — skipping email send")
        return False, None, "SMTP credentials not configured"

    msg = MIMEMultipart()
    msg["From"]    = f"{mail_name} <{mail_from}>"
    msg["To"]      = invoice.client_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if mail_use_ssl or mail_port == 465:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=10)
            server.ehlo()
            if mail_use_tls:
                server.starttls()
                server.ehlo()
        server.login(mail_username, mail_password)
        server.sendmail(mail_from, invoice.client_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent: invoice={invoice.id} stage={stage}")
        return True, "smtp-sent", None
    except Exception as e:
        logger.error(f"SMTP error: invoice={invoice.id} stage={stage} error={str(e)}")
        return False, None, str(e)