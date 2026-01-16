#!/usr/bin/env python3
"""
Test script for core components
Tests KalshiClient, NWSAdapter, and MarketParser
"""

import os
import logging
from dotenv import load_dotenv
from datetime import datetime, date

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_market_parser():
    """Test the MarketParser with sample titles"""
    from scanner.market_parser import MarketParser

    logger.info("\n" + "="*60)
    logger.info("Testing MarketParser")
    logger.info("="*60)

    parser = MarketParser()

    test_cases = [
        {
            "title": "Will the minimum temperature in Denver, CO be 31° or above on January 12, 2026?",
            "ticker": "TEST-DENVER-MIN-31",
            "expected": {
                "location": "Denver, CO",
                "metric": "minimum",
                "comparison": "above",
                "threshold": 31.0,
                "date": date(2026, 1, 12)
            }
        },
        {
            "title": "Will the maximum temperature in Miami, FL be 85° or below on January 15, 2026?",
            "ticker": "TEST-MIAMI-MAX-85",
            "expected": {
                "location": "Miami, FL",
                "metric": "maximum",
                "comparison": "below",
                "threshold": 85.0,
                "date": date(2026, 1, 15)
            }
        },
        {
            "title": "Will the minimum temperature in Denver, CO be between 25° and 35° on January 20, 2026?",
            "ticker": "TEST-DENVER-RANGE",
            "expected": {
                "location": "Denver, CO",
                "metric": "minimum",
                "comparison": "between",
                "threshold": 25.0,
                "threshold_high": 35.0,
                "date": date(2026, 1, 20)
            }
        },
        {
            "title": "Will the average temperature in Miami, FL be at least 70° on February 1, 2026?",
            "ticker": "TEST-MIAMI-AVG-70",
            "expected": {
                "location": "Miami, FL",
                "metric": "average",
                "comparison": "above",  # "at least" converts to "above"
                "threshold": 70.0,
                "date": date(2026, 2, 1)
            }
        },
        {
            "title": "Some unparseable market title",
            "ticker": "TEST-UNPARSEABLE",
            "expected": None
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        logger.info(f"\nTest {i}: {test['title'][:60]}...")
        parsed = parser.parse(test["title"], test["ticker"])

        if test["expected"] is None:
            # Expect unparseable
            if not parsed.is_parseable:
                logger.info(f"  ✓ Correctly identified as unparseable")
                passed += 1
            else:
                logger.error(f"  ✗ Should be unparseable but was parsed: {parsed}")
                failed += 1
        else:
            # Expect successful parse
            if not parsed.is_parseable:
                logger.error(f"  ✗ Failed to parse")
                failed += 1
                continue

            # Check each field
            errors = []
            for key, expected_value in test["expected"].items():
                actual_value = getattr(parsed, key)
                if actual_value != expected_value:
                    errors.append(f"{key}: expected {expected_value}, got {actual_value}")

            if errors:
                logger.error(f"  ✗ Parse errors:")
                for error in errors:
                    logger.error(f"    - {error}")
                failed += 1
            else:
                logger.info(f"  ✓ Parsed correctly: {parsed}")
                passed += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"MarketParser Results: {passed} passed, {failed} failed")
    logger.info(f"{'='*60}\n")

    return failed == 0


def test_nws_adapter():
    """Test the NWSAdapter with real API calls"""
    from scanner.nws_adapter import NWSAdapter

    logger.info("\n" + "="*60)
    logger.info("Testing NWSAdapter")
    logger.info("="*60)

    user_agent = os.getenv("NWS_USER_AGENT", "KalshiWeatherScanner/1.0 Test")
    nws = NWSAdapter(user_agent=user_agent)

    # Test 1: Get forecast for Denver
    logger.info("\nTest 1: Fetching Denver forecast...")
    try:
        denver_forecast = nws.get_forecast_for_city("Denver", "CO")
        logger.info(f"  ✓ Retrieved {len(denver_forecast)} forecast periods")

        if denver_forecast:
            first_period = denver_forecast[0]
            logger.info(f"  First period: {first_period.get('startTime')} - {first_period.get('temperature')}°F")
    except Exception as e:
        logger.error(f"  ✗ Failed to fetch Denver forecast: {e}")
        return False

    # Test 2: Get forecast for Miami
    logger.info("\nTest 2: Fetching Miami forecast...")
    try:
        miami_forecast = nws.get_forecast_for_city("Miami", "FL")
        logger.info(f"  ✓ Retrieved {len(miami_forecast)} forecast periods")

        if miami_forecast:
            first_period = miami_forecast[0]
            logger.info(f"  First period: {first_period.get('startTime')} - {first_period.get('temperature')}°F")
    except Exception as e:
        logger.error(f"  ✗ Failed to fetch Miami forecast: {e}")
        return False

    # Test 3: Extract temperature stats for today
    logger.info("\nTest 3: Extracting temperature stats for today...")
    try:
        today = datetime.now().date().isoformat()
        stats = nws.extract_temperature_stats_for_date(
            denver_forecast,
            today,
            "America/Denver"
        )

        if stats:
            logger.info(f"  ✓ Temperature stats for {today}:")
            logger.info(f"    Min: {stats['min']:.1f}°F")
            logger.info(f"    Max: {stats['max']:.1f}°F")
            logger.info(f"    Avg: {stats['avg']:.1f}°F")
            logger.info(f"    Periods: {stats['num_periods']}")
        else:
            logger.warning(f"  ⚠ No data available for today (may be too far in future)")
    except Exception as e:
        logger.error(f"  ✗ Failed to extract temperature stats: {e}")
        return False

    # Test 4: Convenience method
    logger.info("\nTest 4: Testing convenience method...")
    try:
        tomorrow = datetime.now().date().replace(day=datetime.now().date().day + 1).isoformat()
        stats = nws.get_forecast_stats_for_city_and_date("Denver", "CO", tomorrow)

        if stats:
            logger.info(f"  ✓ Stats for tomorrow ({tomorrow}):")
            logger.info(f"    Min: {stats['min']:.1f}°F")
            logger.info(f"    Max: {stats['max']:.1f}°F")
            logger.info(f"    Avg: {stats['avg']:.1f}°F")
        else:
            logger.warning(f"  ⚠ No data available for tomorrow")
    except Exception as e:
        logger.error(f"  ✗ Failed convenience method: {e}")
        return False

    logger.info(f"\n{'='*60}")
    logger.info(f"NWSAdapter: All tests passed")
    logger.info(f"{'='*60}\n")

    return True


def test_kalshi_client():
    """Test the KalshiClient with real API calls"""
    from scanner.kalshi_client import KalshiClient

    logger.info("\n" + "="*60)
    logger.info("Testing KalshiClient")
    logger.info("="*60)

    # Check for API key credentials (preferred method)
    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")

    # Fallback to email/password
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")

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
        logger.warning("  ⚠ No Kalshi credentials found in .env")
        logger.warning("  ⚠ Need either:")
        logger.warning("  ⚠   - KALSHI_API_KEY_ID + kalshi_api_private_key.txt")
        logger.warning("  ⚠   - KALSHI_EMAIL + KALSHI_PASSWORD")
        logger.warning("  ⚠ Skipping KalshiClient tests")
        return True  # Don't fail if credentials aren't set

    # Test 1: Authentication
    logger.info("\nTest 1: Authentication...")
    try:
        client = KalshiClient(**auth_kwargs)
        logger.info(f"  ✓ Authenticated successfully using {client.auth_method}")
    except Exception as e:
        logger.error(f"  ✗ Authentication failed: {e}")
        return False

    # Test 2: Get events
    logger.info("\nTest 2: Fetching events...")
    try:
        events = client.get_events(status="open", limit=10)
        logger.info(f"  ✓ Retrieved {len(events)} events")

        if events:
            first_event = events[0]
            logger.info(f"  First event: {first_event.get('event_ticker')}")
            logger.info(f"    Title: {first_event.get('title')[:60]}...")
            logger.info(f"    Markets: {len(first_event.get('markets', []))}")
    except Exception as e:
        logger.error(f"  ✗ Failed to fetch events: {e}")
        return False

    # Test 3: Get promo markets
    logger.info("\nTest 3: Fetching promo markets...")
    try:
        promo_markets = client.get_promo_markets()
        logger.info(f"  ✓ Found {len(promo_markets)} promo markets")

        if promo_markets:
            # Show first few promo markets
            for i, market in enumerate(promo_markets[:3], 1):
                logger.info(f"\n  Promo Market {i}:")
                logger.info(f"    Ticker: {market['ticker']}")
                logger.info(f"    Title: {market['title'][:60]}...")
                logger.info(f"    Category: {market.get('category')}")
                logger.info(f"    Volume: {market.get('volume')}")
                logger.info(f"    YES bid/ask: {market.get('yes_bid')}/{market.get('yes_ask')}")
                logger.info(f"    NO bid/ask: {market.get('no_bid')}/{market.get('no_ask')}")
                logger.info(f"    Pool size: ${market.get('liquidity_pool', {}).get('pool_size')}")

            # Count weather markets
            weather_markets = [m for m in promo_markets if 'temperature' in m['title'].lower()]
            logger.info(f"\n  Weather markets: {len(weather_markets)}")

            # Count Denver/Miami markets
            denver_miami = [m for m in weather_markets if 'denver' in m['title'].lower() or 'miami' in m['title'].lower()]
            logger.info(f"  Denver/Miami weather markets: {len(denver_miami)}")

    except Exception as e:
        logger.error(f"  ✗ Failed to fetch promo markets: {e}")
        return False

    logger.info(f"\n{'='*60}")
    logger.info(f"KalshiClient: All tests passed")
    logger.info(f"{'='*60}\n")

    return True


def main():
    """Run all component tests"""
    # Load environment variables
    load_dotenv()

    logger.info("=" * 80)
    logger.info("KALSHI WEATHER SCANNER - CORE COMPONENT TESTS")
    logger.info("=" * 80)

    results = {}

    # Test 1: MarketParser (no API calls needed)
    results['parser'] = test_market_parser()

    # Test 2: NWSAdapter (uses NWS API)
    results['nws'] = test_nws_adapter()

    # Test 3: KalshiClient (uses Kalshi API, requires credentials)
    results['kalshi'] = test_kalshi_client()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for component, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{component.upper():15} {status}")

    all_passed = all(results.values())
    logger.info("=" * 80)

    if all_passed:
        logger.info("✓ ALL TESTS PASSED")
        logger.info("\nCore components are ready! Next steps:")
        logger.info("1. Implement MispricingDetector")
        logger.info("2. Implement ReportGenerator")
        logger.info("3. Implement main KalshiWeatherScanner orchestrator")
        logger.info("4. Create scan.py entry point")
    else:
        logger.info("✗ SOME TESTS FAILED")
        logger.info("\nPlease fix the failing components before proceeding.")

    logger.info("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
