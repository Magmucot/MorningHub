from app.services.currency import poluch_val_kurs
from app.services.it_news import it_nov
from app.services.politics import polit_nov
from app.services.uploader import sohr_fon_img
from app.services.aggregator import sobr_svod_t
from app.services.ai_models import poluch_ai_mod_nov
from app.services.ai_summary import poluch_ai_svod
from app.services.weather import pog_prog
from app.services.crypto import poluch_crypto_kurs
from app.services.game_news import igry_nov

__all__ = [
    "poluch_val_kurs",
    "it_nov",
    "polit_nov",
    "sohr_fon_img",
    "sobr_svod_t",
    "poluch_ai_mod_nov",
    "poluch_ai_svod",
    "pog_prog",
    "poluch_crypto_kurs",
    "igry_nov",
]
