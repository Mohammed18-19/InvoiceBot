# InvoiceBot

Automated invoice follow-up for freelancers and small businesses. Add invoices, schedule multi-stage reminder emails, manage clients, and keep overdue payments moving with graceful reminder sequences.

## What this project does

- User registration, login, and password reset
- Create invoices with client email, amount, due date, tone, and payment link
- Automatically schedule 3 reminder emails per invoice
- Send reminder emails on a schedule using SMTP with TLS/SSL support
- Track email logs and delivery success/failure
- Support pricing plans via Lemon Squeezy webhook billing
- Show graceful custom error pages for `403`, `404`, and `500`

## Features

- Authenticated user dashboard with invoice status and payment tracking
- Invoice creation and detail view
- Configurable follow-up tone: `polite`, `professional`, `firm`
- Automatic overdue email scheduling and sending
- Password reset email flow
- Admin panel for managing blocked users and monitoring email logs
- Lemon Squeezy upgrade flow for paid plans
- Production-ready Flask setup with Talisman security hardening

## Tech stack

- Python 3.12
- Flask 3
- PostgreSQL
- SQLAlchemy + Flask-Migrate
- Flask-Login
- Flask-WTF + WTForms
- APScheduler for background email processing
- SMTP email delivery via Python `smtplib`
- Lemon Squeezy webhook billing
- Bootstrap 5 for UI styling

## Repository structure

```
invoicebot/
├── app/
│   ├── __init__.py          # App factory, extensions, error handlers, scheduler bootstrap
│   ├── models.py            # User, Invoice, EmailSchedule, EmailLog models
│   ├── auth/                # Authentication: register, login, forgot/reset password
│   ├── billing/             # Lemon Squeezy upgrade and webhook handling
│   ├── dashboard/           # Main authenticated dashboard
│   ├── invoices/            # Invoice CRUD and validation
│   ├── email_service/       # Email content and SMTP send logic
│   ├── scheduler/           # APScheduler job for sending due emails
│   ├── templates/           # Jinja views and error pages
│   └── static/              # CSS/JS assets
├── config.py                # App configuration and environment settings
├── init_db.py               # Database initialization script
├── run.py                   # Local run entry point
├── seed.py                  # Seed development data
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway/Heroku process file
├── railway.toml             # Railway deployment config
├── .env.example             # Example environment variables
└── README.md                # Project documentation
```

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/Mohammed18-19/invoicebot.git
cd invoicebot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example env file and update the values:

```bash
cp .env.example .env
```

Then edit `.env` with your own settings.

#### Required variables

- `FLASK_ENV=development`
- `SECRET_KEY` (strong random secret)
- `DATABASE_URL=postgresql://localhost/invoicebot_dev`
- `MAIL_SERVER` (e.g. `smtp.gmail.com`)
- `MAIL_PORT` (e.g. `587`)
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_FROM_NAME`
- `LS_WEBHOOK_SECRET`
- `LS_STARTER_URL`
- `LS_PRO_URL`
- `APP_URL=http://localhost:5000`

### 4. Initialize the database

```bash
python init_db.py
```

If you prefer manual migrations:

```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

### 5. Seed optional demo data

```bash
python seed.py
```

### 6. Run the app

```bash
python run.py
```

Open `http://localhost:5000` in your browser.

## SMTP email configuration

This project sends emails using SMTP directly through `smtplib`.

For Gmail SMTP, use the following settings:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your@gmail.com
MAIL_FROM_NAME=Your Name
```

If your provider requires SSL on port `465`, set:

```env
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USE_TLS=False
```

### Gmail notes

- Use an App Password if you have 2FA enabled
- Do not use your regular Gmail login password

## Lemon Squeezy billing setup

Billing is handled through Lemon Squeezy webhooks and plan URLs.

- `LS_WEBHOOK_SECRET` is used to verify incoming webhook signatures
- `LS_STARTER_URL` and `LS_PRO_URL` are the product checkout URLs

When a subscription event occurs, the webhook updates the user's plan to `starter`, `pro`, or `free`.

## Testing error pages

With the app running locally, test the custom error pages by visiting:

- `http://localhost:5000/this-page-does-not-exist` → `404`
- Add a temporary route that raises an exception to test `500`
- Add a temporary route that calls `abort(403)` to test `403`

## Testing password reset

1. Go to `/auth/forgot-password`
2. Enter a registered email
3. Confirm the reset email is sent via SMTP

If nothing is delivered, check logs and SMTP credentials.

## Deployment notes

This project includes a `Procfile` for deployment on Railway, Heroku, or any Gunicorn-compatible host.

### Recommended deployment workflow

1. Push code to GitHub
2. Connect the repo to Railway
3. Add environment variables in Railway settings
4. Deploy and run database migrations

## Useful commands

```bash
source venv/bin/activate
python run.py
python init_db.py
python seed.py
```

## Project improvements already included

- Error handlers for `403`, `404`, and `500`
- Password reset email sending with robust TLS/SSL support
- Background scheduler using APScheduler for due email processing
- Config-driven Lemon Squeezy billing integration

## Contributing

If you want to extend the app, consider:

- Adding more email templates or custom reminder copy
- Supporting file uploads or invoice PDF generation
- Adding analytics for email opens and clicks
- Adding a user-facing settings page for reminder intervals

## License

This project is released under a proprietary license. All rights are reserved by Mohammed.
Unauthorized copying, distribution, or derivative use is prohibited without express written permission.

---

Built with Flask and PostgreSQL for fast, secure invoice follow-up automation.
