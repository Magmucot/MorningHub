from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Подтвердите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, field: StringField) -> None:
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError("Это имя пользователя уже занято.")
