from pathlib import Path
import re

p = Path("app/auth/routes.py")
text = p.read_text()

new_logout = """
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out. See you soon!", "info")
    return redirect(url_for("dashboard.landing"))
"""

text = re.sub(
    r"@auth_bp\.route\(\"/logout\"\)[\\s\\S]*?def logout\(\):[\\s\\S]*?(?=@auth_bp\.route|@|$)",
    new_logout.strip() + "\n\n",
    text
)

p.write_text(text)
print("✔ logout cleaned")
