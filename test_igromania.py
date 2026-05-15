import feedparser
u = "https://www.igromania.ru/rss/all/"
try:
    f = feedparser.parse(u)
    print("Entries:", len(f.entries))
    if len(f.entries) > 0:
        print("First title:", f.entries[0].title)
except Exception as e:
    print("Error:", e)
