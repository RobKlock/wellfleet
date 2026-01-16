#!/usr/bin/env python3
"""
Debug script to check specific Kalshi markets
"""

import os
import logging
from dotenv import load_dotenv
from scanner import KalshiClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    load_dotenv()

    # Get credentials
    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")

    if not api_key_id or not os.path.exists(private_key_path):
        logger.error("Need KALSHI_API_KEY_ID and kalshi_api_private_key.txt")
        return 1

    # Initialize client
    client = KalshiClient(api_key_id=api_key_id, private_key_path=private_key_path)

    # Test specific market tickers
    test_tickers = [
        "KXLOWTMIA-26JAN16",
        "KXLOWTDEN-26JAN16"
    ]

    logger.info("Fetching specific markets...")
    for ticker in test_tickers:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Ticker: {ticker}")
            market = client.get_market(ticker)

            logger.info(f"Title: {market.get('title')}")
            logger.info(f"Status: {market.get('status')}")
            logger.info(f"Category: {market.get('category')}")
            logger.info(f"YES bid/ask: {market.get('yes_bid')}/{market.get('yes_ask')}")
            logger.info(f"NO bid/ask: {market.get('no_bid')}/{market.get('no_ask')}")
            logger.info(f"Volume: {market.get('volume')}")
            logger.info(f"Close time: {market.get('close_time')}")
            logger.info(f"Has liquidity pool: {bool(market.get('liquidity_pool'))}")

            if market.get('liquidity_pool'):
                pool = market['liquidity_pool']
                logger.info(f"  Pool size: ${pool.get('pool_size')}")
                logger.info(f"  Start time: {pool.get('start_time')}")
                logger.info(f"  End time: {pool.get('end_time')}")

        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")

    # Also check what promo markets we're actually getting
    logger.info(f"\n{'='*60}")
    logger.info("Checking all promo markets...")
    promo_markets = client.get_promo_markets()
    logger.info(f"Total promo markets: {len(promo_markets)}")

    # Filter for weather/temperature
    weather_markets = [m for m in promo_markets if 'temperature' in m['title'].lower() or 'weather' in m['title'].lower()]
    logger.info(f"Weather/temperature markets: {len(weather_markets)}")

    if weather_markets:
        logger.info("\nWeather markets found:")
        for m in weather_markets[:10]:  # Show first 10
            logger.info(f"  - {m['ticker']}: {m['title'][:80]}")

    # Check for Denver/Miami specifically
    denver_miami = [m for m in promo_markets if 'denver' in m['title'].lower() or 'miami' in m['title'].lower()]
    logger.info(f"\nDenver/Miami markets: {len(denver_miami)}")

    if denver_miami:
        logger.info("\nDenver/Miami markets found:")
        for m in denver_miami:
            logger.info(f"  - {m['ticker']}: {m['title']}")
    else:
        logger.warning("No Denver/Miami markets found in promo markets!")
        logger.info("Checking all categories in promo markets:")
        categories = set(m.get('category', 'unknown') for m in promo_markets)
        logger.info(f"Categories: {categories}")

if __name__ == "__main__":
    main()
