# InvoiceBot

Automated invoice follow-up for freelancers and small businesses. Add invoices, schedule multi-stage reminder emails, manage clients, and keep overdue payments moving with graceful reminder sequences.

## What this project does

- User registration, login, and password reset
- Create invoices with client email, amount, due date, tone, and payment link
- Automatically schedule 3 reminder emails per invoice
- Send reminder emails on a schedule using SMTP or Brevo
- Track email logs and delivery success/failure
- Support pricing plans via Lemon Squeezy webhook billing
- Show graceful custom error pages for `403`, `404`, and `500`
- Multi-language email reminders (English, French, Arabic)
- Welcome email on new user registration
- Email preview per reminder stage before sending
- Invoice report with per-client breakdown and CSV export
- User settings: company name, default payment link, email language

## Features

- Authenticated user dashboard with invoice status and payment tracking
- Onboarding checklist on dashboard for new users (company, payment link, first invoice)
- Invoice creation and detail view with email preview per stage
- Configurable follow-up tone: `polite`, `professional`, `firm`
- Multi-language reminder emails: English, French, Arabic (set per user in Settings)
- Automatic overdue email scheduling and sending
- Welcome email sent on registration
- Password reset email flow
- Admin panel for managing blocked users and monitoring email logs
- Invoice report page: total invoiced, collected, pending, overdue, per-client breakdown
- CSV export of all invoices (Starter plan and above)
- PDF report export (Pro plan)
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
- SMTP email delivery via Brevo (recommended) or any SMTP provider
- Lemon Squeezy webhook billing
- Bootstrap 5 for UI styling

## Repository structure

```
invoicebot/
├── app/
│   ├── __init__.py          # App factory, extensions, error handlers, scheduler bootstrap
│   ├── models.py            # User, Invoice, EmailSchedule, EmailLog models
│   ├── auth/                # Authentication: register, login, forgot/reset password, settings
│   ├── billing/             # Lemon Squeezy upgrade and webhook handling
│   ├── dashboard/           # Main authenticated dashboard with onboarding checklist
│   ├── invoices/            # Invoice CRUD, email preview, report, CSV export
│   ├── email_service/       # Email content (EN/FR/AR), SMTP send logic, welcome email
│   ├── scheduler/           # APScheduler job for sending due emails
│   ├── templates/           # Jinja views and error pages
│   └── static/              # CSS/JS assets
├── config.py                # App configuration, environment settings, plan limits
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
- `MAIL_SERVER` (e.g. `smtp-relay.brevo.com`)
- `MAIL_PORT` (e.g. `587`)
- `MAIL_USE_TLS=True`
- `MAIL_USE_SSL=False`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `MAIL_FROM_NAME`
- `EMAIL_MODE=smtp`
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

## Email configuration

### Brevo (recommended — free, inbox delivery)

Brevo provides 300 free emails/day with proper SPF/DKIM authentication, meaning reminders land in inbox rather than spam. Sign up at [brevo.com](https://brevo.com) and use the SMTP credentials from your dashboard:

```env
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_brevo_login@smtp-brevo.com
MAIL_PASSWORD=your_brevo_smtp_key
MAIL_FROM=yourapp@gmail.com
MAIL_FROM_NAME=InvoiceBot by YourCompany
EMAIL_MODE=smtp
```

### Gmail SMTP (development only)

For Gmail SMTP, use an App Password (requires 2FA enabled on the account):

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USE_TLS=False
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_FROM=your@gmail.com
MAIL_FROM_NAME=Your Name
EMAIL_MODE=smtp
```

> Note: Gmail SMTP is not recommended for production as reminder emails may land in spam for recipients. Use Brevo for production.

### Resend (alternative)

Resend provides 3,000 free emails/month. The SDK is already installed:

```env
EMAIL_MODE=resend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
```

### DB draft-only mode

To store emails as database drafts without sending (useful for debugging):

```env
EMAIL_MODE=db
```

Drafts are viewable from the admin panel.

### Test mode

To log emails to the terminal without sending:

```env
EMAIL_MODE=test
```

## Multi-language email reminders

Users can set their preferred reminder language in **Settings → Language**. Supported languages:

- English (`en`) — default
- French (`fr`) — Français
- Arabic (`ar`) — العربية

The language applies to all 3 reminder stages across all tones (polite, professional, firm). Clients receive reminders in the language the user has selected.

## User settings

Each user can configure the following from `/auth/settings`:

- **Full name** — shown in email signatures
- **Company name** — appended to sender name in reminders (e.g. "Issam — AINTORA Systems")
- **Default payment link** — auto-filled on every new invoice (can be overridden per invoice)
- **Email language** — language for all client-facing reminder emails

## Plan limits

| Feature | Free | Starter | Pro |
|---|---|---|---|
| Active invoices | 3 | 20 | Unlimited |
| Email reminders | ✓ | ✓ | ✓ |
| CSV export | ✗ | ✓ | ✓ |
| PDF report | ✗ | ✗ | ✓ |

Plans are managed via Lemon Squeezy webhooks. When a subscription event is received, the user's plan updates automatically.

## Invoice report

The report page (`/invoices/report`) shows:

- Total invoiced, collected, pending, and overdue amounts
- Per-client breakdown with invoice count and revenue
- Full invoice list with status and due dates
- CSV export button (Starter+) and PDF export button (Pro)

Currency shown is automatically detected from the user's most-used invoice currency.

## Onboarding checklist

New users see a checklist on the dashboard until they complete the three setup steps:

1. Add company name in Settings
2. Set a default payment link in Settings
3. Create their first invoice

Each item shows a green checkmark once completed and the checklist disappears when all three are done.

## Email preview

From any invoice detail page, users can preview exactly what each reminder stage will look like before it sends — including subject line, body, sender, and recipient — across all 3 stages. The preview reflects the user's current language and tone settings.

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

## Testing email

Hit the debug route while logged in to verify email delivery:

```
http://localhost:5000/debug/test-email
```

Returns a JSON response with `success`, `provider`, `error`, and config details.

## Testing password reset

1. Go to `/auth/forgot-password`
2. Enter a registered email
3. Confirm the reset email arrives via your configured provider

## Deployment notes

This project includes a `Procfile` for deployment on Railway, Render, Heroku, or any Gunicorn-compatible host.

### Recommended deployment workflow

1. Push code to GitHub
2. Connect the repo to your hosting provider
3. Add all environment variables from `.env.example` in the dashboard
4. Run database migrations via the provider's shell or a release command:
   ```bash
   flask db upgrade
   ```
5. Deploy

### Environment variables for production

All variables from the local `.env` file must be added to your hosting provider's environment settings. The most critical ones for production:

- `FLASK_ENV=production`
- `SECRET_KEY` (strong, random, never reuse the dev key)
- `DATABASE_URL` (provided by your hosting PostgreSQL add-on)
- `MAIL_*` (Brevo credentials recommended)
- `APP_URL` (your public domain, e.g. `https://invoicebot.yourcompany.com`)

## Useful commands

```bash
source venv/bin/activate
python run.py
python init_db.py
python seed.py
flask db migrate -m "description"
flask db upgrade
flask routes
```

## License

This project is released under a proprietary license. All rights are reserved by Mohammed.
Unauthorized copying, distribution, or derivative use is prohibited without express written permission.

---

Built with Flask and PostgreSQL for fast, secure invoice follow-up automation.