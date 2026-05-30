# path: config.py
import os
from dotenv import load_dotenv

load_dotenv()


def env(name, default=""):
    return os.environ.get(name, default).strip()


def normalize_url(url, default="http://localhost:5000"):
    url = (url or "").strip()
    if not url:
        url = default
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


class Config:
    SECRET_KEY = env("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = env("DATABASE_URL", "postgresql://localhost/invoicenudge")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER    = env("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT      = int(env("MAIL_PORT", "587"))
    MAIL_USERNAME  = env("MAIL_USERNAME", "")
    MAIL_PASSWORD  = env("MAIL_PASSWORD", "")
    MAIL_FROM      = env("MAIL_FROM", "")
    MAIL_FROM_NAME = env("MAIL_FROM_NAME", "InvoiceBot")
    MAIL_USE_TLS   = env("MAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
    MAIL_USE_SSL   = env("MAIL_USE_SSL", "False").lower() in ("1", "true", "yes")

    # Resend
    RESEND_API_KEY = env("RESEND_API_KEY", "")

    # Email mode: 'resend', 'smtp', 'db', or 'test'
    EMAIL_MODE = env("EMAIL_MODE", "smtp")

    # Lemon Squeezy
    LS_API_KEY         = env("LS_API_KEY", "")
    LS_WEBHOOK_SECRET = env("LS_WEBHOOK_SECRET", "")
    LS_STARTER_URL    = env("LS_STARTER_URL", "")
    LS_PRO_URL        = env("LS_PRO_URL", "")

    # App
    APP_URL = normalize_url(env("APP_URL", "http://localhost:5000"))
    CRON_SECRET = env("CRON_SECRET", "")


    # Security
    SESSION_COOKIE_SECURE      = False  # set True in prod only
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400
    WTF_CSRF_TIME_LIMIT        = 3600

    # Plan limits
    PLAN_LIMITS = {
        "free":    {"invoices": 3,       "csv_export": False, "pdf_report": False},
        "starter": {"invoices": 20,      "csv_export": True,  "pdf_report": False},
        "pro":     {"invoices": 999999,  "csv_export": True,  "pdf_report": True},
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://localhost/invoicenudge_dev"
    )


class ProductionConfig(Config):
    DEBUG = False
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {"connect_timeout": 10},
}

class SecurityConfig:
    # Session security
    SESSION_COOKIE_SECURE     = False  # set True in prod only
    SESSION_COOKIE_HTTPONLY   = True   # No JS access
    SESSION_COOKIE_SAMESITE   = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day

    # CSRF already handled by Flask-WTF
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Prevent clickjacking
    X_FRAME_OPTIONS = "DENY"
