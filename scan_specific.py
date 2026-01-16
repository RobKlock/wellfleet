#!/usr/bin/env python3
"""
Scan specific Kalshi market tickers
Usage: python scan_specific.py TICKER1 TICKER2 ...
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

    # Get tickers from command line or use defaults
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        # Default to Denver and Miami markets
        tickers = [
            "KXLOWTDEN-26JAN16",
            "KXLOWTMIA-26JAN16"
        ]

    logger.info(f"Scanning specific tickers: {tickers}")

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

    try:
        # Initialize scanner
        scanner = KalshiWeatherScanner(
            **auth_kwargs,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            min_edge_threshold=min_edge_threshold
        )

        # Scan specific tickers
        opportunities = scanner.scan(specific_tickers=tickers)

        # Generate reports
        if opportunities:
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Found {len(opportunities)} opportunities!")

            # Show details
            for i, opp in enumerate(opportunities, 1):
                logger.info(f"\n{i}. {opp.ticker}")
                logger.info(f"   Location: {opp.location}")
                logger.info(f"   Date: {opp.date}")
                logger.info(f"   Forecast: min={opp.forecast_min}°F, max={opp.forecast_max}°F")
                logger.info(f"   Market: YES={opp.market_yes_price:.0%}, NO={opp.market_no_price:.0%}")
                logger.info(f"   TRUE PROBABILITY: {opp.true_probability:.0%}")
                logger.info(f"   EDGE: {opp.edge:+.1%}")
                logger.info(f"   RECOMMENDATION: {opp.recommended_side} ${opp.recommended_bet_size:.2f}")
                logger.info(f"   Confidence: {opp.confidence:.0%}")
                logger.info(f"   Reasoning: {opp.reasoning}")

            # Save reports
            scanner.run_and_save()

        else:
            logger.info("❌ No opportunities found (markets efficiently priced)")

        logger.info(f"{'='*60}")
        return 0

    except Exception as e:
        logger.error(f"Scanner failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
