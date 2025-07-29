#!/usr/bin/env python3
import aiohttp
from datetime import datetime, timedelta, timezone

BASE_URL = "https://serverprod.vest.exchange/v2"

async def get_vest_metrics(symbol: str, account_group: str = "0") -> dict:
    """
    Async: Retrieve Vest metrics for a given perpetual symbol.
    """
    headers = {
        "xrestservermm": f"restserver{account_group}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # 1) Latest ticker
        async with session.get(f"{BASE_URL}/ticker/latest", headers=headers, params={"symbols": symbol}) as r:
            r.raise_for_status()
            ticker = (await r.json())["tickers"][0]
        mark_price = float(ticker["markPrice"])
        funding_snapshot = float(ticker["oneHrFundingRate"])

        # 2) 24h ticker
        async with session.get(f"{BASE_URL}/ticker/24hr", headers=headers, params={"symbols": symbol}) as r:
            r.raise_for_status()
            vol_info = (await r.json())["tickers"][0]
        vol_base_24h = float(vol_info["volume"])
        vol_quote_24h = float(vol_info["quoteVolume"])

        # 3) Funding history
        now = datetime.now(timezone.utc)
        now_ms = int(now.timestamp() * 1000)
        start_30d_ms = int((now - timedelta(days=30)).timestamp() * 1000)
        async with session.get(
            f"{BASE_URL}/funding/history", headers=headers, params={
                "symbol": symbol,
                "startTime": start_30d_ms,
                "endTime": now_ms,
                "limit": 1000,
                "interval": "1h"
            }
        ) as r:
            r.raise_for_status()
            hist = await r.json()

    def avg_rate(days: float) -> float:
        cutoff = int((now - timedelta(days=days)).timestamp() * 1000)
        rates = []
        for e in hist:
            ts = int(e.get("time", e.get("timestamp", 0)))
            if ts >= cutoff:
                try:
                    rates.append(float(e.get("oneHrFundingRate")))
                except (TypeError, ValueError):
                    continue
        return sum(rates) / len(rates) if rates else None

    return {
        "symbol": symbol,
        "mark_price": mark_price,
        "funding_rate_snapshot": funding_snapshot,
        "funding_rate_1h": avg_rate(2*1/24),
        "funding_rate_24h": avg_rate(1),
        "funding_rate_7d": avg_rate(7),
        "funding_rate_30d": avg_rate(30),
        "vol_base_24h": vol_base_24h,
    }
