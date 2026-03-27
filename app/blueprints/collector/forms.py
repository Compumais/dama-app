from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import DecimalField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ScanForm(FlaskForm):
    barcode = StringField("Código de barras", validators=[DataRequired()])
    quantity = DecimalField(
        "Quantidade",
        places=3,
        default=Decimal("1"),
        validators=[DataRequired(), NumberRange(min=Decimal("0.001"))],
    )
    submit = SubmitField("Ler código")
