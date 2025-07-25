#!/usr/bin/env python3
from hl import get_hl_metrics
from vest import get_vest_metrics
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL


def main():
    # Initialize Hyperliquid SDK to list available perps
    info = Info(MAINNET_API_URL, skip_ws=True)
    universe_resp, _ = info.meta_and_asset_ctxs()

    # Build base symbol list from perp names, skip those prefixed 'k'
    base_symbols = [u['name'] for u in universe_resp['universe'] if not u['name'].startswith('k')]

    best = None
    best_diff = 0.0

    for sym in sorted(base_symbols):
        try:
            hl_metrics = get_hl_metrics(sym)
            vest_metrics = get_vest_metrics(f"{sym}-PERP")
            fr_hl = hl_metrics.get('funding_rate_snapshot', 0) or 0
            fr_vest = vest_metrics.get('funding_rate_snapshot', 0) or 0

            diff = fr_hl - fr_vest
            if best is None or abs(diff) > abs(best_diff):
                best_diff = diff
                best = {
                    'symbol': sym,
                    'hl_rate': fr_hl,
                    'vest_rate': fr_vest,
                    'diff': diff
                }
        except Exception:
            continue

    if best:
        direction = ('Long HL / Short Vest' if best['diff'] > 0 else 'Long Vest / Short HL')
        print(f"Best arbitrage on {best['symbol']}: {direction}")
        print(f"  HL snapshot funding:   {best['hl_rate']:.6f}")
        print(f"  Vest snapshot funding: {best['vest_rate']:.6f}")
        print(f"  Funding spread:        {best['diff']:.6f}")
    else:
        print("No valid arbitrage opportunities found.")
        
if __name__ == '__main__':
    main()
