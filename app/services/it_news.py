import feedparser
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def it_novosti(lim: int = 5) -> List[Dict[str, Any]]:
    u_urls = [
        "https://habr.com/ru/rss/articles/",
        "https://www.opennet.ru/opennews/opennews_all_noadv.rss"
    ]
    novosti_spis: List[Dict[str, Any]] = []
    
    try:
        for u in u_urls:
            f = feedparser.parse(u)
            for e in f.entries[:lim]:
                novosti_spis.append({"title": e.title, "link": e.link, "published": getattr(e, "published", "")})
        
        # Sort by published date might be complex since formats differ, so just interleave or take first 'limit' of combined
        # But for now, let's just return limit items from Habr and limit items from OpenNET, total up to limit*2.
        # If user wants total 'limit' across both, we should just slice the whole list.
        return novosti_spis[:lim * 2] # return more since we have 2 sources, or slice to limit
    except Exception as e:
        return [{"error": str(e)}]
