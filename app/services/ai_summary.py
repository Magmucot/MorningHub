import os
from openai import OpenAI
from cachetools import TTLCache, cached
from typing import Dict, Any
from dotenv import load_dotenv
from app.services.it_news import get_it_news
from app.services.game_news import get_game_news
from app.services.politics import get_polit_news
from app.services.ai_models import get_ai_models_news

from app.models.user import User

load_dotenv()


@cached(cache=TTLCache(maxsize=128, ttl=7200))
def get_ai_summary(user: User) -> Dict[str, Any]:
    api_key = user.ai_api_key or os.environ.get("OPENAI_API_KEY")
    base_url = user.ai_base_url or os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return {"error": "API-ключ не настроен. Добавьте его в Настройках или в .env файл."}

    it_news = get_it_news(limit=5)
    pol_news = get_polit_news(limit=5)
    ai_news = get_ai_models_news(limit=5)

    all_titles = []

    for news_list in [it_news, pol_news, ai_news]:
        for item in news_list:
            if "title" in item and "error" not in item:
                all_titles.append(item["title"])

    if not all_titles:
        return {"error": "Нет новостей для генерации сводки."}

    prompt = (
        "Сделай емкую и структурированную выжимку главных событий из следующих заголовков новостей. "
        "Пиши живо и интересно. Используй Markdown (жирный шрифт, списки), чтобы выделить самое важное и разделить по категориям:\n\n"
        + "\n".join(all_titles)
    )

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)

        # Модель пользователя, иначе из ENV, иначе по умолчанию
        model_name = user.ai_model or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Ты — умный и лаконичный помощник, составляющий утреннюю сводку."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        summary_text = response.choices[0].message.content
        return {"summary": summary_text}
    except Exception as e:
        return {"error": f"Ошибка генерации сводки: {str(e)}"}
