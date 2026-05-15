from typing import List
from app.models.widget import WidgetConfig
from app.services.currency import poluch_val_kurs
from app.services.it_news import it_nov
from app.services.politics import polit_nov
from app.services.ai_models import poluch_ai_mod_nov
from app.services.ai_summary import poluch_ai_svod


def sobr_svod_t(akt_wid_spis: List[WidgetConfig]) -> str:
    svod: List[str] = ["=== Утренняя Сводка MorningHub ===\n"]

    for w in akt_wid_spis:
        if w.w_tip == "ai_summary":
            svod.append("\n--- ИИ-Пересказ Новостей ---")
            rez = poluch_ai_svod(w.user)
            if "error" in rez:
                svod.append(f"Ошибка: {rez['error']}")
            else:
                svod.append(rez.get("summary", ""))

        elif w.w_tip == "currency":
            svod.append("\n--- Курсы Валют ---")
            kurs_d = poluch_val_kurs(w.user.val_spis)
            if "error" in kurs_d:
                svod.append(f"Ошибка загрузки: {kurs_d['error']}")
            else:
                for k, v in kurs_d.items():
                    if k != "date":
                        svod.append(f"{k}: {v['current']} руб.")
                svod.append(f"Дата: {kurs_d.get('date')}")

        elif w.w_tip == "it_news":
            svod.append("\n--- IT Новости (Habr, OpenNET) ---")
            nov_spis = it_nov(lim=5)
            for n in nov_spis:
                if "error" in n:
                    svod.append(f"Ошибка: {n['error']}")
                    break
                svod.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "ai_models":
            svod.append("\n--- AI Модели (Artificial Analysis) ---")
            nov_spis = poluch_ai_mod_nov(lim=5)
            for n in nov_spis:
                if "error" in n:
                    svod.append(f"Ошибка: {n['error']}")
                    break
                svod.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "politics":
            svod.append("\n--- Политика (Lenta.ru) ---")
            nov_spis = polit_nov(lim=5)
            for n in nov_spis:
                if "error" in n:
                    svod.append(f"Ошибка: {n['error']}")
                    break
                svod.append(f"- {n.get('title')}\n  {n.get('link')}")

    svod.append("\n==================================")
    return "\n".join(svod)
