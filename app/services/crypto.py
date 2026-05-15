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
    "litecoin": "LTC",
    "notcoin": "NOT",
}

IPUT_NAMES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "ton": "the-open-network",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "doge": "dogecoin",
    "ada": "cardano",
    "trx": "tron",
    "dot": "polkadot",
    "ltc": "litecoin",
    "not": "notcoin",
}


@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_crypto_kurs(crypto_lst_str: str) -> Dict[str, Any]:
    c_lst = [c.strip().lower() for c in crypto_lst_str.split(",") if c.strip()]
    if not c_lst:
        return {}

    id_lst = ",".join(c_lst)

    url = "https://api.coingecko.com/api/v3/simple/price"
    p = {"ids": id_lst, "vs_currencies": "usd", "include_24hr_change": "true"}
    try:
        r = requests.get(url, params=p, timeout=5)
        r.raise_for_status()
        d = r.json()

        res = {}
        for cid in c_lst:
            info = d.get(cid)
            if info:
                sym = KNOWN_CRYPTOS.get(cid, cid.upper()[:4])
                res[sym] = {
                    "price": round(info.get("usd", 0), 4),
                    "change": round(info.get("usd_24h_change", 0), 4),
                }
        return res
    except requests.RequestException as e:
        return {"error": str(e)}
