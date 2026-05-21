import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://localhost/invoicenudge")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail (Gmail SMTP / Brevo)
    MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_FROM     = os.environ.get("MAIL_FROM", "")
    MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "InvoiceBot")

    # Lemon Squeezy
    LS_WEBHOOK_SECRET = os.environ.get("LS_WEBHOOK_SECRET", "")
    LS_STARTER_URL    = os.environ.get("LS_STARTER_URL", "")
    LS_PRO_URL        = os.environ.get("LS_PRO_URL", "")

    # App
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")

    # Plan limits
    PLAN_LIMITS = {
        "free":    3,
        "starter": 20,
        "pro":     999999,
    }


class DevelopmentConfig(Config):
    DEBUG = True
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