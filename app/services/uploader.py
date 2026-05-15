import os
import uuid
from typing import Optional
from werkzeug.datastructures import FileStorage
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _razresh_f(f_imya: str, mimetype: str) -> bool:
    if mimetype not in ALLOWED_MIME_TYPES:
        return False
    return "." in f_imya and f_imya.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_fon_img(f: FileStorage) -> Optional[str]:
    """Saves the file safely with UUID4 filename and returns it."""
    if not f or not f.filename:
        return None

    if not f.mimetype or not _razresh_f(f.filename, f.mimetype):
        raise ValueError("Недопустимый тип файла или расширение.")

    rassh = f.filename.rsplit(".", 1)[1].lower()
    news_imya = f"{uuid.uuid4().hex}.{rassh}"

    f_papka = current_app.config.get("UPLOAD_FOLDER")
    if not f_papka:
        raise RuntimeError("UPLOAD_FOLDER не настроен.")

    f_put = os.path.join(f_papka, news_imya)

    f.save(f_put)
    return news_imya
