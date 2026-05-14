from app.services.currency import poluch_valuta_kurs
from app.services.it_news import it_novosti
from app.services.politics import polit_novosti
from app.services.uploader import sohr_fon_img
from app.services.aggregator import sobr_utro_svodka_tekst
from app.services.ai_models import poluch_ai_mod_novosti
from app.services.ai_summary import poluch_ai_svodka
from app.services.weather import pog_prognoz
from app.services.crypto import poluch_kripta_kurs

__all__ = [
    "poluch_valuta_kurs",
    "it_novosti",
    "polit_novosti",
    "sohr_fon_img",
    "sobr_utro_svodka_tekst",
    "poluch_ai_mod_novosti",
    "poluch_ai_svodka",
    "pog_prognoz",
    "poluch_kripta_kurs",
]
