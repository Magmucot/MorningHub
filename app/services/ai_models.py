import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache, cached
from typing import List, Dict, Any


@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_ai_models_news(lim: int = 5) -> List[Dict[str, Any]]:
    url = "https://artificialanalysis.ai/changelog"
    try:
        req = requests.get(url, timeout=10)
        req.raise_for_status()

        s = BeautifulSoup(req.text, "html.parser")
        n_lst: List[Dict[str, Any]] = []

        art_lst = s.find_all("h3")

        for art in art_lst:
            if len(n_lst) >= lim:
                break

            title = art.get_text(strip=True)

            l_tag = art.find("a")
            if not l_tag:
                l_tag = art.find_parent("a")

            url = "https://artificialanalysis.ai"
            if l_tag and l_tag.get("href"):
                href = l_tag.get("href")
                url = href if href.startswith("http") else f"https://artificialanalysis.ai{href}"
            else:
                url = "https://artificialanalysis.ai/changelog"

            n_lst.append({"title": title, "link": url})

        return n_lst
    except Exception as e:
        return [{"error": str(e)}]
