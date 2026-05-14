#!/usr/bin/env python
"""
Populate the dev database with realistic sample data for testing.

Usage:
    python seed.py
"""
import os
import sys
from datetime import date, datetime, timedelta, timezone

os.environ.setdefault("FLASK_ENV", "development")

from app import create_app, db
from app.models import User, Invoice, EmailSchedule, EmailLog


def seed():
    app = create_app("development")
    with app.app_context():
        print("🌱 Seeding database...")

        # Clear existing data
        EmailLog.query.delete()
        EmailSchedule.query.delete()
        Invoice.query.delete()
        User.query.delete()
        db.session.commit()

        # ── Users ──────────────────────────────────────
        users_data = [
            {"name": "Mohammed Tomar", "email": "mohammed@example.com", "plan": "starter"},
            {"name": "Alex Rivera",    "email": "alex@example.com",     "plan": "free"},
        ]
        users = []
        for ud in users_data:
            u = User(name=ud["name"], email=ud["email"], plan=ud["plan"])
            u.set_password("password123")
            db.session.add(u)
            users.append(u)
        db.session.flush()
        print(f"  Created {len(users)} users")

        # ── Invoices ───────────────────────────────────
        today = date.today()
        invoices_data = [
            # Mohammed's invoices
            {
                "user": users[0], "client_name": "Acme Corp", "client_email": "billing@acme.com",
                "invoice_number": "INV-001", "amount": 2500.00, "currency": "USD",
                "due_date": today - timedelta(days=12), "tone": "professional",
                "status": "pending", "payment_link": "https://stripe.com/pay/acme",
                "description": "Web app development — Phase 1",
                "logs": [(1, True), (2, True)],  # stages 1 and 2 already sent
            },
            {
                "user": users[0], "client_name": "Design Studio X", "client_email": "pay@designx.io",
                "invoice_number": "INV-002", "amount": 800.00, "currency": "USD",
                "due_date": today - timedelta(days=3), "tone": "polite",
                "status": "pending",
                "description": "Logo redesign",
                "logs": [(1, True)],
            },
            {
                "user": users[0], "client_name": "StartupFlow", "client_email": "finance@startupflow.co",
                "invoice_number": "INV-003", "amount": 4200.00, "currency": "USD",
                "due_date": today - timedelta(days=35), "tone": "firm",
                "status": "paid",
                "description": "API integration project",
                "logs": [(1, True), (2, True), (3, True)],
            },
            {
                "user": users[0], "client_name": "NovaTech", "client_email": "accounts@novatech.com",
                "invoice_number": "INV-004", "amount": 1200.00, "currency": "EUR",
                "due_date": today + timedelta(days=7), "tone": "polite",
                "status": "pending",
                "description": "Consulting — Q2 retainer",
                "logs": [],
            },
            # Alex's invoice (free plan — 1 of 3)
            {
                "user": users[1], "client_name": "Bright Media", "client_email": "billing@brightmedia.com",
                "invoice_number": "INV-001", "amount": 650.00, "currency": "USD",
                "due_date": today - timedelta(days=5), "tone": "polite",
                "status": "pending",
                "description": "Social media content package",
                "logs": [(1, True)],
            },
        ]

        for idata in invoices_data:
            inv = Invoice(
                user_id=idata["user"].id,
                client_name=idata["client_name"],
                client_email=idata["client_email"],
                invoice_number=idata.get("invoice_number"),
                amount=idata["amount"],
                currency=idata["currency"],
                due_date=idata["due_date"],
                tone=idata["tone"],
                status=idata["status"],
                description=idata.get("description"),
                payment_link=idata.get("payment_link"),
            )
            if idata["status"] == "paid":
                inv.marked_paid_at = datetime.now(timezone.utc)
            db.session.add(inv)
            db.session.flush()

            # Create schedules for all 3 stages
            for stage, delay in [(1, 1), (2, 5), (3, 10)]:
                send_at = datetime.combine(
                    idata["due_date"] + timedelta(days=delay),
                    datetime.min.time()
                ).replace(hour=9, tzinfo=timezone.utc)
                sent = any(lg[0] == stage for lg in idata["logs"])
                db.session.add(EmailSchedule(
                    invoice_id=inv.id, stage=stage, send_at=send_at, sent=sent
                ))

            # Create email logs for already-sent stages
            for stage, success in idata["logs"]:
                sent_at = datetime.combine(
                    idata["due_date"] + timedelta(days=[1, 5, 10][stage - 1]),
                    datetime.min.time()
                ).replace(hour=9, tzinfo=timezone.utc)
                db.session.add(EmailLog(
                    invoice_id=inv.id,
                    stage=stage,
                    subject=f"Stage {stage} reminder — {idata['client_name']}",
                    sent_at=sent_at,
                    sendgrid_message_id=f"fake-msg-id-{inv.id[:8]}-s{stage}",
                    success=success,
                ))

        db.session.commit()
        print(f"  Created {len(invoices_data)} invoices with schedules and logs")
        print()
        print("✅ Seed complete!")
        print()
        print("  Login credentials:")
        print("    mohammed@example.com / password123  (Starter plan)")
        print("    alex@example.com     / password123  (Free plan)")
        print()
        print("  Run: python run.py")


if __name__ == "__main__":
    seed()
