import os
from openai import OpenAI
from cachetools import TTLCache, cached
from typing import Dict, Any
from dotenv import load_dotenv
from app.services.it_news import it_nov
from app.services.politics import polit_nov
from app.services.ai_models import poluch_ai_mod_nov

from app.models.user import User

load_dotenv()

@cached(cache=TTLCache(maxsize=128, ttl=7200))
def poluch_ai_svod(u: User) -> Dict[str, Any]:
    key = u.ai_key or os.environ.get("OPENAI_API_KEY")
    u_url = u.ai_url or os.environ.get("OPENAI_BASE_URL")  # Например: http://localhost:11434/v1 для Ollama
    if not key:
        return {"error": "API-ключ не настроен. Добавьте его в Настройках или в .env файл."}

    # Собираем все новости
    it_nov_spis = it_nov(lim=5)
    polit_nov_spis = polit_nov(lim=5)
    ai_mod_nov = poluch_ai_mod_nov(lim=5)

    vse_zagol = []

    for n_spis in [it_nov_spis, polit_nov_spis, ai_mod_nov]:
        for n in n_spis:
            if "title" in n and "error" not in n:
                vse_zagol.append(n["title"])

    if not vse_zagol:
        return {"error": "Нет новостей для генерации сводки."}

    promt = (
        "Сделай емкую и структурированную выжимку главных событий из следующих заголовков новостей. "
        "Пиши живо и интересно. Используй Markdown (жирный шрифт, списки), чтобы выделить самое важное и разделить по категориям:\n\n"
        + "\n".join(vse_zagol)
    )

    try:
        kl_kwargs = {"api_key": key}
        if u_url:
            kl_kwargs["base_url"] = u_url

        kl = OpenAI(**kl_kwargs)

        # Модель пользователя, иначе из ENV, иначе по умолчанию
        mod_name = u.ai_mod or os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

        otvet = kl.chat.completions.create(
            model=mod_name,
            messages=[
                {"role": "system", "content": "Ты — умный и лаконичный помощник, составляющий утреннюю сводку."},
                {"role": "user", "content": promt},
            ],
            temperature=0.7,
        )

        svod_t = otvet.choices[0].message.content
        return {"summary": svod_t}
    except Exception as e:
        return {"error": f"Ошибка генерации сводки: {str(e)}"}
