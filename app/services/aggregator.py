from typing import List
from app.models.widget import WidgetConfig
from app.services.currency import get_val_kurs
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_models_news
from app.services.ai_summary import get_ai_summary
from app.services.game_news import get_game_news


def sobr_summary_t(act_wid_lst: List[WidgetConfig]) -> str:
    summary: List[str] = ["=== Утренняя Сводка MorningHub ===\n"]

    for w in act_wid_lst:
        if w.w_tip == "ai_summary":
            summary.append("\n--- ИИ-Пересказ Новостей ---")
            res = get_ai_summary(w.user)
            if "error" in res:
                summary.append(f"Ошибка: {res['error']}")
            else:
                summary.append(res.get("summary", ""))

        elif w.w_tip == "currency":
            summary.append("\n--- Курсы Валют ---")
            kurs_d = get_val_kurs(w.user.val_lst)
            if "error" in kurs_d:
                summary.append(f"Ошибка загрузки: {kurs_d['error']}")
            else:
                for k, v in kurs_d.items():
                    if k != "date":
                        summary.append(f"{k}: {v['current']} руб.")
                summary.append(f"Дата: {kurs_d.get('date')}")

        elif w.w_tip == "it_news":
            summary.append("\n--- IT Новости (Habr, OpenNET) ---")
            news_lst = get_it_news(lim=5)
            for n in news_lst:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "game_news":
            summary.append("\n--- Игровые Новости (Playground.ru) ---")
            news_lst = get_game_news(lim=5)
            for n in news_lst:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "ai_models":
            summary.append("\n--- AI Модели (Artificial Analysis) ---")
            news_lst = get_ai_models_news(lim=5)
            for n in news_lst:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

        elif w.w_tip == "politics":
            summary.append("\n--- Политика (Lenta.ru) ---")
            news_lst = get_polit_news(lim=5)
            for n in news_lst:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                summary.append(f"- {n.get('title')}\n  {n.get('link')}")

    summary.append("\n==================================")
    return "\n".join(summary)
