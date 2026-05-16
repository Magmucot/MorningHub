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
        usr = User(usr_name=form.username.data)
        usr.set_pass(form.password.data)
        db.session.add(usr)
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
        
        default_layout = {
            "it_news": {"x": 0, "y": 0, "h": 6},
            "politics": {"x": 0, "y": 6, "h": 6},
            "ai_models": {"x": 0, "y": 12, "h": 6},
            "game_news": {"x": 0, "y": 18, "h": 6},
            "analog_clock": {"x": 3, "y": 0, "h": 4},
            "calendar": {"x": 3, "y": 4, "h": 8},
            "bookmarks": {"x": 3, "y": 12, "h": 6},
            "currency": {"x": 6, "y": 0, "h": 8},
            "crypto": {"x": 6, "y": 8, "h": 8},
            "ai_summary": {"x": 9, "y": 0, "h": 10},
            "weather": {"x": 9, "y": 10, "h": 8},
        }

        for idx, tip in enumerate(wid_def):
            layout = default_layout.get(tip, {"x": (idx % 4) * 3, "y": (idx // 4) * 6, "h": 6})
            w = WidgetConfig(
                usr_id=usr.id,
                w_tip=tip,
                poz=idx,
                is_act=(tip != "ai_summary"),
                x=layout["x"],
                y=layout["y"],
                w=3,
                h=layout["h"]
            )
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
        usr = User.query.filter_by(usr_name=form.username.data).first()
        if usr and usr.check_pass(form.password.data):
            login_user(usr)
            return redirect(url_for("dashboard.index"))
        flash("Неверное имя пользователя или пароль.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
