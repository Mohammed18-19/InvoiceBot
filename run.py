import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

from app import create_app, db
from app.models import User, Invoice, EmailSchedule, EmailLog

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Invoice": Invoice,
        "EmailSchedule": EmailSchedule,
        "EmailLog": EmailLog,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)
