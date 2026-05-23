import os
import uuid
from typing import Optional
from werkzeug.datastructures import FileStorage
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def _allow_f(f_name: str, mimetype: str) -> bool:
    if mimetype not in ALLOWED_MIME_TYPES:
        return False
    return "." in f_name and f_name.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_back_img(f: FileStorage) -> Optional[str]:
    """Saves the file safely with UUID4 filename and returns it."""
    if not f or not f.filename:
        return None

    if not f.mimetype or not _allow_f(f.filename, f.mimetype):
        raise ValueError("Недопустимый тип файла или расширение.")

    ext = f.filename.rsplit(".", 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"

    f_dir = current_app.config.get("UPLOAD_FOLDER")
    if not f_dir:
        raise RuntimeError("UPLOAD_FOLDER не настроен.")

    f_path = os.path.join(f_dir, new_name)

    f.save(f_path)
    return new_name
