import uuid
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


def gen_uuid():
    return str(uuid.uuid4())


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    plan = db.Column(db.String(20), default="free", nullable=False)  # free | starter | pro
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    language = db.Column(db.String(10), default="en", nullable=False)  # en | fr | ar
    company = db.Column(db.String(255), nullable=True)
    default_payment_link = db.Column(db.String(500), nullable=True)

    invoices = db.relationship("Invoice", backref="owner", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def invoice_limit(self):
        from config import Config
        limits = Config.PLAN_LIMITS.get(self.plan, {"invoices": 3})
        return limits["invoices"] if isinstance(limits, dict) else limits

    @property
    def can_export_csv(self):
        from config import Config
        limits = Config.PLAN_LIMITS.get(self.plan, {})
        return limits.get("csv_export", False) if isinstance(limits, dict) else False

    @property
    def can_export_pdf(self):
        from config import Config
        limits = Config.PLAN_LIMITS.get(self.plan, {})
        return limits.get("pdf_report", False) if isinstance(limits, dict) else False

    @property
    def active_invoice_count(self):
        return self.invoices.filter(Invoice.status == "pending").count()

    @property
    def can_add_invoice(self):
        return self.active_invoice_count < self.invoice_limit

    @property
    def is_active(self):
        return not self.is_blocked

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # Client info
    client_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(255), nullable=False)

    # Invoice info
    invoice_number = db.Column(db.String(100), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default="USD")
    due_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    payment_link = db.Column(db.String(500), nullable=True)

    # Sequence config
    tone = db.Column(db.String(20), default="polite")  # polite | professional | firm
    status = db.Column(db.String(20), default="pending")  # pending | paid | cancelled

    # Delays (days after due date to send each stage)
    stage1_delay = db.Column(db.Integer, default=1)   # 1 day overdue
    stage2_delay = db.Column(db.Integer, default=5)   # 5 days overdue
    stage3_delay = db.Column(db.Integer, default=10)  # 10 days overdue

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    marked_paid_at = db.Column(db.DateTime, nullable=True)

    email_schedules = db.relationship("EmailSchedule", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")
    email_logs = db.relationship("EmailLog", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")
    email_drafts = db.relationship("EmailDraft", backref="invoice", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def days_overdue(self):
        from datetime import date
        today = date.today()
        if self.due_date < today and self.status == "pending":
            return (today - self.due_date).days
        return 0

    @property
    def next_scheduled_email(self):
        return (
            self.email_schedules
            .filter(EmailSchedule.sent == False)
            .order_by(EmailSchedule.send_at)
            .first()
        )

    @property
    def sent_emails_count(self):
        return self.email_logs.count()

    def __repr__(self):
        return f"<Invoice {self.invoice_number} for {self.client_name}>"


class EmailSchedule(db.Model):
    __tablename__ = "email_schedules"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)
    stage = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    send_at = db.Column(db.DateTime, nullable=False)
    sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<EmailSchedule invoice={self.invoice_id} stage={self.stage} sent={self.sent}>"


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=False)
    stage = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(500), nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sendgrid_message_id = db.Column(db.String(200), nullable=True)
    error = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<EmailLog invoice={self.invoice_id} stage={self.stage}>"


class EmailDraft(db.Model):
    __tablename__ = "email_drafts"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    invoice_id = db.Column(db.String(36), db.ForeignKey("invoices.id"), nullable=True)
    email_type = db.Column(db.String(50), nullable=True)
    to_address = db.Column(db.String(255), nullable=False)
    from_email = db.Column(db.String(255), nullable=True)
    from_name = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=True)
    html_body = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<EmailDraft to={self.to_address} type={self.email_type}>"
# ← this won't work, we need to edit directly
