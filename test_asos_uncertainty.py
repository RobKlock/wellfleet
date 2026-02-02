#!/usr/bin/env python3
"""
Test ASOS Uncertainty Detection
Validates that the scanner correctly identifies when observations are in the uncertainty zone
"""

import logging
from datetime import date
from scanner.market_parser import ParsedMarket
from scanner.mispricing_detector import MispricingDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_asos_uncertainty():
    """Test ASOS uncertainty detection with various scenarios"""

    logger.info("=" * 80)
    logger.info("TESTING ASOS UNCERTAINTY DETECTION")
    logger.info("=" * 80)

    # Initialize detector
    detector = MispricingDetector(
        bankroll=1000,
        kelly_fraction=0.25,
        min_edge_threshold=0.05
    )

    # Test Case 1: Observed 19.4°F, threshold 20°F (close - should warn!)
    logger.info("\n[Test 1] Observed 19.4°F vs threshold 20°F")
    logger.info("Expected: ⚠️ ASOS UNCERTAINTY WARNING (within 1°F)")

    forecast1 = {
        "min": 19.4,
        "max": 35.0,
        "avg": 27.2,
        "timezone": "America/Denver",
        "includes_observations": True
    }

    parsed1 = ParsedMarket(
        ticker="TEST-B19.5",
        location="Denver, CO",
        metric="minimum",
        comparison="between",
        threshold=19.0,
        threshold_high=20.0,
        date=date.today(),
        is_parseable=True
    )

    result1 = detector._check_observation_constraints(forecast1, parsed1, "min")
    logger.info(f"Result: {result1:.1%} confidence" if result1 else "Not constrained")


    # Test Case 2: Observed 17.0°F, threshold 20°F (far - should NOT warn)
    logger.info("\n[Test 2] Observed 17.0°F vs threshold 20°F")
    logger.info("Expected: NO WARNING (>1°F away, clearly resolved)")

    forecast2 = {
        "min": 17.0,
        "max": 35.0,
        "avg": 26.0,
        "timezone": "America/Denver",
        "includes_observations": True
    }

    parsed2 = ParsedMarket(
        ticker="TEST-T20",
        location="Denver, CO",
        metric="minimum",
        comparison="at least",
        threshold=20.0,
        date=date.today(),
        is_parseable=True
    )

    result2 = detector._check_observation_constraints(forecast2, parsed2, "min")
    logger.info(f"Result: {result2:.1%} confidence" if result2 else "Not constrained")


    # Test Case 3: Observed 20.8°F, threshold 21°F (edge case!)
    logger.info("\n[Test 3] Observed 20.8°F vs threshold 21°F")
    logger.info("Expected: ⚠️ ASOS UNCERTAINTY WARNING (within 1°F of boundary)")

    forecast3 = {
        "min": 20.8,
        "max": 36.0,
        "avg": 28.4,
        "timezone": "America/Denver",
        "includes_observations": True
    }

    parsed3 = ParsedMarket(
        ticker="TEST-B20.5",
        location="Denver, CO",
        metric="minimum",
        comparison="between",
        threshold=20.0,
        threshold_high=21.0,
        date=date.today(),
        is_parseable=True
    )

    result3 = detector._check_observation_constraints(forecast3, parsed3, "min")
    logger.info(f"Result: {result3:.1%} confidence" if result3 else "Not constrained")


    # Test Case 4: The real Denver Jan 19 case!
    logger.info("\n[Test 4] REAL CASE: Denver Jan 19 - Observed 19.4°F in B18.5 (18-19°F range)")
    logger.info("Expected: ⚠️ ASOS UNCERTAINTY WARNING (could be 19 or 20 in final CLI)")

    forecast4 = {
        "min": 19.4,
        "max": 25.0,
        "avg": 22.0,
        "timezone": "America/Denver",
        "includes_observations": True
    }

    parsed4 = ParsedMarket(
        ticker="KXLOWTDEN-26JAN19-B18.5",
        location="Denver, CO",
        metric="minimum",
        comparison="between",
        threshold=18.0,
        threshold_high=19.0,
        date=date(2026, 1, 19),
        is_parseable=True
    )

    result4 = detector._check_observation_constraints(forecast4, parsed4, "min")
    logger.info(f"Result: {result4:.1%} confidence" if result4 else "Not constrained")
    logger.info("Interpretation: If ASOS 5-min avg was 19.5-19.9°F, final CLI will show 20°F (bet LOSES)")


    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)
    logger.info("\nKey Takeaway:")
    logger.info("  When observed temp is within ±1°F of threshold:")
    logger.info("  → Scanner issues WARNING about ASOS uncertainty")
    logger.info("  → Confidence reduced by 30%")
    logger.info("  → Displayed integer value may round differently in final CLI")


if __name__ == "__main__":
    test_asos_uncertainty()
