#!/usr/bin/env python3
import asyncio
import time
from datetime import datetime
from hl import get_hl_metrics
from vest import get_vest_metrics
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL


def hourly_to_apy(hourly_rate: float) -> float:
    """Convert hourly funding rate to annualized APY."""
    if hourly_rate is None:
        return None
    return hourly_rate* 24 * 365

async def main():
    start_time = time.time()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting arbitrage scan...")

    # Get available Hyperliquid symbols
    info = Info(MAINNET_API_URL, skip_ws=True)
    universe_resp, _ = info.meta_and_asset_ctxs()
    hl_symbols = [u['name'] for u in universe_resp['universe'] if not u['name'].startswith('k')]

    # Optional: restrict to known supported symbols in Vest
    supported_symbols = ["BTC", "ETH", "BNB", "ZRO", "PUMP","BERA","HYPER","ZRO","KAITO"]  # Add mapping as needed
    base_symbols = [s for s in hl_symbols if s in supported_symbols]

    async def fetch_metrics(sym):
        try:
            hl_metrics, vest_metrics = await asyncio.gather(
                get_hl_metrics(sym),
                get_vest_metrics(f"{sym}-PERP")
            )
            fr_hl = hl_metrics.get('funding_rate_snapshot')
            fr_vest = vest_metrics.get('funding_rate_snapshot')

            # Skip if missing or invalid
            if fr_hl is None or fr_vest is None:
                return None

            return sym, fr_hl, fr_vest, fr_hl - fr_vest
        except Exception:
            return None

    results = await asyncio.gather(*(fetch_metrics(sym) for sym in base_symbols))
    results = [r for r in results if r is not None]

    if not results:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No valid arbitrage opportunities found.")
        print(f"Total runtime: {time.time() - start_time:.2f} seconds")
        return

    # Sort by absolute spread and get top 3
    results.sort(key=lambda x: abs(x[3]), reverse=True)
    best = results[0]
    sym, fr_hl, fr_vest, diff = best
    direction = 'Long HL / Short Vest' if diff > 0 else 'Long Vest / Short HL'


    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Best arbitrage on {sym}: {direction}")
    print(f"  HL snapshot funding:   {fr_hl:+.6f} ({hourly_to_apy(fr_hl)*100:.2f}% APY)")
    print(f"  Vest snapshot funding: {fr_vest:+.6f} ({hourly_to_apy(fr_vest)*100:.2f}% APY)")
    print(f"  Funding spread:        {diff:+.6f}  (absolute: {abs(diff):.6f}, APY spread: {hourly_to_apy(diff)*100:.2f}%)")
    print(f"Total runtime: {time.time() - start_time:.2f} seconds")
if __name__ == '__main__':
    asyncio.run(main())
