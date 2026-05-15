import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache, cached
from typing import List, Dict, Any


# Кэш на 30 минут (1800 секунд)
@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_game_news(lim: int = 5) -> List[Dict[str, Any]]:
    url = "https://www.playground.ru/news"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
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
    except Exception as e:
        return [{"error": str(e)}]
