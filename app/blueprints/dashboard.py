from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.forms.settings import SettingsForm
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app.services.uploader import save_fon_img

bp = Blueprint("dashboard", __name__)


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
    est_wid = WidgetConfig.query.filter_by(usr_id=usr_id).all()
    est_tipi = {w.w_tip for w in est_wid}

    nov_wid = []
    for tip in wid_def:
        if tip not in est_tipi:
            # Расставляем новые виджеты ниже существующих (или по умолчанию)
            nov_wid.append(WidgetConfig(usr_id=usr_id, w_tip=tip, is_act=True))

    if nov_wid:
        db.session.add_all(nov_wid)
        db.session.commit()


@bp.route("/")
@login_required
def index():
    _prover_wid_def(current_user.id)
    # Получаем активные виджеты пользователя (для GridStack)
    wid_spis = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).all()
    bm_spis = Bookmark.query.filter_by(usr_id=current_user.id).all()
    return render_template("dashboard/index.html", widgets=wid_spis, bookmarks=bm_spis)


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
                if g and g != current_user.weath_gorod:
                    current_user.weath_gorod = g
                    current_user.weath_lat = None
                    current_user.weath_lon = None

            # Настройки ИИ
            current_user.ai_key = request.form.get("ai_api_key", "").strip() or None
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
                try:
                    current_user.wid_prozr = float(p)
                except ValueError:
                    pass

            db.session.commit()
            flash("Настройки успешно обновлены.", "success")

            if form.fon_img.data:
                try:
                    imya_f = save_fon_img(form.fon_img.data)
                    if imya_f:
                        current_user.back_img = imya_f
                        db.session.commit()
                        flash("Фоновое изображение успешно обновлено.", "success")
                except ValueError as e:
                    flash(str(e), "danger")
            return redirect(url_for("dashboard.settings"))
        else:
            for f, err_spis in form.errors.items():
                for e in err_spis:
                    flash(f"{e}", "danger")

    # Все виджеты для управления переключателями
    wid_spis = WidgetConfig.query.filter_by(usr_id=current_user.id).order_by(WidgetConfig.poz).all()
    return render_template("dashboard/settings.html", form=form, widgets=wid_spis)
