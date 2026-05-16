import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache, cached
from typing import List, Dict, Any


def fetch_from_playground(lim: int) -> List[Dict[str, Any]]:
    url = "https://www.playground.ru/news"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    n_lst: List[Dict[str, Any]] = []

    # Парсим заголовки и ссылки
    articles = soup.find_all("div", class_="post-title")
    for a in articles:
        if len(n_lst) >= lim:
            break
        link_tag = a.find("a")
        if link_tag:
            title = link_tag.text.strip()
            link = link_tag["href"]
            n_lst.append({"title": title, "link": link})

    return n_lst

def fetch_from_ixbt(lim: int) -> List[Dict[str, Any]]:
    import feedparser
    url = "https://ixbt.games/export/rss.xml"
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", 0) and not feed.entries:
        raise ValueError("Failed to parse iXBT RSS")
        
    n_lst = []
    for entry in feed.entries[:lim]:
        n_lst.append({"title": entry.title, "link": entry.link})
    return n_lst


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_game_news(lim: int = 5) -> List[Dict[str, Any]]:
    try:
        return fetch_from_playground(lim)
    except Exception as e1:
        try:
            return fetch_from_ixbt(lim)
        except Exception as e2:
            return [{"error": f"Playground: {str(e1)} | iXBT: {str(e2)}"}]
