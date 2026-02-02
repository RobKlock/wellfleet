#!/usr/bin/env python3
"""
Show ALL markets with VERBOSE logging to see observation merging

Usage: python show_all_markets_verbose.py KXLOWTDEN
"""

import os
import sys
import logging
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner

def setup_logging():
    """Configure VERBOSE logging to see everything"""
    logging.basicConfig(
        level=logging.INFO,  # Show INFO logs
        format='%(levelname)s - %(message)s'
    )

def main():
    load_dotenv()
    setup_logging()

    if len(sys.argv) > 1:
        series_tickers = sys.argv[1:]
    else:
        series_tickers = ["KXLOWTDEN"]

    print("=" * 100)
    print("SHOW ALL MARKETS (VERBOSE MODE - See Observation Merging)")
    print("=" * 100)
    print(f"Series: {', '.join(series_tickers)}\n")

    # Get credentials
    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")

    if api_key_id and os.path.exists(private_key_path):
        auth_kwargs = {"api_key_id": api_key_id, "private_key_path": private_key_path}
    elif email and password:
        auth_kwargs = {"email": email, "password": password}
    else:
        print("❌ No credentials configured!")
        return 1

    bankroll = float(os.getenv("BANKROLL", "1000"))
    kelly_fraction = float(os.getenv("KELLY_FRACTION", "0.25"))

    try:
        # Set threshold to -1.0 to see EVERYTHING
        scanner = KalshiWeatherScanner(
            **auth_kwargs,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            min_edge_threshold=-1.0  # Show all markets
        )

        opportunities = scanner.scan(series_tickers=series_tickers)

        if opportunities:
            # Sort by edge (best to worst)
            sorted_opps = sorted(opportunities, key=lambda x: x.edge, reverse=True)

            print(f"\n{'=' * 100}")
            print(f"Found {len(opportunities)} markets\n")

            for i, opp in enumerate(sorted_opps, 1):
                # Color code
                if opp.edge >= 0.20:
                    marker = "🔥"
                elif opp.edge >= 0.10:
                    marker = "⭐"
                elif opp.edge >= 0.05:
                    marker = "✓"
                elif opp.edge >= 0:
                    marker = "·"
                else:
                    marker = "❌"

                print(f"{i:3d}. {marker} [{opp.edge:+6.1%}] {opp.ticker}")
                print(f"      {opp.title[:85]}")
                print(f"      Forecast: {opp.forecast_min:.0f}-{opp.forecast_max:.0f}°F (avg {opp.forecast_avg:.0f}°F)")
                print(f"      Our Prob: {opp.true_probability:>5.1%} | Market: YES {opp.market_yes_price:>5.1%} / NO {opp.market_no_price:>5.1%}")
                print(f"      Reasoning: {opp.reasoning[:120]}")
                print()

        else:
            print("No markets found or all markets failed to parse")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
