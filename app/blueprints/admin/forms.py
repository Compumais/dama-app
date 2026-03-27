from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class BranchForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    code = StringField("Codigo", validators=[DataRequired(), Length(max=20)])
    active = BooleanField("Ativa", default=True)
    submit = SubmitField("Salvar filial")


class ProductForm(FlaskForm):
    barcode = StringField("Codigo de barras", validators=[DataRequired(), Length(max=60)])
    internal_code = StringField("Codigo interno", validators=[Optional(), Length(max=40)])
    description = StringField("Descricao", validators=[DataRequired(), Length(max=255)])
    unit = StringField("Unidade", validators=[DataRequired(), Length(max=10)])
    active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar produto")


class UserForm(FlaskForm):
    full_name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(),
            Length(max=255),
            Regexp(r"^[^@\s]+@[^@\s]+$", message="Informe um e-mail válido."),
        ],
    )
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6, max=255)])
    role_id = SelectField("Perfil", coerce=int, validators=[DataRequired()])
    branch_id = SelectField("Filial", coerce=int, validators=[Optional()], default=0)
    active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")


class UserEditForm(FlaskForm):
    full_name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(),
            Length(max=255),
            Regexp(r"^[^@\s]+@[^@\s]+$", message="Informe um e-mail válido."),
        ],
    )
    password = PasswordField(
        "Nova senha (deixe em branco para manter)",
        validators=[Optional(), Length(min=6, max=255)],
    )
    role_id = SelectField("Perfil", coerce=int, validators=[DataRequired()])
    branch_id = SelectField("Filial", coerce=int, validators=[Optional()], default=0)
    active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar alterações")
