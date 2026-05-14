from flask_wtf import FlaskForm
from wtforms import (
    StringField, DecimalField, DateField, TextAreaField,
    SelectField, SubmitField, IntegerField
)
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length


class InvoiceForm(FlaskForm):
    client_name = StringField("Client name", validators=[DataRequired(), Length(1, 255)])
    client_email = StringField("Client email", validators=[DataRequired(), Email()])
    invoice_number = StringField("Invoice number", validators=[Optional(), Length(0, 100)])
    amount = DecimalField(
        "Amount",
        validators=[DataRequired(), NumberRange(min=0.01)],
        places=2,
        render_kw={"step": "0.01", "placeholder": "500.00"}
    )
    currency = SelectField(
        "Currency",
        choices=[("USD","USD"),("EUR","EUR"),("GBP","GBP"),("MAD","MAD"),("AED","AED"),("CAD","CAD"),("AUD","AUD")],
        default="USD",
    )
    due_date = DateField("Due date", validators=[DataRequired()])
    description = TextAreaField("Description / notes", validators=[Optional(), Length(0, 1000)])
    payment_link = StringField("Payment link (optional)", validators=[Optional(), Length(0, 500)])
    tone = SelectField(
        "Email tone",
        choices=[
            ("polite", "Polite"),
            ("professional", "Professional"),
            ("firm", "Firm"),
        ],
        default="polite",
    )
    stage1_delay = IntegerField("Stage 1 delay", default=1, validators=[NumberRange(0, 30)])
    stage2_delay = IntegerField("Stage 2 delay", default=5, validators=[NumberRange(1, 60)])
    stage3_delay = IntegerField("Stage 3 delay", default=10, validators=[NumberRange(2, 90)])
    submit = SubmitField("Add invoice & start sequence")