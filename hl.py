#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL


def get_hl_metrics(symbol: str) -> dict:
    """
    Retrieve Hyperliquid metrics for a given perpetual symbol:
        - mark_price (float, USD)
        - funding_rate_snapshot (float)
        - funding_rate_1h (float)
        - funding_rate_24h (float)
        - funding_rate_7d (float)
        - funding_rate_30d (float)
        - open_interest_usd (float, USD)
        - vol_base_24h (float, base asset volume in 24h)
      
    Args:
        symbol: e.g.'BTC'
    Returns:
        dict of metrics.
    """
    # Initialize SDK
    info = Info(MAINNET_API_URL, skip_ws=True)
    uni, ctxs = info.meta_and_asset_ctxs()

    # Normalize symbol to full perp name
    target = symbol if '-' in symbol else f"{symbol.upper()}"

    for u, c in zip(uni['universe'], ctxs):
        if u['name'] == target:
            # Prices
            mark_price = float(c['markPx'])
            # Open Interest and volumes
            open_interest = float(c.get('openInterest', 0))
            open_interest_usd = open_interest * mark_price
            vol_base_24h = float(c.get('dayNtlVlm', 0))
            funding_snapshot = float(c.get('funding', 0))
            # 1h average funding rate
            
            def avg_funding_rate(h):
                hour=int(h)
                now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
                start_ms = now_ms - hour * 60 * 60 * 1000 # convert hours to milliseconds
                hist = info.funding_history(target, start_ms, now_ms)
                rates = []
                for e in hist:
                    rate = e.get('fundingRate')
                    try:
                        rates.append(float(rate))
                    except (TypeError, ValueError):
                        continue
                avg_fund= sum(rates) / len(rates) if rates else None
                return avg_fund

            funding_1h  = avg_funding_rate(1)
            funding_24h = avg_funding_rate(24)
            funding_7d   = avg_funding_rate(24 * 7)
            funding_30d  = avg_funding_rate(24 * 30)

            return {
                'symbol': target,
                'mark_price': mark_price,
                'funding_rate_snapshot': funding_snapshot,
                'funding_rate_1h': funding_1h,
                'funding_rate_24h': funding_24h,
                'funding_rate_7d': funding_7d,
                'funding_rate_30d': funding_30d,
                'open_interest_usd': open_interest_usd,
                'vol_base_24h': vol_base_24h,
            }

    raise ValueError(f"Perpetual '{target}' not found in Hyperliquid universe.")

if __name__ == '__main__':
    # Example
    metrics = get_hl_metrics('BERA')
    print(metrics)
