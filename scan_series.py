#!/usr/bin/env python3
"""
Scan Kalshi series (all markets in a series)
Usage: python scan_series.py [SERIES1] [SERIES2] ...

Example:
  python scan_series.py KXLOWTDEN KXLOWTMIA
"""

import os
import sys
import logging
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('kalshi_scanner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    # Load environment
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)

    # Get series tickers from command line or use defaults
    if len(sys.argv) > 1:
        series_tickers = sys.argv[1:]
    else:
        # Default to Denver and Miami lowest temperature series
        series_tickers = [
            "KXLOWTDEN",  # Lowest temperature in Denver
            "KXLOWTMIA"   # Lowest temperature in Miami
        ]

    logger.info("=" * 80)
    logger.info("KALSHI WEATHER SCANNER - SERIES MODE")
    logger.info("=" * 80)
    logger.info(f"Scanning series: {', '.join(series_tickers)}")

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
        logger.error("No credentials configured!")
        return 1

    # Get scanner config
    bankroll = float(os.getenv("BANKROLL", "1000"))
    kelly_fraction = float(os.getenv("KELLY_FRACTION", "0.25"))
    min_edge_threshold = float(os.getenv("MIN_EDGE_THRESHOLD", "0.20"))

    logger.info(f"Configuration:")
    logger.info(f"  Bankroll: ${bankroll:.2f}")
    logger.info(f"  Kelly Fraction: {kelly_fraction:.2%}")
    logger.info(f"  Min Edge: {min_edge_threshold:.0%}")
    logger.info("")

    try:
        # Initialize scanner
        scanner = KalshiWeatherScanner(
            **auth_kwargs,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            min_edge_threshold=min_edge_threshold
        )

        # Scan series
        opportunities = scanner.scan(series_tickers=series_tickers)

        # Generate reports
        logger.info("=" * 80)
        if opportunities:
            logger.info(f"✅ Found {len(opportunities)} opportunities!")
            logger.info("")

            # Show summary
            summary = scanner.reporter.generate_summary(opportunities)
            logger.info(summary)
            logger.info("")

            # Show top opportunities
            sorted_opps = sorted(opportunities, key=lambda x: x.edge, reverse=True)
            logger.info("Top opportunities:")
            for i, opp in enumerate(sorted_opps[:5], 1):
                logger.info(
                    f"  {i}. {opp.ticker}: {opp.edge:+.1%} edge, "
                    f"bet {opp.recommended_side} ${opp.recommended_bet_size:.2f}"
                )
                logger.info(f"     {opp.reasoning[:100]}...")

            # Save full reports
            logger.info("")
            report_md = scanner.reporter.generate_daily_report(opportunities)
            report_csv = scanner.reporter.generate_csv_export(opportunities)

            # Save files
            from datetime import datetime
            from pathlib import Path

            output_dir = "./reports"
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            md_path = f"{output_dir}/kalshi_report_{timestamp}.md"
            csv_path = f"{output_dir}/kalshi_opportunities_{timestamp}.csv"
            current_path = f"{output_dir}/current.md"

            with open(md_path, "w") as f:
                f.write(report_md)
            with open(csv_path, "w") as f:
                f.write(report_csv)
            with open(current_path, "w") as f:
                f.write(report_md)

            logger.info(f"📊 Saved reports:")
            logger.info(f"   - {md_path}")
            logger.info(f"   - {csv_path}")
            logger.info(f"   - {current_path}")

        else:
            logger.info("❌ No opportunities found")
            logger.info("All markets are efficiently priced or outside edge threshold.")

        logger.info("=" * 80)
        return 0

    except Exception as e:
        logger.error(f"Scanner failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
