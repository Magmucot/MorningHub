import requests
import json
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

INPUT_NAMES = {
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
    "bitcoin": "bitcoin",
    "ethereum": "ethereum",
    "the-open-network": "the-open-network",
    "solana": "solana",
    "binancecoin": "binancecoin",
    "ripple": "ripple",
    "dogecoin": "dogecoin",
    "cardano": "cardano",
    "tron": "tron",
    "polkadot": "polkadot",
    "litecoin": "litecoin",
    "notcoin": "notcoin",
}


def fetch_from_coingecko(c_lst: list[str]) -> Dict[str, Any]:
    id_lst = ",".join(c_lst)
    url = "https://api.coingecko.com/api/v3/simple/price"
    p = {"ids": id_lst, "vs_currencies": "usd", "include_24hr_change": "true"}
    
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


def fetch_from_binance(c_lst: list[str]) -> Dict[str, Any]:
    # Формируем список символов для Binance (например, BTCUSDT)
    symbols = []
    sym_map = {}
    
    for cid in c_lst:
        sym = KNOWN_CRYPTOS.get(cid, cid.upper()[:4])
        b_sym = f"{sym}USDT"
        symbols.append(b_sym)
        sym_map[b_sym] = sym
        
    url = "https://api.binance.com/api/v3/ticker/24hr"
    p = {"symbols": json.dumps(symbols).replace(" ", "")}
    
    r = requests.get(url, params=p, timeout=5)
    r.raise_for_status()
    d = r.json()
    
    res = {}
    for item in d:
        b_sym = item.get("symbol")
        if b_sym in sym_map:
            sym = sym_map[b_sym]
            res[sym] = {
                "price": round(float(item.get("lastPrice", 0)), 4),
                "change": round(float(item.get("priceChangePercent", 0)), 4),
            }
    return res


@cached(cache=TTLCache(maxsize=100, ttl=600))
def get_crypto_kurs(crypto_lst_str: str) -> Dict[str, Any]:
    c_lst = [
        INPUT_NAMES.get(c.strip().lower(), "")
        for c in crypto_lst_str.split(",")
        if c.strip() and INPUT_NAMES.get(c.strip().lower(), "")
    ]
    
    # Удаляем дубликаты
    c_lst = list(dict.fromkeys(c_lst))
    
    if not c_lst:
        return {}

    # Попытка 1: CoinGecko (Primary API)
    try:
        return fetch_from_coingecko(c_lst)
    except requests.RequestException as e1:
        # Попытка 2: Binance (Fallback API)
        try:
            return fetch_from_binance(c_lst)
        except requests.RequestException as e2:
            return {"error": f"CoinGecko: {str(e1)} | Binance: {str(e2)}"}
