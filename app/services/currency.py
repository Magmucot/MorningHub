import requests
from cachetools import TTLCache, cached
from typing import Dict, Any


# Кэш на 1 час (3600 секунд)
@cached(cache=TTLCache(maxsize=100, ttl=3600))
def get_val_rates(val_lst_str: str) -> Dict[str, Any]:
    v_lst = [c.strip().upper() for c in val_lst_str.split(",") if c.strip()]
    if not v_lst:
        return {}

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        d = r.json()

        v_d = d.get("Valute", {})

        def get_v(kod):
            v = v_d.get(kod, {})
            if not v:
                return None
            # Если номинал больше 1, делим, чтобы получить цену за 1 единицу
            nom = v.get("Nominal", 1)
            tek = v.get("Value", 0.0) / nom if nom else 0.0
            pre = v.get("Previous", 0.0) / nom if nom else 0.0
            return {"current": round(tek, 2), "previous": round(pre, 2)}

        res = {}
        for c in v_lst:
            v_info = get_v(c)
            if v_info:
                res[c] = v_info

        res["date"] = d.get("Date", "")
        return res
    except requests.RequestException as e:
        return {"error": str(e)}
