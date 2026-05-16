from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.forms.settings import SettingsForm
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app.services.uploader import save_back_img

bp = Blueprint("dashboard", __name__)


def _normalize_widget_opacity(raw_value: str) -> float | None:
    try:
        value = float(raw_value)
    except ValueError:
        return None

    if value > 1:
        value /= 100

    return max(0.1, min(1.0, value))


def _prover_wid_def(usr_id: int):
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

    est_wid = WidgetConfig.query.filter_by(usr_id=usr_id).all()
    est_tipi = {w.w_tip for w in est_wid}

    nov_wid = []
    start_pos = len(est_wid)
    offset = 0

    for tip in wid_def:
        if tip not in est_tipi:
            pos = start_pos + offset
            layout = default_layout.get(tip, {"x": (pos % 4) * 3, "y": (pos // 4) * 6, "h": 6})
            nov_wid.append(
                WidgetConfig(
                    usr_id=usr_id,
                    w_tip=tip,
                    is_act=True,
                    poz=pos,
                    x=layout["x"],
                    y=layout["y"],
                    w=3,
                    h=layout["h"]
                )
            )
            offset += 1

    if nov_wid:
        db.session.add_all(nov_wid)
        db.session.commit()


@bp.route("/")
@login_required
def index():
    _prover_wid_def(current_user.id)
    # Получаем активные виджеты пользователя (для GridStack)
    wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).order_by(WidgetConfig.poz.asc()).all()
    bm_lst = Bookmark.query.filter_by(usr_id=current_user.id).all()
    return render_template("dashboard/index.html", widgets=wid_lst, bookmarks=bm_lst)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    _prover_wid_def(current_user.id)
    form = SettingsForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # Обработка города погоды
            if "weather_city" in request.form:
                g = request.form.get("weather_city", "").strip()
                if g and g != current_user.weath_city:
                    current_user.weath_city = g
                    current_user.weath_lat = None
                    current_user.weath_lon = None

            # Настройки ИИ
            new_key = request.form.get("ai_api_key", "").strip()
            if new_key:
                current_user.ai_key = new_key
            current_user.ai_url = request.form.get("ai_base_url", "").strip() or None
            current_user.ai_model = request.form.get("ai_model", "").strip() or None

            # Настройки виджетов
            if "crypto_tracking" in request.form:
                current_user.crypto_lst = request.form.get("crypto_tracking", "").strip()
            if "currency_tracking" in request.form:
                current_user.val_lst = request.form.get("currency_tracking", "").strip()
            if "clock_style" in request.form:
                current_user.clock_stile = request.form.get("clock_style", "both")

            # Настройки UI
            t = request.form.get("theme")
            if t in ["light", "dark"]:
                current_user.theme = t

            c = request.form.get("widget_color")
            if c:
                current_user.wid_cvet = c

            p = request.form.get("widget_opacity")
            if p:
                opacity = _normalize_widget_opacity(p)
                if opacity is not None:
                    current_user.wid_prozr = opacity

            db.session.commit()
            flash("Настройки успешно обновлены.", "success")

            if form.back_img.data:
                try:
                    imya_f = save_back_img(form.back_img.data)
                    if imya_f:
                        current_user.back_img = imya_f
                        db.session.commit()
                        flash("Фоновое изображение успешно обновлено.", "success")
                except ValueError as e:
                    flash(str(e), "danger")
            return redirect(url_for("dashboard.settings"))
        else:
            for f, err_lst in form.errors.items():
                for e in err_lst:
                    flash(f"{e}", "danger")

    # Все виджеты для управления переключателями
    wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id).order_by(WidgetConfig.poz).all()
    return render_template("dashboard/settings.html", form=form, widgets=wid_lst)
