from flask import Blueprint, Response, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app.services.aggregator import sobr_summary_t
from app.services.currency import get_val_kurs
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_models_news
from app.services.ai_summary import get_ai_summary
from app.services.weather import weath_prog
from app.services.crypto import get_crypto_kurs
from app.services.game_news import get_game_news


def _safe_commit() -> bool:
    """Безопасное выполнение транзакций БД с автоматическим откатом при ошибке."""
    try:
        _safe_commit()
        return True
    except SQLAlchemyError as err:
        db.session.rollback()
        logger.error("Ошибка транзакции БД: %s", err)
        return False


bp = Blueprint("api", __name__, url_prefix="/api/v1")


@bp.route("/widgets/crypto", methods=["GET"])
@login_required
def api_crypto():
    return jsonify(get_crypto_kurs(current_user.crypto_lst))


@bp.route("/widgets/weather", methods=["GET"])
@login_required
def api_weather():
    res = weath_prog(current_user)
    # Если город был разрешен, сохраняем координаты
    _safe_commit()
    return jsonify(res)


@bp.route("/bookmarks", methods=["GET", "POST"])
@login_required
def api_bookmarks():
    if request.method == "POST":
        data = request.get_json()
        if not data or not data.get("url") or not data.get("title"):
            return jsonify({"error": "Требуется title и url"}), 400

        bm = Bookmark(usr_id=current_user.id, title=data["title"], url=data["url"], icon=data.get("icon", "fa-link"))
        db.session.add(bm)
        _safe_commit()
        return jsonify({"success": True, "id": bm.id})

    bm_lst = Bookmark.query.filter_by(usr_id=current_user.id).all()
    return jsonify([{"id": bm.id, "title": bm.title, "url": bm.url, "icon": bm.icon} for bm in bm_lst])


@bp.route("/bookmarks/<int:bm_id>", methods=["DELETE"])
@login_required
def api_delete_bookmark(bm_id):
    bm = Bookmark.query.filter_by(id=bm_id, usr_id=current_user.id).first()
    if not bm:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(bm)
    _safe_commit()
    return jsonify({"success": True})


@bp.route("/widgets/save-grid", methods=["PATCH"])
@login_required
def save_grid_widgets():
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id).all()
    wid_karta = {w.w_tip: w for w in wid_lst}

    for i in data["items"]:
        tip = i.get("widget_type")
        if tip in wid_karta:
            w = wid_karta[tip]
            w.x = i.get("x", w.x)
            w.y = i.get("y", w.y)
            w.w = i.get("w", w.w)
            w.h = i.get("h", w.h)

    _safe_commit()
    return jsonify({"success": True})


@bp.route("/widgets/ai-summary", methods=["GET"])
@login_required
async def api_ai_summary():
    return jsonify(await get_ai_summary(current_user))


@bp.route("/user/lock-grid", methods=["PATCH"])
@login_required
def lock_grid():
    data = request.get_json()
    if not data or "is_grid_locked" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    current_user.setka_lock = bool(data["is_grid_locked"])
    _safe_commit()
    return jsonify({"success": True, "is_grid_locked": current_user.setka_lock})


@bp.route("/widgets/ai-models", methods=["GET"])
@login_required
def api_ai_models():
    return jsonify(get_ai_models_news())


@bp.route("/widgets/it-news", methods=["GET"])
@login_required
def api_it_news():
    return jsonify(get_it_news())


@bp.route("/widgets/game-news", methods=["GET"])
@login_required
def api_game_news():
    return jsonify(get_game_news())


@bp.route("/widgets/currency", methods=["GET"])
@login_required
def api_currency():
    return jsonify(get_val_kurs(current_user.val_lst))


@bp.route("/widgets/politics", methods=["GET"])
@login_required
def api_politics():
    return jsonify(get_polit_news())


@bp.route("/widgets/<w_tip>/toggle", methods=["PATCH"])
@login_required
def toggle_widget(w_tip: str):
    w = WidgetConfig.query.filter_by(usr_id=current_user.id, w_tip=w_tip).first()
    if not w:
        return jsonify({"error": "Widget not found"}), 404

    data = request.get_json()
    if not data or "is_active" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    w.is_act = bool(data["is_active"])
    _safe_commit()

    return jsonify({"success": True, "is_active": w.is_act})


@bp.route("/export", methods=["GET"])
@login_required
def export_summary():
    fmt = request.args.get("format", "txt")

    act_wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).order_by(WidgetConfig.poz).all()

    tekst = sobr_summary_t(act_wid_lst)

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
