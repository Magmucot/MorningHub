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
        u = User(u_name=form.username.data)
        u.set_pass(form.password.data)
        db.session.add(u)
        db.session.flush()

        wid_def = [
            "it_news",
            "game_news",
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
        for idx, tip in enumerate(wid_def):
            w = WidgetConfig(u_id=u.id, w_tip=tip, poz=idx, is_akt=True)
            db.session.add(w)

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
        u = User.query.filter_by(u_name=form.username.data).first()
        if u and u.check_pass(form.password.data):
            login_user(u)
            return redirect(url_for("dashboard.index"))
        flash("Неверное имя пользователя или пароль.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
