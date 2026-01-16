#!/usr/bin/env python3
"""
Kalshi Weather Arbitrage Scanner
Main entry point script

Usage:
    python scan.py

Configuration via .env file:
    - KALSHI_API_KEY_ID and kalshi_api_private_key.txt (recommended)
    - Or KALSHI_EMAIL and KALSHI_PASSWORD (legacy)
    - BANKROLL (optional, default 1000)
    - KELLY_FRACTION (optional, default 0.25)
    - MIN_EDGE_THRESHOLD (optional, default 0.20)
"""

import os
import sys
import logging
from dotenv import load_dotenv
from scanner import KalshiWeatherScanner


def setup_logging():
    """Configure logging to both file and console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('kalshi_scanner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("KALSHI WEATHER ARBITRAGE SCANNER")
    logger.info("=" * 80)

    # Get credentials (API key preferred)
    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")

    # Determine authentication method
    if api_key_id and os.path.exists(private_key_path):
        logger.info("Using API key authentication")
        auth_kwargs = {
            "api_key_id": api_key_id,
            "private_key_path": private_key_path
        }
    elif email and password:
        logger.info("Using email/password authentication")
        auth_kwargs = {
            "email": email,
            "password": password
        }
    else:
        logger.error("No valid credentials found!")
        logger.error("Please configure .env with either:")
        logger.error("  - KALSHI_API_KEY_ID + kalshi_api_private_key.txt (recommended)")
        logger.error("  - KALSHI_EMAIL + KALSHI_PASSWORD")
        logger.error("\nSee KALSHI_API_SETUP.md for instructions.")
        return 1

    # Get scanner configuration
    bankroll = float(os.getenv("BANKROLL", "1000"))
    kelly_fraction = float(os.getenv("KELLY_FRACTION", "0.25"))
    min_edge_threshold = float(os.getenv("MIN_EDGE_THRESHOLD", "0.20"))

    logger.info(f"Configuration:")
    logger.info(f"  Bankroll: ${bankroll:.2f}")
    logger.info(f"  Kelly Fraction: {kelly_fraction:.2%}")
    logger.info(f"  Min Edge Threshold: {min_edge_threshold:.0%}")
    logger.info("")

    try:
        # Initialize scanner
        scanner = KalshiWeatherScanner(
            **auth_kwargs,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            min_edge_threshold=min_edge_threshold
        )

        # Run scan and save reports
        opportunities = scanner.run_and_save()

        # Print summary
        logger.info("=" * 80)
        if opportunities:
            logger.info(f"✅ Found {len(opportunities)} opportunities!")
            logger.info("📊 Check ./reports/current.md for details")

            # Show top 3 opportunities
            sorted_opps = sorted(opportunities, key=lambda x: x.edge, reverse=True)
            logger.info("\nTop opportunities:")
            for i, opp in enumerate(sorted_opps[:3], 1):
                logger.info(
                    f"  {i}. {opp.ticker}: {opp.edge:+.1%} edge, "
                    f"bet {opp.recommended_side} ${opp.recommended_bet_size:.2f}"
                )
        else:
            logger.info("❌ No opportunities found")
            logger.info("All markets are efficiently priced or outside edge threshold.")

        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Scanner failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
