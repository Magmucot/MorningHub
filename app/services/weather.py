from typing import Any, Dict, Tuple
import requests
from flask import current_app
from cachetools import TTLCache, cached
from app.models.user import User

WEATHER_CODES = {
    0: "☀️ Ясно",
    1: "🌤 Преимущественно ясно",
    2: "⛅ Переменная облачность",
    3: "☁️ Пасмурно",
    45: "🌫 Туман",
    48: "🌫 Туман (с инеем)",
    51: "🌧 Мелкая морось",
    53: "🌧 Морось",
    55: "🌧 Сильная морось",
    61: "🌧 Небольшой дождь",
    63: "🌧 Дождь",
    65: "🌧 Сильный дождь",
    71: "❄️ Небольшой снег",
    73: "❄️ Снег",
    75: "❄️ Сильный снег",
    80: "🌦 Ливни",
    81: "🌧 Сильные ливни",
    82: "⛈ Очень сильные ливни",
    95: "🌩 Гроза",
    96: "🌩 Гроза с небольшим градом",
    99: "🌩 Гроза с сильным градом",
}


def _get_city_geo(city: str) -> Tuple[float, float, str]:
    geo_u = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(
        geo_u,
        params={"name": city, "count": 1, "language": "ru", "format": "json"},
        timeout=5,
    )
    r.raise_for_status()
    d = r.json()
    res_lst = d.get("results") or []
    if not res_lst:
        raise ValueError(f"Город не найден: {city}")
    perv = res_lst[0]
    return perv["latitude"], perv["longitude"], perv["name"]


# Кеш на 1 час
@cached(cache=TTLCache(maxsize=128, ttl=3600))
def _get_weath(lat: float, lon: float) -> Dict[str, Any]:
    weath_u = "https://api.open-meteo.com/v1/forecast"
    r = requests.get(
        weath_u,
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "hourly": "temperature_2m",
            "timezone": "auto",
            "forecast_days": 2,
        },
        timeout=5,
    )
    r.raise_for_status()
    payload = r.json()
    daily = payload["daily"]
    hourly = payload["hourly"]
    weath_kod = daily["weathercode"][0]

    import datetime

    curr_h = datetime.datetime.now().hour
    # Open-Meteo возвращает 48 часов, т.к forecast_days=2
    chas_vremya = [t.split("T")[1] for t in hourly["time"][curr_h : curr_h + 12]]
    chas_temp = hourly["temperature_2m"][curr_h : curr_h + 12]

    return {
        "date": daily["time"][0],
        "description": WEATHER_CODES.get(weath_kod, "❓ Неизвестно"),
        "temp_max": daily["temperature_2m_max"][0],
        "temp_min": daily["temperature_2m_min"][0],
        "precipitation_probability": daily["precipitation_probability_max"][0],
        "hourly_times": chas_vremya,
        "hourly_temps": chas_temp,
    }


def weath_prog(usr: User) -> Dict[str, Any]:
    """Получает прогноз для пользователя, разрешая город через геокодинг, если нужно."""
    try:
        lat = usr.weath_lat
        lon = usr.weath_lon
        g_name = usr.weath_city

        if lat is None or lon is None:
            lat, lon, g_name = _get_city_geo(usr.weath_city)
            usr.weath_lat = lat
            usr.weath_lon = lon
            usr.weath_city = g_name
            # Мы не коммитим здесь (это лучше сделать в роуте или вызывающем слое),
            # но обновляем объект.

        d = _get_weath(lat, lon)
        d["city"] = g_name
        return d
    except Exception as e:
        return {"error": str(e)}
