import feedparser
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_polit_news(lim: int = 5) -> List[Dict[str, Any]]:
    u = "https://lenta.ru/rss/news"
    try:
        f = feedparser.parse(u)
        n_spis: List[Dict[str, Any]] = []
        for e in f.entries[:lim]:
            n_spis.append({"title": e.title, "link": e.link, "published": getattr(e, "published", "")})
        return n_spis
    except Exception as e:
        return [{"error": str(e)}]
