from app import create_app
from app.services.game_news import get_game_news

app = create_app()
with app.app_context():
    print(get_game_news())
