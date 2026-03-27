from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField(
        "E-mail",
        validators=[DataRequired(), Email(), Length(max=255)],
    )
    password = PasswordField(
        "Senha",
        validators=[DataRequired(), Length(min=6, max=255)],
    )
    remember_me = BooleanField("Lembrar de mim")
    submit = SubmitField("Entrar")
