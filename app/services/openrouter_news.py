import requests
from cachetools import TTLCache, cached
from typing import List, Dict, Any
from datetime import datetime, timezone


@cached(cache=TTLCache(maxsize=1, ttl=1800))
def get_openrouter_news(lim: int = 10) -> List[Dict[str, Any]]:
    url = "https://openrouter.ai/api/v1/models"
    try:
        req = requests.get(url, timeout=10, headers={"Accept": "application/json"})
        req.raise_for_status()

        data = req.json().get("data", [])
        data.sort(key=lambda m: m.get("created", 0), reverse=True)

        n_lst: List[Dict[str, Any]] = []
        seen_base: set = set()

        for m in data:
            if len(n_lst) >= lim:
                break

            m_id: str = m.get("id", "")
            base_id = m_id.replace(":free", "").replace(":nitro", "")
            if base_id in seen_base:
                continue
            seen_base.add(base_id)

            name = m.get("name", m_id)
            created_ts = m.get("created", 0)
            ctx = m.get("context_length") or 0

            pricing = m.get("pricing") or {}
            prompt_price = pricing.get("prompt", "0")
            try:
                price_f = float(prompt_price)
                if price_f < 0:
                    price_str = "special"
                elif price_f == 0:
                    price_str = "free"
                else:
                    price_str = f"${price_f * 1_000_000:.2f}/1M"
            except (ValueError, TypeError):
                price_str = "?"

            if created_ts:
                dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
                date_str = dt.strftime("%d.%m.%Y")
            else:
                date_str = ""

            ctx_str = f"{ctx // 1000}K" if ctx >= 1000 else str(ctx)

            arch = m.get("architecture") or {}
            in_mod = arch.get("input_modalities") or []
            mod_icons = []
            if "text" in in_mod:
                mod_icons.append("📝")
            if "image" in in_mod:
                mod_icons.append("🖼")
            if "video" in in_mod:
                mod_icons.append("🎬")
            if "audio" in in_mod:
                mod_icons.append("🔊")
            if "file" in in_mod:
                mod_icons.append("📄")
            mod_str = "".join(mod_icons)

            n_lst.append({
                "title": name,
                "link": f"https://openrouter.ai/{m_id}",
                "price": price_str,
                "ctx": ctx_str,
                "date": date_str,
                "mod": mod_str,
                "source": "openrouter",
            })

        return n_lst
    except Exception as e:
        return [{"error": str(e), "source": "openrouter"}]
