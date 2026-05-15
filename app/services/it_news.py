import feedparser
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_it_news(lim: int = 5) -> List[Dict[str, Any]]:
    u_urls = ["https://habr.com/ru/rss/articles/", "https://www.opennet.ru/opennews/opennews_all_noadv.rss"]
    news_lst: List[Dict[str, Any]] = []

    try:
        for url in u_urls:
            f = feedparser.parse(url)
            for e in f.entries[:lim]:
                news_lst.append({"title": e.title, "link": e.link, "published": getattr(e, "published", "")})

        return news_lst[: lim * 2]
    except Exception as e:
        return [{"error": str(e)}]
