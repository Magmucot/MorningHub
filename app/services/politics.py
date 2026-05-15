import feedparser
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_polit_news(lim: int = 5) -> List[Dict[str, Any]]:
    url = "https://lenta.ru/rss/news"
    try:
        f = feedparser.parse(url)
        n_lst: List[Dict[str, Any]] = []
        for e in f.entries[:lim]:
            n_lst.append({"title": e.title, "link": e.link, "published": getattr(e, "published", "")})
        return n_lst
    except Exception as e:
        return [{"error": str(e)}]
