#!/usr/bin/env python3
"""
Test script for Cheyenne leading indicator functionality
Tests the NWS adapter methods without requiring Kalshi credentials
"""

import logging
from scanner.nws_adapter import NWSAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("TESTING CHEYENNE LEADING INDICATOR FUNCTIONALITY")
    logger.info("=" * 80)

    # Initialize NWS adapter
    nws = NWSAdapter()

    # Test 1: Check that Cheyenne is in LOCATIONS
    logger.info("\n[Test 1] Checking LOCATIONS configuration")
    logger.info(f"Available locations: {list(nws.LOCATIONS.keys())}")

    if "Cheyenne, WY" in nws.LOCATIONS:
        logger.info("✓ Cheyenne, WY found in LOCATIONS")
        logger.info(f"  Station ID: {nws.LOCATIONS['Cheyenne, WY']['station_id']}")
    else:
        logger.error("✗ Cheyenne, WY not found in LOCATIONS")
        return

    # Test 2: Check leading indicator mapping
    logger.info("\n[Test 2] Checking LEADING_INDICATORS configuration")
    logger.info(f"Leading indicators mapping: {nws.LEADING_INDICATORS}")

    if "Denver, CO" in nws.LEADING_INDICATORS:
        logger.info(f"✓ Denver, CO has leading indicators: {nws.LEADING_INDICATORS['Denver, CO']}")
    else:
        logger.warning("⚠ Denver, CO has no leading indicators configured")

    # Test 3: Fetch observations from both stations
    logger.info("\n[Test 3] Fetching observations from KDEN and KCYS")

    try:
        denver_obs = nws.get_observations("KDEN", hours=200)
        logger.info(f"✓ Denver (KDEN): {len(denver_obs)} observations")
        if denver_obs:
            latest = denver_obs[0]
            logger.info(f"  Latest: {latest['temperature']:.1f}°F at {latest['timestamp']}")
    except Exception as e:
        logger.error(f"✗ Failed to fetch Denver observations: {e}")
        denver_obs = []

    try:
        cheyenne_obs = nws.get_observations("KCYS", hours=200)
        logger.info(f"✓ Cheyenne (KCYS): {len(cheyenne_obs)} observations")
        if cheyenne_obs:
            latest = cheyenne_obs[0]
            logger.info(f"  Latest: {latest['temperature']:.1f}°F at {latest['timestamp']}")
    except Exception as e:
        logger.error(f"✗ Failed to fetch Cheyenne observations: {e}")
        cheyenne_obs = []

    # Test 4: Analyze temperature trends
    logger.info("\n[Test 4] Analyzing temperature trends")

    if denver_obs:
        denver_trend = nws.analyze_temperature_trend(denver_obs, hours_back=6)
        logger.info(f"✓ Denver trend analysis:")
        logger.info(f"  Trend: {denver_trend['trend']}")
        logger.info(f"  Rate: {denver_trend['rate_per_hour']:+.2f}°F/hour")
        logger.info(f"  Change: {denver_trend['change_total']:+.1f}°F over {denver_trend['hours_analyzed']:.1f} hours")
        logger.info(f"  Temperature: {denver_trend['oldest_temp']:.1f}°F → {denver_trend['current_temp']:.1f}°F")

    if cheyenne_obs:
        cheyenne_trend = nws.analyze_temperature_trend(cheyenne_obs, hours_back=6)
        logger.info(f"✓ Cheyenne trend analysis:")
        logger.info(f"  Trend: {cheyenne_trend['trend']}")
        logger.info(f"  Rate: {cheyenne_trend['rate_per_hour']:+.2f}°F/hour")
        logger.info(f"  Change: {cheyenne_trend['change_total']:+.1f}°F over {cheyenne_trend['hours_analyzed']:.1f} hours")
        logger.info(f"  Temperature: {cheyenne_trend['oldest_temp']:.1f}°F → {cheyenne_trend['current_temp']:.1f}°F")

    # Test 5: Get leading indicator insights
    logger.info("\n[Test 5] Getting leading indicator insights for Denver")

    try:
        insights = nws.get_leading_indicator_insights(
            target_station_id="KDEN",
            target_city_state="Denver, CO"
        )

        if insights and insights.get("has_leading_indicators"):
            logger.info("✓ Leading indicator insights:")
            logger.info(f"  Recommendation: {insights['recommendation']}")
            logger.info(f"  Leading stations: {insights['leading_stations']}")

            for insight in insights.get("insights", []):
                logger.info(f"\n  Station {insight['station_id']}:")
                logger.info(f"    Trend: {insight['trend']}")
                logger.info(f"    Rate: {insight['rate_per_hour']:+.2f}°F/hour")
                logger.info(f"    Current temp: {insight['current_temp']:.1f}°F")
                if insight['temp_diff_from_target']:
                    logger.info(f"    Temp diff from Denver: {insight['temp_diff_from_target']:+.1f}°F")

            target_trend = insights.get("target_trend", {})
            logger.info(f"\n  Target (Denver) trend: {target_trend.get('trend', 'unknown')}")
            logger.info(f"  Target rate: {target_trend.get('rate_per_hour', 0):+.2f}°F/hour")

        else:
            logger.warning("⚠ No leading indicators available for Denver")
    except Exception as e:
        logger.error(f"✗ Failed to get leading indicator insights: {e}", exc_info=True)

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
