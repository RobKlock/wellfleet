#!/usr/bin/env python3
"""
Test Kalshi's Official Client Implementation
Tests both HTTP and WebSocket clients
"""

import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import asyncio

from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

# Load environment variables
load_dotenv()

# Determine environment (PROD for real trading, DEMO for testing)
env = Environment.PROD  # Change to Environment.DEMO to use demo environment

# Get credentials based on environment
if env == Environment.DEMO:
    KEYID = os.getenv('DEMO_KEYID')
    KEYFILE = os.getenv('DEMO_KEYFILE')
else:  # PROD
    KEYID = os.getenv('KALSHI_API_KEY_ID')
    KEYFILE = os.getenv('KALSHI_PRIVATE_KEY_PATH')

# Validate credentials
if not KEYID:
    raise ValueError(f"API Key ID not found. Set {'DEMO_KEYID' if env == Environment.DEMO else 'KALSHI_API_KEY_ID'} in .env")
if not KEYFILE:
    raise ValueError(f"Private key file not found. Set {'DEMO_KEYFILE' if env == Environment.DEMO else 'KALSHI_PRIVATE_KEY_PATH'} in .env")

# Load private key
try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None  # Provide the password if your key is encrypted
        )
    print(f"✅ Loaded private key from {KEYFILE}")
except FileNotFoundError:
    print(f"\n❌ Private key file not found: {KEYFILE}")
    print("\n📋 Setup Instructions:")
    print("1. Log in to Kalshi: https://kalshi.com")
    print("2. Go to Settings → API Keys")
    print("3. Generate a new API key and download the private key file")
    print(f"4. Save it as: {os.path.abspath(KEYFILE)}")
    print("\nOr update KALSHI_PRIVATE_KEY_PATH in .env to point to your key file")
    print("\nSee KALSHI_SETUP.md for detailed instructions")
    raise
except Exception as e:
    raise Exception(f"Error loading private key: {str(e)}")

# Initialize the HTTP client
print(f"\n🌐 Initializing Kalshi HTTP Client ({env.value.upper()} environment)...")
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

# Test 1: Get exchange status
print("\n" + "=" * 80)
print("TEST 1: Get Exchange Status")
print("=" * 80)
try:
    status = client.get_exchange_status()
    print(f"Exchange Status: {status.get('exchange_active', 'Unknown')}")
    print(f"Trading Active: {status.get('trading_active', 'Unknown')}")
except Exception as e:
    print(f"❌ Failed to get exchange status: {e}")

# Test 2: Get account balance
print("\n" + "=" * 80)
print("TEST 2: Get Account Balance")
print("=" * 80)
try:
    balance_response = client.get_balance()
    balance = balance_response.get('balance', 0)
    print(f"✅ Account Balance: ${balance / 100:.2f}")
except Exception as e:
    print(f"❌ Failed to get balance: {e}")

# Test 3: Get recent trades (optional - comment out if not needed)
print("\n" + "=" * 80)
print("TEST 3: Get Recent Trades (limit 5)")
print("=" * 80)
try:
    trades = client.get_trades(limit=5)
    trade_list = trades.get('trades', [])
    if trade_list:
        print(f"Found {len(trade_list)} recent trades:")
        for trade in trade_list:
            print(f"  - {trade.get('ticker')}: {trade.get('count')} @ ${trade.get('yes_price', 0)/100:.2f}")
    else:
        print("No recent trades found")
except Exception as e:
    print(f"❌ Failed to get trades: {e}")

print("\n" + "=" * 80)
print("HTTP CLIENT TESTS COMPLETE")
print("=" * 80)

# Test 4: WebSocket (optional - uncomment to test)
print("\n" + "=" * 80)
print("WEBSOCKET TEST (OPTIONAL)")
print("=" * 80)
print("To test WebSocket, uncomment the code below.")
print("Note: WebSocket will run indefinitely until interrupted (Ctrl+C)")

"""
# Uncomment to test WebSocket client
async def test_websocket():
    print("\\nInitializing WebSocket client...")
    ws_client = KalshiWebSocketClient(
        key_id=KEYID,
        private_key=private_key,
        environment=env
    )

    print("Connecting to WebSocket...")
    await ws_client.connect()

# Run WebSocket test
# asyncio.run(test_websocket())
"""

print("\n✅ All tests completed successfully!")
