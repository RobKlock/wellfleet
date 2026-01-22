#!/usr/bin/env python3
"""
Test fetching preliminary CLI report
"""
import requests
from datetime import datetime

def test_cli_fetch():
    """Test fetching the preliminary CLI report for Denver"""

    # URL format from user's working example
    url = "https://forecast.weather.gov/product.php"
    params = {
        "site": "NWS",
        "product": "CLI",
        "issuedby": "DEN"
    }

    print("Testing CLI report fetch...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ CLI report fetched successfully!")
            print()

            # Parse the temperature section
            text = response.text

            # Look for temperature data
            import re

            # Pattern: "MINIMUM         13    138 AM -14    1962  19     -6       16"
            min_pattern = r"MINIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"
            max_pattern = r"MAXIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"

            min_match = re.search(min_pattern, text)
            max_match = re.search(max_pattern, text)

            if min_match:
                min_temp = float(min_match.group(1))
                min_time = f"{min_match.group(2)} {min_match.group(3)}"
                print(f"✅ Parsed MIN: {min_temp}°F at {min_time}")
            else:
                print("❌ Could not parse minimum temperature")

            if max_match:
                max_temp = float(max_match.group(1))
                max_time = f"{max_match.group(2)} {max_match.group(3)}"
                print(f"✅ Parsed MAX: {max_temp}°F at {max_time}")
            else:
                print("❌ Could not parse maximum temperature")

            print()
            print("First 1000 characters of report:")
            print("=" * 60)
            print(text[:1000])
            print("=" * 60)

        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cli_fetch()
