#!/usr/bin/env python3
"""
Portfolio Analysis Script
Shows optimal portfolio allocation and hedging strategies for correlated temperature markets

Usage:
    python portfolio_analysis.py                    # Analyze all series
    python portfolio_analysis.py KXLOWTDEN         # Analyze specific series
    python portfolio_analysis.py --budget 100      # Set custom budget
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner, PortfolioOptimizer


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s - %(message)s'
    )


def print_portfolio_group(group, optimizer, budget):
    """Print detailed analysis for a portfolio group"""
    print(f"\n{'=' * 100}")
    print(f"📊 PORTFOLIO: {group.location} {group.metric.upper()} on {group.date.strftime('%B %d, %Y')}")
    print(f"{'=' * 100}")

    print(f"\n🎯 OVERVIEW:")
    print(f"  Markets: {len(group.opportunities)}")
    print(f"  Total Edge: {group.total_edge:+.1%}")
    print(f"  Sharpe Ratio: {group.sharpe_ratio:.2f}")
    print(f"  Recommended Allocation: ${group.recommended_allocation * optimizer.bankroll:.2f} ({group.recommended_allocation:.1%} of bankroll)")

    print(f"\n💰 EXPECTED RETURNS:")
    print(f"  Expected: ${group.expected_return:+,.2f}")
    print(f"  Best Case: ${group.max_return:+,.2f}")
    print(f"  Worst Case: ${group.min_return:+,.2f}")

    print(f"\n⚠️ RISK METRICS:")
    print(f"  Standard Deviation: ${group.std_dev:.2f}")
    print(f"  Max Drawdown: ${group.max_drawdown:.2f}")

    # Show all opportunities in the group
    print(f"\n📋 ALL MARKETS IN GROUP:")
    for i, opp in enumerate(group.opportunities, 1):
        marker = "⭐" if opp == group.primary_bet else " "
        print(f"  {marker} {i}. [{opp.edge:+6.1%}] {opp.ticker}")
        print(f"      {opp.title[:80]}")
        print(f"      Our Prob: {opp.true_probability:>5.1%} | Market: {opp.recommended_side} @ {opp.market_yes_price if opp.recommended_side == 'YES' else opp.market_no_price:.1%}")
        print(f"      Recommended: ${opp.recommended_bet_size:.2f}")

    # Generate hedging strategy
    print(f"\n🛡️ HEDGING STRATEGY (Budget: ${budget:.2f}):")
    strategy = optimizer.generate_hedging_strategy(group, budget)

    if strategy:
        print(f"  Risk Level: {strategy.risk_level}")
        print(f"  Confidence: {strategy.confidence:.1%}")
        print(f"\n  PRIMARY POSITION:")
        print(f"    ${budget * 0.6:.2f} → {strategy.primary.ticker} {strategy.primary.recommended_side}")
        print(f"    Entry: {strategy.primary.market_yes_price if strategy.primary.recommended_side == 'YES' else strategy.primary.market_no_price:.1%}")
        print(f"    True Prob: {strategy.primary.true_probability:.1%}")
        print(f"    Edge: {strategy.primary.edge:+.1%}")

        if strategy.hedges:
            print(f"\n  HEDGE POSITIONS:")
            for opp, allocation, reason in strategy.hedges:
                if allocation > 0.50:  # Only show hedges with meaningful allocation
                    price = opp.market_yes_price if opp.recommended_side == "YES" else opp.market_no_price
                    print(f"    ${allocation:.2f} → {opp.ticker} {opp.recommended_side}")
                    print(f"      Entry: {price:.1%} | Edge: {opp.edge:+.1%} | Reason: {reason}")

        print(f"\n  RETURN RANGE:")
        print(f"    Expected: ${strategy.expected_return_range[0]:+,.2f} to ${strategy.expected_return_range[1]:+,.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze portfolio allocation and hedging strategies for temperature markets"
    )
    parser.add_argument(
        "series",
        nargs="*",
        default=[],
        help="Series tickers to analyze (e.g., KXLOWTDEN). Default: all"
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=100.0,
        help="Budget per portfolio group (default: $100)"
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=1000.0,
        help="Total bankroll (default: $1000)"
    )
    parser.add_argument(
        "--min-edge",
        type=float,
        default=0.05,
        help="Minimum edge threshold (default: 0.05 = 5%%)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    load_dotenv()
    setup_logging(args.verbose)

    print("=" * 100)
    print("PORTFOLIO ANALYSIS - Optimal Allocation & Hedging Strategies")
    print("=" * 100)

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

    try:
        # Initialize scanner
        scanner = KalshiWeatherScanner(
            **auth_kwargs,
            bankroll=args.bankroll,
            kelly_fraction=0.25,
            min_edge_threshold=args.min_edge
        )

        # Run scan
        series_tickers = args.series if args.series else None
        opportunities = scanner.scan(series_tickers=series_tickers)

        if not opportunities:
            print("\n❌ No opportunities found")
            return 0

        print(f"\n✅ Found {len(opportunities)} opportunities")

        # Initialize portfolio optimizer
        optimizer = PortfolioOptimizer(bankroll=args.bankroll)

        # Group correlated markets
        portfolio_groups = optimizer.group_correlated_markets(opportunities)

        if not portfolio_groups:
            print("\n⚠️ No correlated market groups found (need 2+ markets for same location/date/metric)")
            print("\nShowing individual opportunities:")
            for i, opp in enumerate(sorted(opportunities, key=lambda x: x.edge, reverse=True)[:5], 1):
                print(f"\n  {i}. [{opp.edge:+.1%}] {opp.ticker}")
                print(f"     {opp.title[:80]}")
                print(f"     Recommended: {opp.recommended_side} ${opp.recommended_bet_size:.2f}")
            return 0

        print(f"\n📊 Found {len(portfolio_groups)} portfolio groups with correlated markets\n")

        # Analyze each portfolio group
        for group in portfolio_groups:
            print_portfolio_group(group, optimizer, args.budget)

        # Summary
        print(f"\n{'=' * 100}")
        print(f"💼 PORTFOLIO SUMMARY")
        print(f"{'=' * 100}")

        total_allocation = sum(g.recommended_allocation for g in portfolio_groups) * args.bankroll
        total_expected = sum(g.expected_return for g in portfolio_groups)
        avg_sharpe = sum(g.sharpe_ratio for g in portfolio_groups) / len(portfolio_groups)

        print(f"\nTotal Recommended Allocation: ${total_allocation:.2f}")
        print(f"Total Expected Return: ${total_expected:+,.2f}")
        print(f"Average Sharpe Ratio: {avg_sharpe:.2f}")

        print(f"\n🎯 TOP 3 GROUPS BY SHARPE RATIO:")
        for i, group in enumerate(portfolio_groups[:3], 1):
            print(f"  {i}. {group.location} {group.metric} on {group.date.strftime('%b %d')}: Sharpe {group.sharpe_ratio:.2f}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
