#!/usr/bin/env python3
"""
Test script for Boundary Forecast Model

Tests the enhanced probability calculation for markets within ±3°F of thresholds
"""

import logging
from scanner.mispricing_detector import BoundaryForecastModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_boundary_vs_simple():
    """Test boundary case detection and probability calculation"""
    model = BoundaryForecastModel()

    logger.info("=" * 80)
    logger.info("TEST 1: Boundary Case vs Simple Case")
    logger.info("=" * 80)

    # Test Case 1: Boundary case (forecast 32°F, threshold 33°F)
    logger.info("\nCase 1: Boundary case - Forecast 32°F, threshold ≥33°F")
    prob_boundary = model.calculate_boundary_probability(
        forecast_value=32.0,
        threshold=33.0,
        threshold_high=None,
        comparison="above"
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob_boundary:.1%}")

    # Test Case 2: Clear case (forecast 42°F, threshold 33°F)
    logger.info("\nCase 2: Non-boundary case - Forecast 42°F, threshold ≥33°F")
    prob_clear = model.calculate_boundary_probability(
        forecast_value=42.0,
        threshold=33.0,
        threshold_high=None,
        comparison="above"
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob_clear:.1%}")


def test_meteorological_adjustments():
    """Test impact of meteorological conditions"""
    model = BoundaryForecastModel()

    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Meteorological Adjustments")
    logger.info("=" * 80)

    # Base case: forecast 32°F, threshold ≥33°F
    forecast_value = 32.0
    threshold = 33.0

    # Scenario 1: Clear skies (radiative cooling)
    logger.info("\nScenario 1: Clear skies overnight")
    current_conditions = {
        "temperature": 35.0,
        "dewpoint": 20.0,
        "wind_speed": 3.0,
        "sky_cover": 10
    }
    forecast_stats = {
        "avg_sky_cover": 10,
        "avg_wind_speed": 3.0,
        "avg_dewpoint": 20.0
    }
    prob1 = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=threshold,
        threshold_high=None,
        comparison="above",
        current_conditions=current_conditions,
        forecast_stats=forecast_stats
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob1:.1%}")
    logger.info("Expected: Lower probability (clear skies → enhanced cooling)")

    # Scenario 2: Cloudy with high winds (mixing)
    logger.info("\nScenario 2: Cloudy with high winds")
    current_conditions = {
        "temperature": 35.0,
        "dewpoint": 28.0,
        "wind_speed": 15.0,
        "sky_cover": 90
    }
    forecast_stats = {
        "avg_sky_cover": 90,
        "avg_wind_speed": 15.0,
        "avg_dewpoint": 28.0
    }
    prob2 = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=threshold,
        threshold_high=None,
        comparison="above",
        current_conditions=current_conditions,
        forecast_stats=forecast_stats
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob2:.1%}")
    logger.info("Expected: Higher probability (clouds + wind → less cooling)")

    # Scenario 3: Current temp constraint
    logger.info("\nScenario 3: Current temp already 38°F")
    current_conditions = {
        "temperature": 38.0,
        "dewpoint": 30.0,
        "wind_speed": 5.0,
        "sky_cover": 50
    }
    forecast_stats = {
        "avg_sky_cover": 50,
        "avg_wind_speed": 5.0,
        "avg_dewpoint": 30.0
    }
    prob3 = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=threshold,
        threshold_high=None,
        comparison="above",
        current_conditions=current_conditions,
        forecast_stats=forecast_stats
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob3:.1%}")
    logger.info("Expected: Much higher probability (already warm)")


def test_comparison_operators():
    """Test different comparison operators"""
    model = BoundaryForecastModel()

    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Comparison Operators")
    logger.info("=" * 80)

    forecast_value = 32.0

    # Above
    logger.info("\nOperator: ABOVE (temp ≥ 33°F)")
    prob_above = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=33.0,
        threshold_high=None,
        comparison="above"
    )
    logger.info(f"Result: {prob_above:.1%}")

    # Below
    logger.info("\nOperator: BELOW (temp < 33°F)")
    prob_below = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=33.0,
        threshold_high=None,
        comparison="below"
    )
    logger.info(f"Result: {prob_below:.1%}")
    logger.info(f"Check: above + below ≈ 100%? {prob_above + prob_below:.1%}")

    # Between
    logger.info("\nOperator: BETWEEN (30°F ≤ temp ≤ 35°F)")
    prob_between = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=30.0,
        threshold_high=35.0,
        comparison="between"
    )
    logger.info(f"Result: {prob_between:.1%}")


def test_with_observations():
    """Test NWS bias calculation with observations"""
    model = BoundaryForecastModel()

    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: NWS Bias from Observations")
    logger.info("=" * 80)

    forecast_value = 32.0
    threshold = 33.0

    # Recent observations consistently warmer than forecast
    observations = [
        {"timestamp": "2026-01-15T12:00:00Z", "temperature": 36.0},
        {"timestamp": "2026-01-15T11:00:00Z", "temperature": 35.5},
        {"timestamp": "2026-01-15T10:00:00Z", "temperature": 35.0},
        {"timestamp": "2026-01-15T09:00:00Z", "temperature": 34.5},
        {"timestamp": "2026-01-15T08:00:00Z", "temperature": 34.0},
        {"timestamp": "2026-01-15T07:00:00Z", "temperature": 33.5},
        {"timestamp": "2026-01-15T06:00:00Z", "temperature": 33.0},
        {"timestamp": "2026-01-15T05:00:00Z", "temperature": 32.5},
        {"timestamp": "2026-01-15T04:00:00Z", "temperature": 32.0},
        {"timestamp": "2026-01-15T03:00:00Z", "temperature": 31.5},
    ] * 3  # 30 observations

    logger.info("\nWith observations (recent temps warmer than forecast):")
    prob_with_obs = model.calculate_boundary_probability(
        forecast_value=forecast_value,
        threshold=threshold,
        threshold_high=None,
        comparison="above",
        observations=observations
    )
    logger.info(f"Result: P(temp ≥ 33°F) = {prob_with_obs:.1%}")
    logger.info("Expected: Higher probability (recent bias toward warmer)")


def test_real_world_scenario():
    """Test realistic scenario from Kalshi market"""
    model = BoundaryForecastModel()

    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Real-World Scenario")
    logger.info("=" * 80)

    # Example: KXLOWTDEN market
    # "Will the minimum temperature be ≥33°F on Jan 17, 2026?"
    # NWS forecast: 32°F minimum
    # Market price: 20% (YES)
    # Current: 35°F, clear skies, light winds

    logger.info("\nMarket: Will Denver minimum temp be ≥33°F?")
    logger.info("NWS forecast: 32°F")
    logger.info("Market price: 20% YES")
    logger.info("Current conditions: 35°F, clear skies, light winds")

    current_conditions = {
        "temperature": 35.0,
        "dewpoint": 18.0,  # Dry air
        "wind_speed": 4.0,  # Light winds
        "sky_cover": 15  # Clear
    }

    forecast_stats = {
        "avg_sky_cover": 15,
        "avg_wind_speed": 4.0,
        "avg_dewpoint": 18.0
    }

    prob = model.calculate_boundary_probability(
        forecast_value=32.0,
        threshold=33.0,
        threshold_high=None,
        comparison="above",
        current_conditions=current_conditions,
        forecast_stats=forecast_stats
    )

    logger.info(f"\nBoundary model probability: {prob:.1%}")
    logger.info(f"Market probability: 20%")
    logger.info(f"Edge: {prob - 0.20:+.1%}")

    if prob - 0.20 > 0.10:
        logger.info("✅ OPPORTUNITY: Significant mispricing detected!")
    else:
        logger.info("❌ Market is efficiently priced")


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("BOUNDARY FORECAST MODEL - TEST SUITE")
    logger.info("=" * 80)

    try:
        test_boundary_vs_simple()
        test_meteorological_adjustments()
        test_comparison_operators()
        test_with_observations()
        test_real_world_scenario()

        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL TESTS COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
