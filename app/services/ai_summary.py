import asyncio
import os
from itertools import chain
from typing import Any, Dict

from asyncache import cached
from cachetools import TTLCache, keys
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError

from app.models.user import User
from app.services.ai_models import get_ai_models_news
from app.services.game_news import get_game_news
from app.services.it_news import get_it_news
from app.services.politics import get_polit_news

load_dotenv()


def _user_cache_key(user: User, *args: Any, **kwargs: Any) -> tuple:
    """
    Генерирует ключ кэша по ID пользователя.
    Защищает от промахов кэша, если ORM-модель User мутирует в памяти.
    """
    user_id = getattr(user, "id", id(user))
    return keys.hashkey(user_id)


@cached(cache=TTLCache(maxsize=128, ttl=7200), key=_user_cache_key)
async def get_ai_summary(user: User) -> Dict[str, Any]:
    api_key: str | None = user.ai_key or os.environ.get("OPENAI_API_KEY")
    base_url: str | None = user.ai_url or os.environ.get("OPENAI_BASE_URL")

    if not api_key:
        return {"error": "API-ключ не настроен. Добавьте его в Настройки или в .env файл."}

    news_tasks = [
        asyncio.to_thread(get_it_news, limit=5),
        asyncio.to_thread(get_polit_news, limit=5),
        asyncio.to_thread(get_ai_models_news, limit=5),
        asyncio.to_thread(get_game_news, limit=5),
    ]

    news_results = await asyncio.gather(*news_tasks)

    all_titles: list[str] = [
        item["title"]
        for item in chain.from_iterable(news_results)
        if isinstance(item, dict) and "title" in item and "error" not in item
    ]

    if not all_titles:
        return {"error": "Нет новостей для генерации сводки."}

    prompt: str = (
        "Сделай емкую и структурированную выжимку главных событий из следующих заголовков новостей. "
        "Пиши живо и интересно. Используй Markdown (жирный шрифт, списки), чтобы выделить самое важное "
        "и разделить по категориям:\n\n"
        f"{chr(10).join(all_titles)}"
    )

    model_name: str = user.ai_model or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

    client_kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    try:
        client = AsyncOpenAI(**client_kwargs)

        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Ты — умный и лаконичный помощник, составляющий утреннюю сводку."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        if not response.choices:
            return {"error": "Пустой ответ от AI-модели."}

        return {"summary": response.choices[0].message.content}

    except OpenAIError as err:
        return {"error": f"Сбой API OpenAI: {err}"}
    except Exception as err:
        return {"error": f"Внутренняя ошибка генератора сводки: {err}"}
