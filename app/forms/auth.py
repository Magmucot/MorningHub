from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models.user import User
import re


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=8)])

    confirm_password = PasswordField("Подтвердите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")

    def validate_password(self, password):
        p = password.data
        if not re.search(r"[A-Z]", p):
            raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
        if not re.search(r"[a-z]", p):
            raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
        if not re.search(r"[0-9]", p):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")

    def validate_username(self, field: StringField) -> None:
        usr = User.query.filter_by(u_name=field.data).first()
        if usr:
            raise ValidationError("Это имя пользователя уже занято.")
