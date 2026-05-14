import io
from flask import Blueprint, Response, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app.services.aggregator import sobr_utro_svodka_tekst
from app.services.currency import poluch_valuta_kurs
from app.services.it_news import it_novosti
from app.services.politics import polit_novosti
from app.services.ai_models import poluch_ai_mod_novosti
from app.services.ai_summary import poluch_ai_svodka
from app.services.weather import pog_prognoz
from app.services.crypto import poluch_kripta_kurs

bp = Blueprint("api", __name__, url_prefix="/api/v1")


@bp.route("/widgets/crypto", methods=["GET"])
@login_required
def api_crypto():
    return jsonify(poluch_kripta_kurs(current_user.kripta_spis))


@bp.route("/widgets/weather", methods=["GET"])
@login_required
def api_weather():
    rez = pog_prognoz(current_user)
    # Если город был разрешен, сохраняем координаты
    db.session.commit()
    return jsonify(rez)


@bp.route("/bookmarks", methods=["GET", "POST"])
@login_required
def api_bookmarks():
    if request.method == "POST":
        d = request.get_json()
        if not d or not d.get("url") or not d.get("title"):
            return jsonify({"error": "Требуется title и url"}), 400

        bm = Bookmark(u_id=current_user.id, title=d["title"], url=d["url"], icon=d.get("icon", "fa-link"))
        db.session.add(bm)
        db.session.commit()
        return jsonify({"success": True, "id": bm.id})

    bm_spis = Bookmark.query.filter_by(u_id=current_user.id).all()
    return jsonify([{"id": bm.id, "title": bm.title, "url": bm.url, "icon": bm.icon} for bm in bm_spis])


@bp.route("/bookmarks/<int:bm_id>", methods=["DELETE"])
@login_required
def api_delete_bookmark(bm_id):
    bm = Bookmark.query.filter_by(id=bm_id, u_id=current_user.id).first()
    if not bm:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(bm)
    db.session.commit()
    return jsonify({"success": True})


@bp.route("/widgets/save-grid", methods=["PATCH"])
@login_required
def save_grid_widgets():
    d = request.get_json()
    if not d or "items" not in d:
        return jsonify({"error": "Invalid payload"}), 400

    wid_spis = WidgetConfig.query.filter_by(u_id=current_user.id).all()
    wid_karta = {w.w_tip: w for w in wid_spis}

    for i in d["items"]:
        w_tip = i.get("widget_type")
        if w_tip in wid_karta:
            w = wid_karta[w_tip]
            w.x = i.get("x", 0)
            w.y = i.get("y", 0)
            w.w = i.get("w", 4)
            w.h = i.get("h", 3)

    db.session.commit()
    return jsonify({"success": True})


@bp.route("/widgets/ai-summary", methods=["GET"])
@login_required
def api_ai_summary():
    return jsonify(poluch_ai_svodka(current_user))


@bp.route("/user/lock-grid", methods=["PATCH"])
@login_required
def lock_grid():
    d = request.get_json()
    if not d or "is_grid_locked" not in d:
        return jsonify({"error": "Invalid payload"}), 400

    current_user.setka_lock = bool(d["is_grid_locked"])
    db.session.commit()
    return jsonify({"success": True, "is_grid_locked": current_user.setka_lock})


@bp.route("/widgets/ai-models", methods=["GET"])
@login_required
def api_ai_models():
    return jsonify(poluch_ai_mod_novosti())


@bp.route("/widgets/it-news", methods=["GET"])
@login_required
def api_it_news():
    return jsonify(it_novosti())


@bp.route("/widgets/currency", methods=["GET"])
@login_required
def api_currency():
    return jsonify(poluch_valuta_kurs(current_user.valuta_spis))


@bp.route("/widgets/politics", methods=["GET"])
@login_required
def api_politics():
    return jsonify(polit_novosti())


@bp.route("/widgets/<w_tip>/toggle", methods=["PATCH"])
@login_required
def toggle_widget(w_tip: str):
    w = WidgetConfig.query.filter_by(u_id=current_user.id, w_tip=w_tip).first()
    if not w:
        return jsonify({"error": "Widget not found"}), 404

    d = request.get_json()
    if not d or "is_active" not in d:
        return jsonify({"error": "Invalid payload"}), 400

    w.is_akt = bool(d["is_active"])
    db.session.commit()

    return jsonify({"success": True, "is_active": w.is_akt})


@bp.route("/export", methods=["GET"])
@login_required
def export_summary():
    fmt = request.args.get("format", "txt")

    akt_wid_spis = (
        WidgetConfig.query.filter_by(u_id=current_user.id, is_akt=True).order_by(WidgetConfig.poz).all()
    )

    tekst = sobr_utro_svodka_tekst(akt_wid_spis)

    if fmt == "txt":
        return Response(
            tekst,
            mimetype="text/plain",
            headers={"Content-disposition": "attachment; filename=morning_summary.txt"},
        )
    elif fmt == "csv":
        # Упрощенная CSV версия: просто заменяем переносы строк
        csv_t = tekst.replace("\n", '","')
        csv_t = f'"{csv_t}"'
        return Response(
            csv_t, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=morning_summary.csv"}
        )
    else:
        return jsonify({"error": "Unsupported format"}), 400
