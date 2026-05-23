from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
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


def _chk_wid_def(usr_id: int):
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

    from app.models.user import User
    usr = User.query.get(usr_id)
    is_fr = usr.is_fr if usr else False

    ex_wid = WidgetConfig.query.filter_by(usr_id=usr_id).all()
    ex_tips = {w.w_tip for w in ex_wid}

    new_wid = []
    start_pos = len(ex_wid)
    offset = 0

    for tip in wid_def:
        if tip not in ex_tips:
            pos = start_pos + offset
            layout = default_layout.get(tip, {"x": (pos % 4) * 3, "y": (pos // 4) * 6, "h": 6})
            x_val = layout["x"]
            y_val = layout["y"]
            w_val = 3
            h_val = layout["h"]
            if is_fr:
                x_val *= 10
                w_val *= 10
                y_val = int(round(y_val * 5.8))
                h_val = max(1, int(round(h_val * 5.8 - 0.8)))
            new_wid.append(
                WidgetConfig(
                    usr_id=usr_id,
                    w_tip=tip,
                    is_act=(tip != "ai_summary"),
                    poz=pos,
                    x=x_val,
                    y=y_val,
                    w=w_val,
                    h=h_val
                )
            )
            offset += 1

    if new_wid:
        db.session.add_all(new_wid)
        db.session.commit()


@bp.route("/")
@login_required
def index():
    _chk_wid_def(current_user.id)
    # Получаем активные виджеты пользователя (для GridStack)
    wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).order_by(WidgetConfig.poz.asc()).all()
    bm_lst = Bookmark.query.filter_by(usr_id=current_user.id).all()
    return render_template("dashboard/index.html", widgets=wid_lst, bookmarks=bm_lst)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    _chk_wid_def(current_user.id)
    form = SettingsForm()

    if request.method == "POST":
        if form.validate_on_submit():
            # Обработка города погоды
            if "weather_city" in request.form:
                g = request.form.get("weather_city", "").strip()
                if g and g != current_user.pog_city:
                    current_user.pog_city = g
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
                c_raw = request.form.get("crypto_tracking", "").strip()
                c_lst = [x.strip() for x in c_raw.split(",") if x.strip()][:10]
                current_user.crypto_lst = ",".join(c_lst)
            if "currency_tracking" in request.form:
                v_raw = request.form.get("currency_tracking", "").strip()
                v_lst = [x.strip() for x in v_raw.split(",") if x.strip()][:10]
                current_user.val_lst = ",".join(v_lst)
            if "clock_style" in request.form:
                current_user.clock_stil = request.form.get("clock_style", "both")

            # Настройки UI
            t = request.form.get("theme")
            if t in ["light", "dark"]:
                current_user.theme = t

            c = request.form.get("widget_color")
            if c:
                current_user.wid_clr = c

            p = request.form.get("widget_opacity")
            if p:
                opacity = _normalize_widget_opacity(p)
                if opacity is not None:
                    current_user.wid_op = opacity

            # Режим расположения
            if "is_fr" in request.form:
                nov_fr = request.form.get("is_fr") == "true"
                if nov_fr != current_user.is_fr:
                    current_user.is_fr = nov_fr
                    # Используем прямой запрос к БД чтобы получить свежие данные,
                    # избегая потенциально устаревшего кэша relationship после коммита в _chk_wid_def
                    wids = WidgetConfig.query.filter_by(usr_id=current_user.id).all()
                    for w in wids:
                        if nov_fr:
                            w.x = min(w.x * 10, 110)
                            w.w = min(max(1, w.w * 10), 120)
                            w.y = int(round(w.y * 5.8))
                            w.h = max(1, int(round(w.h * 5.8 - 0.8)))
                        else:
                            w.x = max(0, min(11, w.x // 10))
                            w.w = max(1, min(12, w.w // 10))
                            w.y = max(0, min(100, int(round(w.y / 5.8))))
                            w.h = max(1, min(20, int(round((w.h + 0.8) / 5.8))))

            # Параметры фона
            sz = request.form.get("bg_sz")
            if sz in ["cover", "contain", "auto"]:
                current_user.bg_sz = sz

            ps = request.form.get("bg_ps")
            if ps in ["center", "top", "left", "right", "bottom"]:
                current_user.bg_ps = ps

            db.session.commit()
            flash("Настройки успешно обновлены.", "success")

            if form.back_img.data:
                try:
                    old_f = current_user.back_img
                    imya_f = save_back_img(form.back_img.data)
                    if imya_f:
                        current_user.back_img = imya_f
                        db.session.commit()
                        flash("Фоновое изображение успешно обновлено.", "success")
                        if old_f:
                            import os
                            old_p = os.path.join(current_app.config["UPLOAD_FOLDER"], old_f)
                            if os.path.exists(old_p):
                                try:
                                    os.remove(old_p)
                                except Exception:
                                    pass
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
