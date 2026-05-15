from app import create_app
from flask import url_for
from app.services.game_news import igry_nov

app = create_app()
with app.app_context():
    print(igry_nov())
