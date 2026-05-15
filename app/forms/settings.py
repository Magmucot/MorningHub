from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SubmitField


class SettingsForm(FlaskForm):
    fon_img = FileField(
        "Фоновое изображение", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Только изображения!")]
    )
    submit = SubmitField("Сохранить настройки")
