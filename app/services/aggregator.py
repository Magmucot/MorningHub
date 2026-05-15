from typing import List
from app.models.widget import WidgetConfig
from app.services.currency import get_val_kurs
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_mod_news
from app.services.ai_summary import get_ai_summary
from app.services.game_news import game_news


def sobr_summary_t(akt_wid_spis: List[WidgetConfig]) -> str:
    summary: List[str] = ["=== Утренняя Сводка MorningHub ===\n"]

    for w in akt_wid_spis:
        if w.w_tip == "ai_summary":
            summary.append("\n--- ИИ-Пересказ Новостей ---")
            rez = get_ai_summary(w.user)
            if "error" in rez:
                summary.append(f"Ошибка: {rez['error']}")
            else:
                summary.append(rez.get("summary", ""))

        elif w.w_tip == "currency":
            summary.append("\n--- Курсы Валют ---")
            kurs_d = get_val_kurs(w.user.val_spis)
            if "error" in kurs_d:
                summary.append(f"Ошибка загрузки: {kurs_d['error']}")
            else:
                for k, v in kurs_d.items():
                    if k != "date":
                        summary.append(f"{k}: {v['current']} руб.")
                summary.append(f"Дата: {kurs_d.get('date')}")

        elif w.w_tip == "it_news":
            summary.append("\n--- IT Новости (Habr, OpenNET) ---")
            news_spis = get_it_news(lim=5)
            for n in news_spis:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "game_news":
            summary.append("\n--- Игровые Новости (Playground.ru) ---")
            news_spis = game_news(lim=5)
            for n in news_spis:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "ai_models":
            summary.append("\n--- AI Модели (Artificial Analysis) ---")
            news_spis = get_ai_mod_news(lim=5)
            for n in news_spis:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "politics":
            summary.append("\n--- Политика (Lenta.ru) ---")
            news_spis = get_polit_news(lim=5)
            for n in news_spis:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

    summary.append("\n==================================")
    return "\n".join(summary)
