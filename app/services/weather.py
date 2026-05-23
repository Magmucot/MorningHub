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

    off = payload.get("utc_offset_seconds", 0)
    u_now = datetime.datetime.now(datetime.timezone.utc)
    l_now = u_now + datetime.timedelta(seconds=off)
    t_iso = l_now.strftime("%Y-%m-%dT%H:00")

    times = hourly["time"]
    start = 0
    for idx, val in enumerate(times):
        if val >= t_iso:
            start = idx
            break

    hr_times = [t.split("T")[1] for t in times[start : start + 12]]
    hr_temps = hourly["temperature_2m"][start : start + 12]

    return {
        "date": daily["time"][0],
        "description": WEATHER_CODES.get(weath_kod, "❓ Неизвестно"),
        "temp_max": daily["temperature_2m_max"][0],
        "temp_min": daily["temperature_2m_min"][0],
        "precipitation_probability": daily["precipitation_probability_max"][0],
        "hourly_times": hr_times,
        "hourly_temps": hr_temps,
    }


@cached(cache=TTLCache(maxsize=128, ttl=3600))
def _fetch_from_wttr(city: str) -> Dict[str, Any]:
    url = f"https://wttr.in/{city}?format=j1&lang=ru"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    d = r.json()
    
    curr = d["current_condition"][0]
    today = d["weather"][0]
    
    desc_list = curr.get("lang_ru")
    if desc_list:
        desc = desc_list[0]["value"]
    else:
        desc = curr["weatherDesc"][0]["value"]
        
    temp_max = today["maxtempC"]
    temp_min = today["mintempC"]
    
    # Try to find max precip probability from chances
    max_precip = max((int(h.get("chanceofrain", 0)) for h in today.get("hourly", [])), default=0)

    hr_times = []
    hr_temps = []
    for item in today.get("hourly", []):
        t_val = int(item["time"]) // 100
        hr_times.append(f"{t_val:02d}:00")
        hr_temps.append(float(item["tempC"]))

    return {
        "date": today["date"],
        "description": f"🌈 {desc}",
        "temp_max": float(temp_max),
        "temp_min": float(temp_min),
        "precipitation_probability": max_precip,
        "hourly_times": hr_times,
        "hourly_temps": hr_temps,
        "city": city,
    }


def pog_fc(usr: User) -> Dict[str, Any]:
    """Получает прогноз для пользователя, разрешая город через геокодинг, если нужно."""
    try:
        lat = usr.weath_lat
        lon = usr.weath_lon
        g_name = usr.pog_city

        if lat is None or lon is None:
            try:
                lat, lon, g_name = _get_city_geo(usr.pog_city)
                usr.weath_lat = lat
                usr.weath_lon = lon
                usr.pog_city = g_name
            except requests.RequestException as geo_err:
                try:
                    return _fetch_from_wttr(usr.pog_city)
                except Exception as wttr_err:
                    return {"error": f"Open-Meteo Geo: {str(geo_err)} | wttr.in: {str(wttr_err)}"}

        try:
            d = _get_weath(lat, lon)
            d["city"] = g_name
            return d
        except requests.RequestException as e1:
            try:
                return _fetch_from_wttr(g_name)
            except Exception as e2:
                return {"error": f"Open-Meteo: {str(e1)} | wttr.in: {str(e2)}"}
    except Exception as e:
        return {"error": str(e)}
