import requests
from cachetools import TTLCache, cached
from typing import Dict, Any


KNOWN_CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "the-open-network": "TON",
    "solana": "SOL",
    "binancecoin": "BNB",
    "ripple": "XRP",
    "dogecoin": "DOGE",
    "cardano": "ADA",
    "tron": "TRX",
    "polkadot": "DOT",
    "litecoin": "LTC"
}

# Кэш на 10 минут (600 секунд)
@cached(cache=TTLCache(maxsize=100, ttl=600))
def poluch_kripta_kurs(kripta_spis_str: str) -> Dict[str, Any]:
    k_spis = [c.strip().lower() for c in kripta_spis_str.split(',') if c.strip()]
    if not k_spis:
        return {}
    
    id_spis = ",".join(k_spis)
    
    u = "https://api.coingecko.com/api/v3/simple/price"
    p = {"ids": id_spis, "vs_currencies": "usd", "include_24hr_change": "true"}
    try:
        r = requests.get(u, params=p, timeout=5)
        r.raise_for_status()
        d = r.json()

        rez = {}
        for cid in k_spis:
            info = d.get(cid)
            if info:
                sym = KNOWN_CRYPTOS.get(cid, cid.upper()[:4])
                rez[sym] = {
                    "price": round(info.get("usd", 0), 2),
                    "change": round(info.get("usd_24h_change", 0), 2),
                }
        return rez
    except requests.RequestException as e:
        return {"error": str(e)}
