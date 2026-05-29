from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
@login_required
def home():
    stats = {
        "total_outstanding": 0,
        "total": 0,
        "users": 0,
        "invoices": 0
    }

    return render_template("dashboard/index.html", stats=stats)

@dashboard_bp.route("/landing")
def landing():
    return render_template("landing/index.html")
