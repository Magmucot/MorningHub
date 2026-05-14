import requests
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
}


def get_crypto_rates(crypto_tracking_str: str) -> Dict[str, Any]:
    crypto_list = [c.strip().lower() for c in crypto_tracking_str.split(",") if c.strip()]
    if not crypto_list:
        return {}

    clean_ids = ",".join(crypto_list)

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": clean_ids, "vs_currencies": "usd", "include_24hr_change": "true"}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        result = {}
        for cid in crypto_list:
            info = data.get(cid)
            if info:
                symbol = KNOWN_CRYPTOS.get(cid, cid.upper()[:4])
                result[symbol] = {
                    "price": round(info.get("usd", 0), 2),
                    "change": round(info.get("usd_24h_change", 0), 2),
                }
        return result
    except requests.RequestException as e:
        return {"error": str(e)}


print(get_crypto_rates("bitcoin,ethereum"))
