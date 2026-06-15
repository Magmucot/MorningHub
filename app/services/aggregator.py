from typing import List
import asyncio
from app.models.widget import WidgetConfig
from app.services.currency import get_val_rates
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_models_news
from app.services.openrouter_news import get_openrouter_news
from app.services.ai_summary import get_ai_sum
from app.services.game_news import get_game_news


def build_sum_t(act_wid_lst: List[WidgetConfig]) -> str:
    summary: List[str] = ["=== Утренняя Сводка MorningHub ===\n"]

    for w in act_wid_lst:
        if w.w_tip == "ai_summary":
            summary.append("\n--- ИИ-Пересказ Новостей ---")
            res = asyncio.run(get_ai_sum(w.user))
            if "error" in res:
                summary.append(f"Ошибка: {res['error']}")
            else:
                summary.append(res.get("summary", ""))

        elif w.w_tip == "currency":
            summary.append("\n--- Курсы Валют ---")
            rate_d = get_val_rates(w.user.val_lst)
            if "error" in rate_d:
                summary.append(f"Ошибка загрузки: {rate_d['error']}")
            else:
                for k, v in rate_d.items():
                    if k != "date":
                        summary.append(f"{k}: {v['current']} руб.")
                summary.append(f"Дата: {rate_d.get('date')}")

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
            usr = w.user
            src = getattr(usr, 'ai_models_src', 'both')
            items = []
            if src in ('artificial', 'both'):
                aa = get_ai_models_news(lim=5)
                for n in aa:
                    n.setdefault('source', 'artificial')
                items.extend(aa)
            if src in ('openrouter', 'both'):
                items.extend(get_openrouter_news(lim=5))

            if src == 'artificial':
                summary.append("\n--- AI Модели (Artificial Analysis) ---")
            elif src == 'openrouter':
                summary.append("\n--- AI Модели (OpenRouter) ---")
            else:
                summary.append("\n--- AI Модели (Artificial Analysis + OpenRouter) ---")

            for n in items:
                if "error" in n:
                    summary.append(f"Ошибка: {n['error']}")
                    break
                src_lbl = "[OpenRouter]" if n.get('source') == 'openrouter' else "[AA]"
                title = n.get('title', '')
                link = n.get('link', '')
                extra = ""
                if n.get('price'):
                    extra += f" | {n['price']}"
                if n.get('ctx'):
                    extra += f" | ctx {n['ctx']}"
                summary.append(f"- {src_lbl} {title}{extra}\n  {link}")

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
