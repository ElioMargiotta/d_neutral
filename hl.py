#!/usr/bin/env python3
import asyncio
from datetime import datetime, timezone
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL

async def get_hl_metrics(symbol: str) -> dict:
    """
    Async version: Retrieve Hyperliquid metrics for a given perpetual symbol.
    Same fields as before, but designed for parallel execution.
    """
    # SDK is still sync, so we run it in a thread to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_hl_metrics_sync, symbol)

def _get_hl_metrics_sync(symbol: str) -> dict:
    """
    Original synchronous logic kept here so we can call it in a thread pool.
    """
    info = Info(MAINNET_API_URL, skip_ws=True)
    uni, ctxs = info.meta_and_asset_ctxs()

    target = symbol if '-' in symbol else f"{symbol.upper()}"
    for u, c in zip(uni['universe'], ctxs):
        if u['name'] == target:
            mark_price = float(c['markPx'])
            open_interest = float(c.get('openInterest', 0))
            open_interest_usd = open_interest * mark_price
            vol_base_24h = float(c.get('dayNtlVlm', 0))
            funding_snapshot = float(c.get('funding', 0))

            def avg_funding_rate(hours):
                now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
                start_ms = now_ms - int(hours * 60 * 60 * 1000)
                hist = info.funding_history(target, start_ms, now_ms)
                rates = [float(e['fundingRate']) for e in hist if 'fundingRate' in e]
                return sum(rates) / len(rates) if rates else None

            return {
                'symbol': target,
                'mark_price': mark_price,
                'funding_rate_snapshot': funding_snapshot,
                'funding_rate_1h': avg_funding_rate(1),
                'funding_rate_24h': avg_funding_rate(24),
                'funding_rate_7d': avg_funding_rate(24*7),
                'funding_rate_30d': avg_funding_rate(24*30),
                'open_interest_usd': open_interest_usd,
                'vol_base_24h': vol_base_24h,
            }
    raise ValueError(f"Perpetual '{target}' not found")

if __name__ == '__main__':
    # Example async run
    async def test():
        data = await get_hl_metrics('BERA')
        print(data)
    asyncio.run(test())
