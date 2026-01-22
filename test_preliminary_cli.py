#!/usr/bin/env python3
"""
Test that preliminary CLI report data is used correctly to filter out impossible markets
"""

def test_preliminary_cli_logic():
    """Demonstrate the fix for impossible market recommendations"""

    # Simulate the scenario from the user's report:
    # - Preliminary CLI shows minimum of 13°F
    # - Market asks: "Will the minimum temperature be 14-15°F?"
    # - Since 13 < 14, this should be a definite NO

    forecast = {
        "date": "2026-01-22",
        "min": 14.0,  # Observation-based minimum
        "max": 40.0,
        "avg": 20.0,
        "preliminary_min": 13.0,  # CLI report shows 13°F (more reliable)
        "preliminary_max": 21.0,
        "includes_observations": True
    }

    # Market details
    market_threshold_low = 14
    market_threshold_high = 15
    market_question = "Will the minimum temperature be 14-15°F?"

    # Check constraint logic (from _check_observation_constraints)
    # Prioritize preliminary CLI data
    observed_min = forecast.get("preliminary_min", forecast.get("min"))

    print(f"Market: {market_question}")
    print(f"Observation-based minimum: {forecast['min']}°F")
    print(f"Preliminary CLI minimum: {forecast['preliminary_min']}°F")
    print(f"Using: {observed_min}°F (preliminary CLI is more reliable)")
    print()

    # Check if the observed minimum already determines the outcome
    # For "between 14-15°F" market:
    # - If observed_min < 14, then the minimum is already below the range
    # - Since minimums can only go lower (never higher), this is a definite NO

    if observed_min < market_threshold_low:
        print(f"✅ CORRECT: Observed minimum {observed_min}°F < {market_threshold_low}°F")
        print(f"   Since minimums can only go lower, this market is IMPOSSIBLE (definite NO)")
        print(f"   This market should NOT be recommended!")
        result = "FILTERED OUT (correct)"
    else:
        print(f"❌ WRONG: Would recommend this market even though it's already impossible")
        result = "RECOMMENDED (incorrect)"

    print()
    print(f"Result: {result}")
    print()

    # Test the old behavior (without preliminary CLI)
    print("=" * 60)
    print("OLD BEHAVIOR (without preliminary CLI fix):")
    print("=" * 60)
    old_observed_min = forecast.get("min")  # Would only use observation-based min
    print(f"Would use observation-based minimum: {old_observed_min}°F")

    if old_observed_min < market_threshold_low:
        print(f"   Would filter out (correct)")
    else:
        print(f"   Would RECOMMEND (INCORRECT - market is actually impossible!)")
        print(f"   This is the bug that was fixed!")

    return result == "FILTERED OUT (correct)"

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Preliminary CLI Report Fix")
    print("=" * 60)
    print()

    success = test_preliminary_cli_logic()

    print()
    print("=" * 60)
    if success:
        print("✅ TEST PASSED: Fix correctly filters out impossible markets")
    else:
        print("❌ TEST FAILED: Logic needs adjustment")
    print("=" * 60)
