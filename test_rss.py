import feedparser
u = "https://stopgame.ru/rss/rss_news.xml"
try:
    f = feedparser.parse(u)
    print("Entries:", len(f.entries))
    if len(f.entries) > 0:
        print("First title:", f.entries[0].title)
except Exception as e:
    print("Error:", e)
