#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "https://serverprod.vest.exchange/v2"


def get_vest_metrics(symbol: str, account_group: str = "0") -> dict:
    """
    Retrieve Vest metrics for a given perpetual symbol:
      - mark_price (float)
      - funding_rate_snapshot (float)
      - funding_rate_1h (float)
      - funding_rate_24h (float)
      - funding_rate_7d (float)
      - funding_rate_30d (float)
      - vol_base_24h (float)
      - vol_quote_24h (float)
      - open_interest (None) + note
    """
    headers = {
        "xrestservermm": f"restserver{account_group}",
        "Content-Type": "application/json"
    }

    # 1) Latest ticker for mark price and snapshot funding rate
    resp_latest = requests.get(
        f"{BASE_URL}/ticker/latest", headers=headers,
        params={"symbols": symbol}
    )
    resp_latest.raise_for_status()
    ticker = resp_latest.json()["tickers"][0]

    mark_price = float(ticker["markPrice"])
    funding_snapshot = float(ticker["oneHrFundingRate"])

    # 2) 24h ticker for base and quote volume
    resp_24hr = requests.get(
        f"{BASE_URL}/ticker/24hr", headers=headers,
        params={"symbols": symbol}
    )
    resp_24hr.raise_for_status()
    vol_info = resp_24hr.json()["tickers"][0]
    vol_base_24h = float(vol_info["volume"])
    vol_quote_24h = float(vol_info["quoteVolume"])

    # 3) Funding history for averaging
    now = datetime.now(timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    # fetch last 30 days hourly data
    start_30d_ms = int((now - timedelta(days=30)).timestamp() * 1000)
    resp_hist = requests.get(
        f"{BASE_URL}/funding/history", headers=headers,
        params={
            "symbol": symbol,
            "startTime": start_30d_ms,
            "endTime": now_ms,
            "limit": 1000,
            "interval": "1h"
        }
    )
    resp_hist.raise_for_status()
    hist = resp_hist.json()  # list of {symbol, time, oneHrFundingRate}

    # helper to compute average over last `d` days
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

    funding_rate_1h = avg_rate(2*1/24)
    funding_rate_24h = avg_rate(1)
    funding_rate_7d = avg_rate(7)
    funding_rate_30d = avg_rate(30)

    # 4) Open interest placeholder
    open_interest = None
    note = "Open interest not exposed by public Vest API"

    return {
        "symbol": symbol,
        "mark_price": mark_price,
        "funding_rate_snapshot": funding_snapshot,
        "funding_rate_1h": funding_rate_1h,
        "funding_rate_24h": funding_rate_24h,
        "funding_rate_7d": funding_rate_7d,
        "funding_rate_30d": funding_rate_30d,
        "vol_base_24h": vol_base_24h,
    }


if __name__ == "__main__":
    # Example usage
    data = get_vest_metrics("BTC-PERP", account_group="0")
    print(data)
