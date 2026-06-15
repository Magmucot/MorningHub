import asyncio
from urllib.parse import urlparse
from flask import Blueprint, Response, jsonify, request
from flask_login import login_required, current_user
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.widget import WidgetConfig
from app.models.bookmark import Bookmark
from app.services.aggregator import build_sum_t
from app.services.currency import get_val_rates
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_models_news
from app.services.openrouter_news import get_openrouter_news
from app.services.ai_summary import get_ai_sum
from app.services.weather import pog_fc
from app.services.crypto import get_crypto_rates
from app.services.game_news import get_game_news

logger = logging.getLogger(__name__)


def _safe_commit() -> bool:
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as err:
        db.session.rollback()
        logger.error("Ошибка транзакции БД: %s", err)
        return False


def _is_url(u_str: str) -> bool:
    try:
        p = urlparse(u_str)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


bp = Blueprint("api", __name__, url_prefix="/api/v1")


@bp.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


@bp.route("/widgets/crypto", methods=["GET"])
@login_required
def api_crypto():
    return jsonify(get_crypto_rates(current_user.crypto_lst))


@bp.route("/widgets/weather", methods=["GET"])
@login_required
def api_weather():
    res = pog_fc(current_user)
    if _safe_commit():
        return jsonify(res)
    return jsonify({"error": "DB error"}), 500


@bp.route("/bookmarks", methods=["GET", "POST"])
@login_required
def api_bookmarks():
    if request.method == "POST":
        data = request.get_json()
        if not data or not data.get("url") or not data.get("title"):
            return jsonify({"error": "Требуется title и url"}), 400

        u_str = data["url"].strip()
        if not _is_url(u_str):
            return jsonify({"error": "Неверный формат URL. Требуется http:// или https://"}), 400

        bm = Bookmark(usr_id=current_user.id, title=data["title"].strip(), url=u_str, icon=data.get("icon", "fa-link"))
        db.session.add(bm)
        if _safe_commit():
            return jsonify({"success": True, "id": bm.id})
        return jsonify({"error": "DB error"}), 500
    bm_lst = Bookmark.query.filter_by(usr_id=current_user.id).all()
    return jsonify([{"id": bm.id, "title": bm.title, "url": bm.url, "icon": bm.icon} for bm in bm_lst])


@bp.route("/bookmarks/<int:bm_id>", methods=["DELETE"])
@login_required
def api_delete_bookmark(bm_id):
    bm = Bookmark.query.filter_by(id=bm_id, usr_id=current_user.id).first()
    if not bm:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(bm)
    if _safe_commit():
        return jsonify({"success": True})
    return jsonify({"error": "DB error"}), 500


def _int_range(value, default, min_v, max_v):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_v, min(max_v, value))


@bp.route("/widgets/save-grid", methods=["PATCH"])
@login_required
def save_grid_widgets():
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id).all()
    wid_karta = {w.w_tip: w for w in wid_lst}

    col_limit = 120 if current_user.is_fr else 12
    y_limit = 1000 if current_user.is_fr else 100
    h_limit = 200 if current_user.is_fr else 20

    for i in data["items"]:
        tip = i.get("widget_type")
        if tip in wid_karta:
            w = wid_karta[tip]
            w.x = _int_range(i.get("x"), w.x, 0, col_limit - 1)
            w.y = _int_range(i.get("y"), w.y, 0, y_limit)
            w.w = _int_range(i.get("w"), w.w, 1, col_limit)
            w.h = _int_range(i.get("h"), w.h, 1, h_limit)

    if _safe_commit():
        return jsonify({"success": True})
    return jsonify({"error": "DB error"}), 500


@bp.route("/widgets/ai-summary", methods=["GET"])
@login_required
def api_ai_summary():
    result = asyncio.run(get_ai_sum(current_user))
    return jsonify(result)


@bp.route("/user/lock-grid", methods=["PATCH"])
@login_required
def lock_grid():
    data = request.get_json()
    if not data or "is_grid_locked" not in data:
        return jsonify({"error": "Invalid payload"}), 400

    is_lock = data.get("is_grid_locked")
    if not isinstance(is_lock, bool):
        return jsonify({"error": "is_grid_locked должен быть типа boolean"}), 400

    current_user.grid_lock = is_lock
    if _safe_commit():
        return jsonify({"success": True, "is_grid_locked": current_user.grid_lock})
    return jsonify({"error": "DB error"}), 500


@bp.route("/widgets/ai-models", methods=["GET"])
@login_required
def api_ai_models():
    src = getattr(current_user, 'ai_models_src', 'both')
    items = []
    if src in ('artificial', 'both'):
        aa = get_ai_models_news()
        for i in aa:
            i.setdefault('source', 'artificial')
        items.extend(aa)
    if src in ('openrouter', 'both'):
        items.extend(get_openrouter_news())
    return jsonify(items)


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
    return jsonify(get_val_rates(current_user.val_lst))


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
    is_act = data.get("is_active")
    if not isinstance(is_act, bool):
        return jsonify({"error": "Invalid boolean"}), 400
    w.is_act = is_act
    if _safe_commit():
        return jsonify({"success": True, "is_active": w.is_act})
    return jsonify({"error": "DB error"}), 500


@bp.route("/export", methods=["GET"])
@login_required
def export_summary():
    fmt = request.args.get("format", "txt")

    act_wid_lst = WidgetConfig.query.filter_by(usr_id=current_user.id, is_act=True).order_by(WidgetConfig.poz).all()

    tekst = build_sum_t(act_wid_lst)

    if fmt == "txt":
        return Response(
            tekst,
            mimetype="text/plain",
            headers={"Content-disposition": "attachment; filename=morning_summary.txt"},
        )
    elif fmt == "csv":
        import csv
        from io import StringIO
        buf = StringIO()
        wr = csv.writer(buf)
        for line in tekst.splitlines():
            wr.writerow([line])
        return Response(
            buf.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-disposition": "attachment; filename=morning_summary.csv"},
        )
    else:
        return jsonify({"error": "Unsupported format"}), 400
