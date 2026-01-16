#!/usr/bin/env python3
"""Quick test to check what markets we can access"""

import os
import logging
from dotenv import load_dotenv
from scanner import KalshiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Get credentials
api_key_id = os.getenv("KALSHI_API_KEY_ID")
private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")
email = os.getenv("KALSHI_EMAIL")
password = os.getenv("KALSHI_PASSWORD")

# Initialize client
if api_key_id and os.path.exists(private_key_path):
    client = KalshiClient(api_key_id=api_key_id, private_key_path=private_key_path)
elif email and password:
    client = KalshiClient(email=email, password=password)
else:
    print("No credentials found!")
    exit(1)

# Try specific tickers
print("\n" + "="*60)
print("Testing specific market tickers:")
print("="*60)

for ticker in ["KXLOWTMIA-26JAN16", "KXLOWTDEN-26JAN16"]:
    try:
        print(f"\n{ticker}:")
        market = client.get_market(ticker)
        print(f"  Title: {market.get('title')}")
        print(f"  Status: {market.get('status')}")
        print(f"  YES: {market.get('yes_bid')}/{market.get('yes_ask')}")
        print(f"  Liquidity pool: {bool(market.get('liquidity_pool'))}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Check promo markets
print("\n" + "="*60)
print("Checking promo markets:")
print("="*60)

promo_markets = client.get_promo_markets()
print(f"Total promo markets: {len(promo_markets)}")

# Look for temperature/weather
weather = [m for m in promo_markets if 'temp' in m['title'].lower() or 'weather' in m['title'].lower()]
print(f"Weather-related promo markets: {len(weather)}")

if weather:
    print("\nFirst 5 weather promo markets:")
    for m in weather[:5]:
        print(f"  {m['ticker']}: {m['title'][:70]}")

# Look for Denver/Miami
denver_miami = [m for m in promo_markets if 'denver' in m['title'].lower() or 'miami' in m['title'].lower()]
print(f"\nDenver/Miami promo markets: {len(denver_miami)}")

if denver_miami:
    for m in denver_miami:
        print(f"  {m['ticker']}: {m['title'][:70]}")
else:
    print("  None found in promo markets!")

print("\n" + "="*60)
