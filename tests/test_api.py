import requests

try:
    r = requests.post("http://127.0.0.1:5000/auth/login", data={"username": "admin", "password": "password"})
    cookie = r.headers.get("Set-Cookie")
    session = cookie.split(";")[0].split("=")[1] if cookie else ""
    print("Session:", session)
    r2 = requests.get("http://127.0.0.1:5000/api/v1/widgets/game-news", cookies={"session": session})
    print(r2.status_code)
    print(r2.text)
except Exception as e:
    print("Error:", e)
