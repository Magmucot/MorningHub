from app.services.currency import get_val_kurs
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.uploader import save_back_img
from app.services.aggregator import sobr_summary_t
from app.services.ai_models import get_ai_models_news
from app.services.ai_summary import get_ai_summary
from app.services.weather import weath_prog
from app.services.crypto import get_crypto_kurs
from app.services.game_news import get_game_news

__all__ = [
    "get_val_kurs",
    "get_it_news",
    "get_polit_news",
    "save_back_img",
    "sobr_summary_t",
    "get_ai_models_news",
    "get_ai_summary",
    "weath_prog",
    "get_crypto_kurs",
    "get_game_news",
]
