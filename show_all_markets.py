#!/usr/bin/env python3
"""
Show ALL markets with their edges (including negative)
Set min_edge_threshold to -1.0 to see everything

Usage: python show_all_markets.py KXLOWTDEN
"""

import os
import sys
import logging
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(message)s'
    )

def main():
    load_dotenv()
    setup_logging()

    if len(sys.argv) > 1:
        series_tickers = sys.argv[1:]
    else:
        series_tickers = ["KXLOWTDEN"]

    print("=" * 100)
    print("SHOW ALL MARKETS (Including Negative Edges)")
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

            print(f"Found {len(opportunities)} markets\n")
            print("=" * 100)

            # Create edge buckets
            buckets = {
                "HUGE (30%+)": [],
                "STRONG (20-30%)": [],
                "GOOD (10-20%)": [],
                "DECENT (5-10%)": [],
                "SMALL (2-5%)": [],
                "TINY (0-2%)": [],
                "NEGATIVE (0% to -10%)": [],
                "VERY NEGATIVE (-10%+)": []
            }

            for opp in sorted_opps:
                if opp.edge >= 0.30:
                    buckets["HUGE (30%+)"].append(opp)
                elif opp.edge >= 0.20:
                    buckets["STRONG (20-30%)"].append(opp)
                elif opp.edge >= 0.10:
                    buckets["GOOD (10-20%)"].append(opp)
                elif opp.edge >= 0.05:
                    buckets["DECENT (5-10%)"].append(opp)
                elif opp.edge >= 0.02:
                    buckets["SMALL (2-5%)"].append(opp)
                elif opp.edge >= 0:
                    buckets["TINY (0-2%)"].append(opp)
                elif opp.edge >= -0.10:
                    buckets["NEGATIVE (0% to -10%)"].append(opp)
                else:
                    buckets["VERY NEGATIVE (-10%+)"].append(opp)

            # Show distribution
            print("EDGE DISTRIBUTION")
            print("-" * 100)
            for bucket_name, opps in buckets.items():
                if opps:
                    bar = "█" * len(opps)
                    print(f"{bucket_name:<25} | {bar} ({len(opps)})")
            print()

            # Show all opportunities
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
                print(f"      Bet: {opp.recommended_side} ${opp.recommended_bet_size:.2f} | Confidence: {opp.confidence:.0%}")
                print()

            print("=" * 100)
            print(f"\nShowing all {len(opportunities)} markets")
            print("\nLegend:")
            print("  🔥 = 20%+ edge (very strong)")
            print("  ⭐ = 10-20% edge (strong)")
            print("  ✓ = 5-10% edge (good)")
            print("  · = 0-5% edge (marginal)")
            print("  ❌ = negative edge (market pricing better than our model)")

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
