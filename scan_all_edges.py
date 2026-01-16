#!/usr/bin/env python3
"""
Grid search scanner - shows opportunities at ALL edge levels
Useful for seeing the full spectrum from longshots to sure bets

Usage: python scan_all_edges.py KXLOWTDEN KXLOWTMIA
"""

import os
import sys
import logging
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.WARNING,  # Quiet logs for cleaner output
        format='%(message)s'
    )

def main():
    # Load environment
    load_dotenv()
    setup_logging()

    # Get series tickers from command line
    if len(sys.argv) > 1:
        series_tickers = sys.argv[1:]
    else:
        series_tickers = ["KXLOWTDEN", "KXLOWTMIA"]

    print("=" * 100)
    print("KALSHI WEATHER SCANNER - GRID SEARCH (ALL EDGES)")
    print("=" * 100)
    print(f"Scanning series: {', '.join(series_tickers)}")
    print()

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

    # Try multiple edge thresholds
    thresholds = [
        (0.00, "SHOW ALL (including negative edges)"),
        (0.05, "Aggressive (5%+ edge)"),
        (0.10, "Moderate (10%+ edge)"),
        (0.15, "Conservative (15%+ edge)"),
        (0.20, "Very Conservative (20%+ edge)"),
    ]

    all_results = {}

    for threshold, label in thresholds:
        print(f"\n{'=' * 100}")
        print(f"THRESHOLD: {threshold:.0%} - {label}")
        print('=' * 100)

        try:
            # Initialize scanner with this threshold
            scanner = KalshiWeatherScanner(
                **auth_kwargs,
                bankroll=bankroll,
                kelly_fraction=kelly_fraction,
                min_edge_threshold=threshold
            )

            # Scan (suppress logs)
            opportunities = scanner.scan(series_tickers=series_tickers)
            all_results[threshold] = opportunities

            if opportunities:
                # Sort by edge
                sorted_opps = sorted(opportunities, key=lambda x: x.edge, reverse=True)

                print(f"\n✅ Found {len(opportunities)} opportunities at {threshold:.0%} threshold\n")

                # Show all opportunities
                for i, opp in enumerate(sorted_opps, 1):
                    # Categorize edge
                    if opp.edge >= 0.30:
                        category = "🔥 HUGE EDGE"
                    elif opp.edge >= 0.20:
                        category = "⭐ STRONG EDGE"
                    elif opp.edge >= 0.10:
                        category = "✓ GOOD EDGE"
                    elif opp.edge >= 0.05:
                        category = "~ SMALL EDGE"
                    elif opp.edge >= 0:
                        category = "⚠ TINY EDGE"
                    else:
                        category = "❌ NEGATIVE EDGE"

                    print(f"{i:2d}. {category} | {opp.ticker}")
                    print(f"    Market: {opp.title[:80]}")
                    print(f"    NWS Forecast: min={opp.forecast_min:.1f}°F, max={opp.forecast_max:.1f}°F, avg={opp.forecast_avg:.1f}°F")
                    print(f"    Our Probability: {opp.true_probability:.1%}")
                    print(f"    Market Price: YES={opp.market_yes_price:.1%}, NO={opp.market_no_price:.1%}")
                    print(f"    Edge: {opp.edge:+.1%} | Bet {opp.recommended_side} ${opp.recommended_bet_size:.2f}")
                    print(f"    Reasoning: {opp.reasoning[:120]}")
                    print(f"    Confidence: {opp.confidence:.0%} | Liquidity: ${opp.liquidity_pool_size:,.0f}")
                    print()
            else:
                print(f"\n❌ No opportunities at {threshold:.0%} threshold")
                print("All markets are efficiently priced or outside this threshold.\n")

        except Exception as e:
            print(f"\n❌ Error at threshold {threshold:.0%}: {e}\n")
            continue

    # Summary comparison
    print("\n" + "=" * 100)
    print("SUMMARY - Opportunities by Threshold")
    print("=" * 100)
    print(f"{'Threshold':<15} {'Label':<35} {'Count':>10}")
    print("-" * 100)

    for threshold, label in thresholds:
        count = len(all_results.get(threshold, []))
        print(f"{threshold:>6.0%}         {label:<35} {count:>10}")

    print("=" * 100)

    # Show the wildest longshots (negative or tiny edges)
    print("\n" + "=" * 100)
    print("LONGSHOTS & CONTRARIAN PLAYS (Negative or Tiny Edges)")
    print("=" * 100)
    print("These are markets where Kalshi and NWS roughly agree, or Kalshi is actually")
    print("pricing BETTER than our model. Could be noise, or market knows something we don't.\n")

    if 0.0 in all_results and all_results[0.0]:
        longshots = [opp for opp in all_results[0.0] if opp.edge < 0.05]

        if longshots:
            sorted_longshots = sorted(longshots, key=lambda x: x.edge)

            for i, opp in enumerate(sorted_longshots[:10], 1):  # Top 10 worst
                print(f"{i:2d}. {opp.ticker} | Edge: {opp.edge:+.1%}")
                print(f"    Our prob: {opp.true_probability:.1%} vs Market: {opp.market_yes_price:.1%} YES / {opp.market_no_price:.1%} NO")
                print(f"    {opp.reasoning[:100]}")
                print()
        else:
            print("No longshots found - all markets have positive edges!\n")

    print("=" * 100)
    print("\n💡 TIP: Use MIN_EDGE_THRESHOLD in .env to set your preferred threshold")
    print("   Lower threshold = more opportunities but higher risk")
    print("   Higher threshold = fewer opportunities but higher confidence")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
