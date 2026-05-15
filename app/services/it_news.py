import feedparser
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_it_news(lim: int = 5) -> List[Dict[str, Any]]:
    u_urls = ["https://habr.com/ru/rss/articles/", "https://www.opennet.ru/opennews/opennews_all_noadv.rss"]
    news_spis: List[Dict[str, Any]] = []

    try:
        for u in u_urls:
            f = feedparser.parse(u)
            for e in f.entries[:lim]:
                news_spis.append({"title": e.title, "link": e.link, "published": getattr(e, "published", "")})

        return news_spis[: lim * 2]
    except Exception as e:
        return [{"error": str(e)}]
