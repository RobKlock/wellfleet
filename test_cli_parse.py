#!/usr/bin/env python3
"""
Test parsing the CLI report HTML
"""
import requests
import re

def test_cli_parse():
    """Test parsing the CLI report"""

    url = "https://forecast.weather.gov/product.php"
    params = {
        "site": "NWS",
        "product": "CLI",
        "issuedby": "DEN"
    }

    response = requests.get(url, params=params, timeout=30)
    html = response.text

    # The CLI data is in the HTML, need to extract it
    # Look for the pre-formatted text block
    import re
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', html, re.DOTALL)

    if pre_match:
        text = pre_match.group(1)
        print("Found CLI text in <pre> tag:")
        print("=" * 80)
        print(text)
        print("=" * 80)
        print()

        # Now parse temperatures
        min_pattern = r"MINIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"
        max_pattern = r"MAXIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"

        min_match = re.search(min_pattern, text)
        max_match = re.search(max_pattern, text)

        if min_match:
            min_temp = float(min_match.group(1))
            min_time_raw = min_match.group(2)
            min_period = min_match.group(3)
            # Format time properly (e.g., "138" -> "1:38")
            if len(min_time_raw) == 3:
                min_time = f"{min_time_raw[0]}:{min_time_raw[1:]}"
            elif len(min_time_raw) == 4:
                min_time = f"{min_time_raw[:2]}:{min_time_raw[2:]}"
            else:
                min_time = min_time_raw
            print(f"✅ MIN: {min_temp}°F at {min_time} {min_period}")

        if max_match:
            max_temp = float(max_match.group(1))
            max_time_raw = max_match.group(2)
            max_period = max_match.group(3)
            if len(max_time_raw) == 3:
                max_time = f"{max_time_raw[0]}:{max_time_raw[1:]}"
            elif len(max_time_raw) == 4:
                max_time = f"{max_time_raw[:2]}:{max_time_raw[2:]}"
            else:
                max_time = max_time_raw
            print(f"✅ MAX: {max_temp}°F at {max_time} {max_period}")

    else:
        print("❌ Could not find <pre> tag in HTML")
        # Try searching in raw HTML
        min_pattern = r"MINIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"
        max_pattern = r"MAXIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"

        min_match = re.search(min_pattern, html)
        max_match = re.search(max_pattern, html)

        if min_match or max_match:
            print("✅ Found temperature data in raw HTML")
            if min_match:
                print(f"MIN: {min_match.group(1)}°F at {min_match.group(2)} {min_match.group(3)}")
            if max_match:
                print(f"MAX: {max_match.group(1)}°F at {max_match.group(2)} {max_match.group(3)}")

if __name__ == "__main__":
    test_cli_parse()
