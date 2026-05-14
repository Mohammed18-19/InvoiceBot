#!/usr/bin/env python
"""
Run this script ONCE on a fresh clone to initialize Flask-Migrate.
After this, use 'flask db migrate' and 'flask db upgrade' for schema changes.

Usage:
    python init_db.py
"""
import os
import subprocess
import sys


def run(cmd):
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    print("\n🟢 InvoiceNudge — Database Setup\n")

    if not os.path.exists(".env"):
        print("⚠  No .env file found. Copying .env.example → .env")
        run("cp .env.example .env")
        print("   Edit .env with your DATABASE_URL before continuing.\n")
        sys.exit(0)

    print("Step 1: Initialize migrations folder")
    if os.path.exists("migrations"):
        print("  migrations/ already exists — skipping init")
    else:
        run("flask db init")

    print("\nStep 2: Generate initial migration")
    run("flask db migrate -m 'initial schema'")

    print("\nStep 3: Apply migration to database")
    code = run("flask db upgrade")

    if code == 0:
        print("\n✅ Database ready! Run: python run.py\n")
    else:
        print("\n❌ Migration failed. Check DATABASE_URL in .env\n")
        sys.exit(1)
