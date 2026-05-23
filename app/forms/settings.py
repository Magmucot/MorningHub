from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import SubmitField


class SettingsForm(FlaskForm):
    back_img = FileField(
        "Фоновое изображение", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Только изображения (включая GIF)!")]
    )
    submit = SubmitField("Сохранить настройки")
