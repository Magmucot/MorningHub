import requests
import feedparser

u = "https://stopgame.ru/rss/rss_news.xml"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = requests.get(u, headers=headers, timeout=10)
feed = feedparser.parse(response.content)
print(len(feed.entries))
