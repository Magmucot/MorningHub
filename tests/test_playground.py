import requests
from bs4 import BeautifulSoup

url = "https://www.playground.ru/news"
headers = {"User-Agent": "Mozilla/5.0"}
try:
    r = requests.get(url, headers=headers, timeout=10)
    print("Status:", r.status_code)
    soup = BeautifulSoup(r.text, "html.parser")
    articles = soup.find_all("div", class_="post-title")
    for a in articles[:3]:
        link = a.find("a")
        print(link.text.strip(), link["href"])
except Exception as e:
    print("Error:", e)
