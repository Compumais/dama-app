from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class StockRequestForm(FlaskForm):
    branch_id = SelectField("Filial", coerce=int, validators=[DataRequired()])
    product_id = SelectField("Produto", coerce=int, validators=[DataRequired()])
    quantity = DecimalField(
        "Quantidade",
        places=3,
        rounding=None,
        validators=[DataRequired(), NumberRange(min=Decimal("0.001"))],
    )
    item_notes = StringField("Obs. do item", validators=[Optional(), Length(max=255)])
    notes = TextAreaField("Observação da requisição", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Criar requisição")


class StockRequestStatusForm(FlaskForm):
    status = SelectField("Novo status", validators=[DataRequired()])
    notes = StringField("Observação", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Atualizar status")
