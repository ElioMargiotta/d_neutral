#!/usr/bin/env python3
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL
from hl import get_hl_metrics


def main():
    # Initialize SDK
    info = Info(MAINNET_API_URL, skip_ws=True)
    universe_resp, _ = info.meta_and_asset_ctxs()

    # Gather all perpetual symbols
    symbols = [u['name'] for u in universe_resp['universe'] if not u['name'].startswith('k')]
    
    metrics_list = []
    for symbol in symbols:
        try:
            m = get_hl_metrics(symbol)
            metrics_list.append(m)
        except Exception as e:
            # Skip symbols that cause errors
            print(f"Failed to fetch metrics for {symbol}: {e}")

    if not metrics_list:
        print("No metrics retrieved.")
        return

    # Find the pair with the most negative snapshot funding rate
    worst = min(metrics_list, key=lambda x: x.get('funding_rate_snapshot', 0))

    print("Pair with most negative current funding rate:")
    #full metrics
    for k, v in worst.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
