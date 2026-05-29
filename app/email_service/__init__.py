import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import resend as resend_client

logger = logging.getLogger(__name__)

TEMPLATES = {
    "polite": {
        1: {
            "subject": "Quick note about invoice #{invoice_number}",
            "body": """Hi {client_name},

Hope you're having a good week.

I wanted to follow up on invoice #{invoice_number} for {amount} {currency} — the due date was {due_date} and I haven't seen the payment come through yet.

Totally understand things get busy. If you've already sent it, just ignore this — and thank you!

If not, you can settle it here:
{payment_section}

Let me know if anything looks off on the invoice or if you have any questions at all.

Thanks,
{sender_name}""",
        },
        2: {
            "subject": "Following up — invoice #{invoice_number} is {days_overdue} days overdue",
            "body": """Hi {client_name},

I'm checking in again on invoice #{invoice_number} for {amount} {currency}, originally due {due_date}.

It's now {days_overdue} days past due and I still haven't received payment. I want to make sure this didn't get lost in the shuffle.

{payment_section}

Could you let me know where things stand? Even a quick reply helps me plan my end.

I appreciate your time,
{sender_name}""",
        },
        3: {
            "subject": "Final follow-up — invoice #{invoice_number}",
            "body": """Hi {client_name},

This is my third and final follow-up on invoice #{invoice_number} for {amount} {currency}, now {days_overdue} days overdue (due date was {due_date}).

I've reached out a couple of times now without a response. I'd genuinely like to resolve this without any further escalation.

{payment_section}

If there's an issue with the work or the amount, please just reply and let me know — I'm happy to talk through it. But if there isn't, I'd appreciate payment or a confirmed payment date by end of week.

Thank you,
{sender_name}""",
        },
    },
    "professional": {
        1: {
            "subject": "Payment reminder — invoice #{invoice_number}",
            "body": """Dear {client_name},

I hope this message finds you well.

This is a courtesy reminder that invoice #{invoice_number} for {amount} {currency} was due on {due_date} and has not yet been received.

Please arrange payment at your earliest convenience using the details below:
{payment_section}

If you have any questions regarding this invoice, please don't hesitate to reply directly to this email.

Best regards,
{sender_name}""",
        },
        2: {
            "subject": "Second notice — invoice #{invoice_number} ({days_overdue} days overdue)",
            "body": """Dear {client_name},

I am writing to follow up on invoice #{invoice_number} for {amount} {currency}, which was due on {due_date} and remains unpaid after {days_overdue} days.

I would appreciate your prompt attention to this matter.

{payment_section}

If you are experiencing any difficulties or have a query about this invoice, please contact me directly and I will do my best to assist.

Regards,
{sender_name}""",
        },
        3: {
            "subject": "Final notice — invoice #{invoice_number} requires immediate attention",
            "body": """Dear {client_name},

I regret that I must send this final notice regarding invoice #{invoice_number} for {amount} {currency}.

This invoice is now {days_overdue} days past its due date of {due_date} and remains unpaid despite previous reminders.

{payment_section}

Please settle this invoice within 5 business days. If I do not receive payment or hear from you by then, I will have no choice but to consider formal recovery options.

I would prefer to resolve this directly and professionally. Please reply if you wish to discuss.

Regards,
{sender_name}""",
        },
    },
    "firm": {
        1: {
            "subject": "Invoice #{invoice_number} — payment overdue",
            "body": """Hi {client_name},

Invoice #{invoice_number} for {amount} {currency} was due on {due_date} and has not been paid.

Please arrange payment immediately:
{payment_section}

{sender_name}""",
        },
        2: {
            "subject": "Invoice #{invoice_number} — {days_overdue} days overdue, response required",
            "body": """Hi {client_name},

Invoice #{invoice_number} for {amount} {currency} is now {days_overdue} days overdue with no payment received.

I require either immediate payment or a written commitment with a specific payment date.

{payment_section}

Please respond to this email today.

{sender_name}""",
        },
        3: {
            "subject": "FINAL NOTICE — invoice #{invoice_number} ({days_overdue} days overdue)",
            "body": """Hi {client_name},

This is my final notice.

Invoice #{invoice_number} for {amount} {currency} is {days_overdue} days past its due date of {due_date}. I have sent multiple reminders without response or payment.

If full payment is not received within 48 hours, I will proceed with formal debt recovery.

{payment_section}

To avoid this, please pay now or contact me immediately to make arrangements.

{sender_name}""",
        },
    },
}



TEMPLATES_FR = {
    "polite": {
        1: {
            "subject": "Rappel amical : Facture #{invoice_number}",
            "body": """Bonjour {client_name},

J'espère que vous allez bien ! Je vous envoie un rappel amical concernant la facture #{invoice_number} d'un montant de {amount} {currency}, dont la date d'échéance était le {due_date}.

Si vous avez déjà effectué le paiement, veuillez ignorer ce message — merci !

Dans le cas contraire, je vous serais reconnaissant(e) de bien vouloir procéder au règlement dès que possible.

{payment_section}

N'hésitez pas à me contacter pour toute question.

Cordialement,
{sender_name}""",
        },
        2: {
            "subject": "Suivi : Facture #{invoice_number} — {days_overdue} jours de retard",
            "body": """Bonjour {client_name},

Je fais suite à la facture #{invoice_number} d'un montant de {amount} {currency}, échue le {due_date}, qui accuse maintenant {days_overdue} jours de retard.

Je voulais m'assurer que ce message n'avait pas été manqué.

{payment_section}

Pourriez-vous me tenir informé(e) de la situation ?

Merci,
{sender_name}""",
        },
        3: {
            "subject": "Dernier rappel : Facture #{invoice_number} — action requise",
            "body": """Bonjour {client_name},

Ceci est mon dernier rappel concernant la facture #{invoice_number} d'un montant de {amount} {currency}, en retard de {days_overdue} jours (date d'échéance initiale : {due_date}).

Je vous serais très reconnaissant(e) d'effectuer le paiement rapidement ou de m'informer de vos intentions.

{payment_section}

Si vous rencontrez un problème, n'hésitez pas à me contacter.

Merci,
{sender_name}""",
        },
    },
    "professional": {
        1: {
            "subject": "Rappel de paiement : Facture #{invoice_number}",
            "body": """Madame, Monsieur {client_name},

Nous vous rappelons que la facture #{invoice_number} d'un montant de {amount} {currency} était due le {due_date}.

Nous vous remercions de bien vouloir procéder au règlement dans les meilleurs délais.

{payment_section}

Pour toute question relative à cette facture, n'hésitez pas à répondre à cet e-mail.

Cordialement,
{sender_name}""",
        },
        2: {
            "subject": "Deuxième avis : Facture #{invoice_number} — {days_overdue} jours de retard",
            "body": """Madame, Monsieur {client_name},

Nous vous contactons au sujet de la facture #{invoice_number} d'un montant de {amount} {currency}, qui reste impayée {days_overdue} jours après son échéance du {due_date}.

Nous vous remercions de bien vouloir régulariser cette situation rapidement.

{payment_section}

Si vous rencontrez des difficultés, veuillez nous contacter directement.

Cordialement,
{sender_name}""",
        },
        3: {
            "subject": "Urgent : Facture #{invoice_number} — paiement immédiat requis",
            "body": """Madame, Monsieur {client_name},

La facture #{invoice_number} d'un montant de {amount} {currency} accuse un retard important ({days_overdue} jours depuis le {due_date}).

Il s'agit de notre dernier avis avant d'envisager des mesures supplémentaires.

{payment_section}

Veuillez nous contacter d'urgence si vous souhaitez discuter de cette situation.

Cordialement,
{sender_name}""",
        },
    },
    "firm": {
        1: {
            "subject": "Facture #{invoice_number} — paiement dû",
            "body": """Bonjour {client_name},

La facture #{invoice_number} d'un montant de {amount} {currency} était due le {due_date} et n'a pas été réglée.

Veuillez effectuer le paiement immédiatement.

{payment_section}

{sender_name}""",
        },
        2: {
            "subject": "EN RETARD : Facture #{invoice_number} — {days_overdue} jours de retard",
            "body": """Bonjour {client_name},

La facture #{invoice_number} d'un montant de {amount} {currency} accuse {days_overdue} jours de retard.

J'attends un paiement immédiat ou un engagement ferme avec une date de règlement.

{payment_section}

Cette situation requiert votre attention immédiate.

{sender_name}""",
        },
        3: {
            "subject": "DERNIER AVIS : Facture #{invoice_number} — {days_overdue} jours de retard",
            "body": """Bonjour {client_name},

Ceci est mon dernier avis concernant la facture #{invoice_number} d'un montant de {amount} {currency}, en retard de {days_overdue} jours.

Si le paiement n'est pas reçu dans les 48 heures, je serai contraint(e) d'envisager un recouvrement formel.

{payment_section}

{sender_name}""",
        },
    },
}

TEMPLATES_AR = {
    "polite": {
        1: {
            "subject": "تذكير ودي: الفاتورة #{invoice_number}",
            "body": """مرحباً {client_name}،

أتمنى أن تكون بخير! أرسل إليك هذا التذكير الودي بشأن الفاتورة #{invoice_number} بمبلغ {amount} {currency}، والتي كان موعد استحقاقها {due_date}.

إذا كنت قد أرسلت الدفعة بالفعل، يُرجى تجاهل هذه الرسالة — وشكراً!

وإن لم يكن كذلك، أتطلع إلى تسوية المبلغ في أقرب وقت ممكن.

{payment_section}

لا تتردد في التواصل معي إن كان لديك أي استفسار.

مع أطيب التحيات،
{sender_name}""",
        },
        2: {
            "subject": "متابعة: الفاتورة #{invoice_number} — {days_overdue} يوم تأخير",
            "body": """مرحباً {client_name}،

أتابع معك بشأن الفاتورة #{invoice_number} بمبلغ {amount} {currency}، المستحقة منذ {due_date}، والتي تأخرت الآن {days_overdue} يوماً.

أردت فقط التأكد من أن هذه الرسالة لم تفتك.

{payment_section}

هل يمكنك إعلامي بالوضع عندما تتاح لك الفرصة؟

شكراً جزيلاً،
{sender_name}""",
        },
        3: {
            "subject": "آخر تذكير: الفاتورة #{invoice_number} — إجراء مطلوب",
            "body": """مرحباً {client_name}،

هذا هو آخر تذكير بشأن الفاتورة #{invoice_number} بمبلغ {amount} {currency}، المتأخرة {days_overdue} يوماً (تاريخ الاستحقاق الأصلي: {due_date}).

أرجو منك سرعة الدفع أو إخباري بموعد متوقع للتسوية.

{payment_section}

إذا كانت هناك مشكلة لا أعلمها، فلا تتردد في التواصل معي.

شكراً،
{sender_name}""",
        },
    },
    "professional": {
        1: {
            "subject": "تذكير بالدفع: الفاتورة #{invoice_number}",
            "body": """عزيزي/عزيزتي {client_name}،

نود تذكيركم بأن الفاتورة #{invoice_number} بمبلغ {amount} {currency} كانت مستحقة في {due_date}.

نرجو منكم إتمام الدفع في أقرب وقت ممكن.

{payment_section}

لأي استفسار يتعلق بهذه الفاتورة، لا تترددوا في الرد على هذا البريد الإلكتروني.

مع التقدير،
{sender_name}""",
        },
        2: {
            "subject": "إشعار ثانٍ: الفاتورة #{invoice_number} — {days_overdue} يوم تأخير",
            "body": """عزيزي/عزيزتي {client_name}،

نتواصل معكم بشأن الفاتورة #{invoice_number} بمبلغ {amount} {currency}، والتي لا تزال غير مسددة بعد {days_overdue} يوماً من تاريخ استحقاقها {due_date}.

نقدر تعاونكم السريع في تسوية هذا المبلغ.

{payment_section}

إذا كنتم تواجهون أي صعوبات، يُرجى التواصل معنا مباشرة.

مع التقدير،
{sender_name}""",
        },
        3: {
            "subject": "عاجل: الفاتورة #{invoice_number} — يُرجى الدفع الفوري",
            "body": """عزيزي/عزيزتي {client_name}،

الفاتورة #{invoice_number} بمبلغ {amount} {currency} متأخرة بشكل كبير ({days_overdue} يوماً منذ {due_date}).

هذا هو إشعارنا الأخير قبل اتخاذ إجراءات إضافية.

{payment_section}

يُرجى التواصل معنا بشكل عاجل إذا كنتم ترغبون في مناقشة الأمر.

مع التقدير،
{sender_name}""",
        },
    },
    "firm": {
        1: {
            "subject": "الفاتورة #{invoice_number} — مبلغ مستحق",
            "body": """مرحباً {client_name}،

الفاتورة #{invoice_number} بمبلغ {amount} {currency} كانت مستحقة في {due_date} ولم يتم سدادها.

يُرجى الدفع فوراً.

{payment_section}

{sender_name}""",
        },
        2: {
            "subject": "متأخر: الفاتورة #{invoice_number} — {days_overdue} يوم تأخير",
            "body": """مرحباً {client_name}،

الفاتورة #{invoice_number} بمبلغ {amount} {currency} متأخرة {days_overdue} يوماً.

أنتظر الدفع الفوري أو التزاماً واضحاً بموعد السداد.

{payment_section}

هذا الأمر يستدعي اهتمامك الفوري.

{sender_name}""",
        },
        3: {
            "subject": "إشعار نهائي: الفاتورة #{invoice_number} — {days_overdue} يوم تأخير",
            "body": """مرحباً {client_name}،

هذا هو إشعاري النهائي بشأن الفاتورة #{invoice_number} بمبلغ {amount} {currency}، المتأخرة {days_overdue} يوماً.

إذا لم يتم استلام الدفع خلال 48 ساعة، سأضطر إلى النظر في خيارات التحصيل الرسمية.

{payment_section}

{sender_name}""",
        },
    },
}

def _build_payment_section(payment_link):
    if payment_link:
        return f"Pay now: {payment_link}"
    return ""


def _render_template(tone, stage, context, language="en"):
    lang_map = {"fr": TEMPLATES_FR, "ar": TEMPLATES_AR}
    template_set = lang_map.get(language, TEMPLATES)
    template = template_set.get(tone, template_set["polite"]).get(stage, template_set["polite"][1])
    subject = template["subject"].format(**context)
    body = template["body"].format(**context)
    return subject, body


def send_invoice_reminder(invoice, stage):
    from datetime import date

    mail_from = current_app.config.get("MAIL_FROM", "")
    mail_name = current_app.config.get("MAIL_FROM_NAME", "InvoiceBot")

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
        "sender_name": f"{invoice.owner.name or invoice.owner.email} — {invoice.owner.company}" if invoice.owner.company else (invoice.owner.name or invoice.owner.email),
        "payment_section": _build_payment_section(invoice.payment_link),
    }

    language = getattr(invoice.owner, "language", "en") or "en"
    subject, body = _render_template(invoice.tone, stage, context, language=language)

    ok, provider_tag, err = send_mail(
        to_address=invoice.client_email,
        subject=subject,
        body=body,
        from_name=mail_name,
        from_email=mail_from,
        invoice_id=invoice.id,
        email_type="invoice_reminder",
    )

    if ok:
        logger.info(f"Email sent: invoice={invoice.id} stage={stage} provider={provider_tag}")
        return True, provider_tag, None
    else:
        logger.error(f"Email failed: invoice={invoice.id} stage={stage} error={err}")
        return False, None, err


def send_mail(
    to_address,
    subject,
    body,
    html_body=None,
    from_name=None,
    from_email=None,
    invoice_id=None,
    email_type=None,
):
    """Send an email using configured provider (resend, smtp, db, or test).

    Returns (ok: bool, provider_tag: str_or_none, error: str_or_none).
    """
    email_mode = current_app.config.get("EMAIL_MODE", "smtp")
    mail_username = current_app.config.get("MAIL_USERNAME", "")
    mail_password = current_app.config.get("MAIL_PASSWORD", "").replace(" ", "")
    mail_server   = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    mail_port     = current_app.config.get("MAIL_PORT", 587)
    mail_use_tls  = current_app.config.get("MAIL_USE_TLS", True)
    mail_use_ssl  = current_app.config.get("MAIL_USE_SSL", False)
    default_from  = current_app.config.get("MAIL_FROM", mail_username)
    default_name  = current_app.config.get("MAIL_FROM_NAME", "InvoiceBot")

    mail_from = from_email or default_from
    mail_name = from_name or default_name

    logger.info(
        "send_mail called: mode=%s from=%s to=%s",
        email_mode, mail_from, to_address,
    )

    # ── Test mode ──────────────────────────────────────────────────────────
    if email_mode == "test":
        logger.info(
            f"\n{'='*60}\nTEST EMAIL MODE\nTo: {to_address}\n"
            f"Subject: {subject}\n{body}\n{'='*60}\n"
        )
        return True, "test-logged", None

    # ── DB draft mode ──────────────────────────────────────────────────────
    if email_mode == "db":
        try:
            from app import db
            from app.models import EmailDraft

            draft = EmailDraft(
                invoice_id=invoice_id,
                email_type=email_type,
                to_address=to_address,
                from_email=mail_from,
                from_name=mail_name,
                subject=subject,
                body=body,
                html_body=html_body,
            )
            db.session.add(draft)
            db.session.commit()
            logger.info("Email draft saved: %s", draft.id)
            return True, "db-saved", None
        except Exception as e:
            logger.exception("Error saving email draft")
            return False, None, str(e)

    # ── Resend mode ────────────────────────────────────────────────────────
    if email_mode == "resend":
        api_key = current_app.config.get("RESEND_API_KEY", "")
        if not api_key:
            return False, None, "RESEND_API_KEY not configured"
        try:
            resend_client.api_key = api_key
            params = {
                "from": f"{mail_name} <{mail_from}>",
                "to": [to_address],
                "subject": subject,
                "text": body,
            }
            if html_body:
                params["html"] = html_body
            resend_client.Emails.send(params)
            return True, "resend-sent", None
        except Exception as e:
            logger.exception("Resend error sending email")
            return False, None, str(e)

    # ── SMTP mode ──────────────────────────────────────────────────────────
    if email_mode in ("smtp", ""):
        if not mail_username or not mail_password:
            msg = "SMTP credentials not configured"
            logger.warning(msg)
            return False, None, msg

        msg = MIMEMultipart()
        msg["From"]    = f"{mail_name} <{mail_from}>"
        msg["To"]      = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            if mail_use_ssl or int(mail_port) == 465:
                server = smtplib.SMTP_SSL(mail_server, int(mail_port), timeout=10)
            else:
                server = smtplib.SMTP(mail_server, int(mail_port), timeout=10)
                server.ehlo()
                if mail_use_tls:
                    server.starttls()
                    server.ehlo()
            server.login(mail_username, mail_password)
            server.sendmail(mail_from, to_address, msg.as_string())
            server.quit()
            return True, "smtp-sent", None
        except Exception as e:
            logger.exception("SMTP error sending email")
            return False, None, str(e)

    msg = f"Unsupported EMAIL_MODE: {email_mode}"
    logger.error(msg)
    return False, None, msg

def send_welcome_email(user):
    """Send welcome email to newly registered user."""
    mail_from = current_app.config.get("MAIL_FROM", "")
    mail_name = current_app.config.get("MAIL_FROM_NAME", "InvoiceBot")

    subject = "You're in — here's how InvoiceBot works"
    app_url = current_app.config.get("APP_URL", "http://localhost:5000")
    body = f"""Hi {user.name or "there"},

Welcome to InvoiceBot. You just made a smart decision.

Here is exactly what happens next:

STEP 1 — Set up your profile (2 minutes)
Go to Settings and add your company name and payment link.
Every invoice you create will auto-fill your payment link.
→ {app_url}/auth/settings

STEP 2 — Add your first overdue invoice
Enter the client name, email, amount, and due date.
Choose your tone: Polite, Professional, or Firm.
Pick the language your client reads: Arabic, French, or English.
→ {app_url}/invoices/new

STEP 3 — Let us handle the awkward part
InvoiceBot sends 3 professionally written reminders on your schedule.
Stage 1: gentle nudge after due date
Stage 2: follow-up a few days later
Stage 3: firm final notice
You do nothing. We do the chasing.

——

A few things worth knowing:

— You are on the {user.plan.title()} plan ({user.invoice_limit} active invoices)
— Emails go out from our servers, not yours — your clients won't know it's automated
— You can preview every email before it sends
— Mark an invoice as paid and all reminders stop instantly

If you have a question at any point, reply to this email.
I read every message personally.

— Mohammed
Founder, InvoiceBot · AINTORA SYSTEMS
{app_url}
"""

    ok, provider, err = send_mail(
        to_address=user.email,
        subject=subject,
        body=body,
        from_name=mail_name,
        from_email=mail_from,
        email_type="welcome",
    )
    if not ok:
        logger.error(f"Welcome email failed for {user.email}: {err}")
    return ok
