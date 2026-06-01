from app import limiter
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Invoice, EmailLog, EmailSchedule, EmailDraft

admin_bp = Blueprint("admin", __name__)

ADMIN_EMAIL = "aintomar.mohamed19@gmail.com"


def admin_required(f):
    """Decorator — only allows the admin email to access these routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.email != ADMIN_EMAIL:
            flash("Access denied.", "danger")
            return redirect(url_for("dashboard.home"))

        return f(*args, **kwargs)

    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def index():
    total_users = User.query.count()
    paying_users = User.query.filter(User.plan != "free").count()
    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(status="pending").count()
    paid_invoices = Invoice.query.filter_by(status="paid").count()
    blocked_users = User.query.filter_by(is_blocked=True).count()
    emails_sent = EmailLog.query.filter_by(success=True).count()
    emails_failed = EmailLog.query.filter_by(success=False).count()
    draft_count = EmailDraft.query.count()

    starter_count = User.query.filter_by(plan="starter").count()
    pro_count = User.query.filter_by(plan="pro").count()
    mrr = (starter_count * 10) + (pro_count * 20)

    recent_users = (
        User.query
        .order_by(User.created_at.desc())
        .limit(10)
        .all()
    )

    recent_logs = (
        EmailLog.query
        .order_by(EmailLog.sent_at.desc())
        .limit(20)
        .all()
    )

    upcoming = (
        EmailSchedule.query
        .join(Invoice)
        .filter(
            EmailSchedule.sent == False,
            Invoice.status == "pending",
        )
        .order_by(EmailSchedule.send_at)
        .limit(10)
        .all()
    )

    stats = {
        "total_users": total_users,
        "paying_users": paying_users,
        "free_users": total_users - paying_users,
        "total_invoices": total_invoices,
        "pending_invoices": pending_invoices,
        "paid_invoices": paid_invoices,
        "blocked_users": blocked_users,
        "draft_count": draft_count,
        "emails_sent": emails_sent,
        "emails_failed": emails_failed,
        "mrr": mrr,
    }

    return render_template(
        "admin/index.html",
        stats=stats,
        recent_users=recent_users,
        recent_logs=recent_logs,
        upcoming=upcoming,
        draft_count=draft_count,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = (
        User.query
        .order_by(User.created_at.desc())
        .all()
    )
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    invoices = (
        Invoice.query
        .filter_by(user_id=user_id)
        .order_by(Invoice.created_at.desc())
        .all()
    )
    logs = (
        EmailLog.query
        .join(Invoice)
        .filter(Invoice.user_id == user_id)
        .order_by(EmailLog.sent_at.desc())
        .limit(20)
        .all()
    )
    return render_template("admin/user_detail.html", user=user, invoices=invoices, logs=logs)


@admin_bp.route("/users/<user_id>/set-plan", methods=["POST"])
@login_required
@admin_required
def set_plan(user_id):
    user = User.query.get_or_404(user_id)
    plan = request.form.get("plan")
    if plan in ("free", "starter", "pro"):
        old_plan = user.plan
        user.plan = plan
        db.session.commit()
        flash(f"Updated {user.email} from {old_plan} → {plan}.", "success")
    else:
        flash("Invalid plan.", "danger")
    return redirect(url_for("admin.user_detail", user_id=user_id))


@admin_bp.route("/users/<user_id>/block", methods=["POST"])
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.email == ADMIN_EMAIL:
        flash("You cannot block the admin account.", "warning")
        return redirect(url_for("admin.user_detail", user_id=user_id))
    user.is_blocked = True
    db.session.commit()
    flash(f"{user.email} has been blocked.", "success")
    return redirect(url_for("admin.user_detail", user_id=user_id))


@admin_bp.route("/users/<user_id>/unblock", methods=["POST"])
@login_required
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()
    flash(f"{user.email} has been unblocked.", "success")
    return redirect(url_for("admin.user_detail", user_id=user_id))


@admin_bp.route("/trigger-emails", methods=["POST"])
@login_required
@admin_required
def trigger_emails():
    from app.scheduler.jobs import process_due_emails

    try:
        process_due_emails()
        flash("✅ Email scheduler triggered. Check logs for results.", "success")
    except Exception as e:
        flash(f"❌ Scheduler error: {str(e)}", "danger")
    return redirect(url_for("admin.index"))


@admin_bp.route("/invoices")
@login_required
@admin_required
def all_invoices():
    invoices = (
        Invoice.query
        .order_by(Invoice.created_at.desc())
        .all()
    )
    return render_template("admin/invoices.html", invoices=invoices)


@admin_bp.route("/email-drafts")
@login_required
@admin_required
def email_drafts():
    page = request.args.get("page", 1, type=int)
    drafts = (
        EmailDraft.query
        .order_by(EmailDraft.created_at.desc())
        .paginate(page=page, per_page=50)
    )
    return render_template("admin/email_drafts.html", drafts=drafts)


@admin_bp.route("/email-drafts/<draft_id>")
@login_required
@admin_required
def email_draft_detail(draft_id):
    draft = EmailDraft.query.get_or_404(draft_id)
    return render_template("admin/email_draft_detail.html", draft=draft)


@admin_bp.route("/logs")
@login_required
@admin_required
def logs():
    page = request.args.get("page", 1, type=int)
    logs = (
        EmailLog.query
        .order_by(EmailLog.sent_at.desc())
        .paginate(page=page, per_page=50)
    )
    return render_template("admin/logs.html", logs=logs)
