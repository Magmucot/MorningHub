from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user, current_user

from app.extensions import db
from app.forms.auth import LoginForm, RegisterForm
from app.models.user import User
from app.models.widget import WidgetConfig

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Получаем ID пользователя

        # Добавляем стандартные виджеты по умолчанию
        default_widgets = [
            "it_news",
            "currency",
            "politics",
            "ai_models",
            "analog_clock",
            "calendar",
            "ai_summary",
            "weather",
            "bookmarks",
            "crypto",
        ]
        for idx, w_type in enumerate(default_widgets):
            widget = WidgetConfig(user_id=user.id, widget_type=w_type, position=idx, is_active=True)
            db.session.add(widget)

        db.session.commit()
        flash("Регистрация успешна! Теперь вы можете войти.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("dashboard.index"))
        flash("Неверное имя пользователя или пароль.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
