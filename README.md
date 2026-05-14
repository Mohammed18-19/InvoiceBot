# InvoiceNudge 🟢

**Automated invoice follow-up for freelancers. You do the work. We do the chasing.**

A full-stack Flask SaaS that sends configurable multi-stage reminder emails when freelance invoices go unpaid — automatically, on a schedule, with tone control (polite / professional / firm).

---

## What it does

1. You add an invoice (client email, amount, due date, tone)
2. InvoiceNudge schedules 3 escalating reminder emails (configurable delays)
3. Emails fire automatically at 09:00 UTC each day they're due
4. You mark the invoice paid — reminders stop
5. You upgrade for more invoices and premium features

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11 + Flask 3 |
| Database | PostgreSQL + SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login + Werkzeug password hashing |
| Forms | Flask-WTF + WTForms |
| Email | SendGrid (100 emails/day free) |
| Payments | Stripe Checkout + webhooks |
| Scheduler | APScheduler (runs in-process, no Redis needed) |
| Frontend | Jinja2 templates + Bootstrap 5 CDN |
| Deploy | Railway (or any Gunicorn-compatible host) |

---

## Project structure

```
invoicenudge/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # DB models: User, Invoice, EmailSchedule, EmailLog
│   ├── auth/
│   │   ├── forms.py         # RegisterForm, LoginForm
│   │   └── routes.py        # /auth/register, /auth/login, /auth/logout
│   ├── dashboard/
│   │   └── routes.py        # / (main dashboard with stats)
│   ├── invoices/
│   │   ├── forms.py         # InvoiceForm
│   │   └── routes.py        # CRUD + schedule creation
│   ├── billing/
│   │   └── routes.py        # Stripe checkout, webhook, portal
│   ├── email_service/
│   │   └── __init__.py      # 9 email templates (3 tones × 3 stages) + SendGrid send
│   ├── scheduler/
│   │   └── jobs.py          # APScheduler hourly job — sends due emails
│   ├── templates/
│   │   ├── base.html        # Sidebar layout + Bootstrap 5
│   │   ├── auth/            # login.html, register.html
│   │   ├── dashboard/       # index.html
│   │   ├── invoices/        # list.html, new.html, detail.html
│   │   └── billing/         # upgrade.html
│   └── static/
│       ├── css/
│       └── js/
├── config.py                # Dev / Production configs + plan limits
├── run.py                   # Entry point
├── init_db.py               # One-time DB initializer
├── seed.py                  # Dev seed data
├── requirements.txt
├── Procfile                 # For Railway/Heroku
├── railway.toml
└── .env.example
```

---

## Pricing

| Plan | Price | Active invoices | Features |
|------|-------|----------------|----------|
| Free | $0/mo | 3 | Basic 3-stage sequence |
| Starter | $9/mo | 20 | Tone control, custom delays, remove branding |
| Pro | $19/mo | Unlimited | Everything + custom templates, WhatsApp (soon) |

---

## Local setup (Day 1)

### 1. Clone and create venv

```bash
git clone <your-repo-url>
cd invoicenudge
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create PostgreSQL database

```bash
createdb invoicenudge_dev
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in:
#   DATABASE_URL=postgresql://localhost/invoicenudge_dev
#   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
#   SENDGRID_API_KEY=  (get free at sendgrid.com)
#   MAIL_FROM=you@yourdomain.com
```

### 4. Initialise database

```bash
python init_db.py
```

Or manually:
```bash
flask db init
flask db migrate -m "initial schema"
flask db upgrade
```

### 5. (Optional) Seed with sample data

```bash
python seed.py
# Creates 2 test users with invoices, schedules, and email logs
# Login: mohammed@example.com / password123
```

### 6. Run

```bash
python run.py
# App runs at http://localhost:5000
```

---

## Stripe setup (Day 5)

### 1. Create products and prices in Stripe Dashboard

Go to [stripe.com/dashboard](https://dashboard.stripe.com) → Products → Add product

- **InvoiceNudge Starter**: $9.00/month recurring
- **InvoiceNudge Pro**: $19.00/month recurring

Copy the `price_xxx` IDs into your `.env`.

### 2. Set up webhook

In Stripe Dashboard → Developers → Webhooks:

- Endpoint URL: `https://yourdomain.com/billing/webhook`
- Events to listen for:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`

Copy the webhook signing secret (`whsec_xxx`) into `.env`.

### 3. Test locally with Stripe CLI

```bash
stripe listen --forward-to localhost:5000/billing/webhook
```

---

## Deploy to Railway (Day 5)

### Option A: GitHub auto-deploy (recommended)

```bash
git init
git add .
git commit -m "Initial commit — InvoiceNudge MVP"
git remote add origin git@github.com:your-username/invoicenudge.git
git push -u origin main
```

Then in [railway.app](https://railway.app):
1. New project → Deploy from GitHub repo
2. Add PostgreSQL plugin (Railway provides `DATABASE_URL` automatically)
3. Add all env vars from `.env.example` in Railway's Variables tab
4. Set `FLASK_ENV=production`
5. Set `APP_URL=https://your-railway-app.up.railway.app`

Railway auto-detects the `Procfile` and deploys.

### Post-deploy: run migrations

In Railway shell tab:
```bash
flask db upgrade
```

### Option B: Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway run flask db upgrade
```

---

## Email sequence logic

When you create an invoice, 3 `EmailSchedule` rows are created:

```
Invoice due_date: May 15, 2026
  Stage 1 → send at May 16, 09:00 UTC  (due_date + 1 day)
  Stage 2 → send at May 20, 09:00 UTC  (due_date + 5 days)
  Stage 3 → send at May 25, 09:00 UTC  (due_date + 10 days)
```

The APScheduler job runs every 60 minutes, finds all `EmailSchedule` rows where:
- `sent = False`
- `send_at <= now`
- Invoice `status = 'pending'`

...and sends them via SendGrid, logging the result to `EmailLog`.

When you mark an invoice paid, all unsent schedules are marked `sent=True` — no more emails go out.

---

## Email templates

9 templates total: 3 tones × 3 stages. Located in `app/email_service/__init__.py`.

| Tone | Best for |
|------|----------|
| Polite | Long-term clients, creative work |
| Professional | Corporate clients, B2B |
| Firm | Overdue situations, unreliable payers |

All templates support `{payment_link}` substitution — if you added a payment link, clients can pay with one click directly from the email.

---

## Adding WhatsApp reminders (Pro tier — Week 3)

You already have WhatsApp Cloud API experience from BookBot. The integration is straightforward:

```python
# In app/email_service/whatsapp.py
import requests

def send_whatsapp_reminder(invoice, stage):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": invoice.client_whatsapp,
        "type": "template",
        "template": {
            "name": f"invoice_reminder_stage_{stage}",
            "language": {"code": "en"},
            "components": [...]
        }
    }
    # ... same pattern as BookBot
```

Add `client_whatsapp` field to `Invoice` model and a new migration. Gate it behind the Pro plan check.

---

## Go-to-market — Day 1 validation post

Post this verbatim on r/freelance:

> **"How many hours a month do you spend chasing unpaid invoices?"**
>
> I've been talking to freelancers and the #1 complaint after finding clients is getting paid.
> Just curious — do you manually follow up when invoices go past due, or do you use a tool?
> What does that process look like for you?

Let it get 20+ replies. DM the top responders with:

> "Hey [name] — saw your comment. I built a tool that automates the entire follow-up sequence — 3 emails, configurable tone, fires automatically. Still early. Want free 30-day access in exchange for honest feedback? No card. [your-url]"

Target: 10 free signups by end of Day 6, 1 paid by Day 7.

---

## Revenue path

| Milestone | Requirement | Timeline |
|-----------|-------------|----------|
| $0 → $500/mo | 55 users, 10% convert to $9 Starter | Weeks 1–4 |
| $500 → $1k/mo | 111 Starter OR mix with Pro | Month 2 |
| $1k → $5k/mo | Integrations + Product Hunt launch | Month 3–5 |
| $5k → $10k/mo | Agency tier + WhatsApp + affiliate program | Month 6–9 |

---

## Development commands

```bash
# Run dev server
python run.py

# Create new migration after model changes
flask db migrate -m "describe the change"
flask db upgrade

# Open Flask shell
flask shell

# Manually trigger the email scheduler job (for testing)
python -c "
import os; os.environ['FLASK_ENV']='development'
from app import create_app, db
from app.scheduler.jobs import process_due_emails
app = create_app('development')
with app.app_context(): process_due_emails()
"
```

---

## License

MIT — build, fork, sell.
