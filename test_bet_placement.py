#!/usr/bin/env python3
"""
Test Bet Placement
Places a small $2 test bet to verify Kalshi API integration works

Usage: python test_bet_placement.py
"""

import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from clients import KalshiHttpClient, Environment

load_dotenv()

print("=" * 80)
print("TEST BET PLACEMENT - $2 Test Bet")
print("=" * 80)

# Get credentials
env = Environment.PROD
KEYID = os.getenv('KALSHI_API_KEY_ID')
KEYFILE = os.getenv('KALSHI_PRIVATE_KEY_PATH')

if not KEYID or not KEYFILE:
    print("❌ Error: KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH must be set in .env")
    exit(1)

# Load private key
try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
    print(f"✅ Loaded private key from {KEYFILE}")
except FileNotFoundError:
    print(f"❌ Private key file not found: {KEYFILE}")
    exit(1)

# Initialize client
print(f"\n[1] Connecting to Kalshi API...")
client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)
print("✅ Connected successfully")

# Get balance
print(f"\n[2] Fetching account balance...")
balance_response = client.get_balance()
balance = balance_response.get('balance', 0) / 100
print(f"✅ Balance: ${balance:.2f}")

if balance < 2:
    print(f"❌ Insufficient balance. Need at least $2.00, have ${balance:.2f}")
    exit(1)

# Find open markets
print(f"\n[3] Finding test markets...")
markets_response = client.get(
    '/trade-api/v2/markets',
    params={
        'series_ticker': 'KXLOWTDEN',
        'status': 'open'
    }
)
markets = markets_response.get('markets', [])

if not markets:
    print("❌ No open markets found in KXLOWTDEN series")
    exit(1)

print(f"✅ Found {len(markets)} open markets")

# Pick first market
test_market = markets[0]
ticker = test_market['ticker']
title = test_market['title']
yes_bid = test_market.get('yes_bid', 0) / 100.0
no_bid = test_market.get('no_bid', 0) / 100.0

print(f"\n[4] Selected market:")
print(f"   Ticker: {ticker}")
print(f"   Title: {title}")
print(f"   YES bid: {yes_bid:.1%}")
print(f"   NO bid: {no_bid:.1%}")

# Determine side to bet (pick side with lower price for better odds)
if yes_bid <= no_bid and yes_bid > 0:
    side = "yes"
    price = yes_bid
else:
    side = "no"
    price = no_bid

# Calculate contracts for ~$2
count = max(1, int(2.00 / max(price, 0.01)))
estimated_cost = count * price

print(f"\n[5] PREPARING TEST BET:")
print(f"   Side: {side.upper()}")
print(f"   Contracts: {count}")
print(f"   Price: ${price:.2f} per contract")
print(f"   Estimated cost: ${estimated_cost:.2f}")
print(f"   Max payout: ${count:.2f}")

# Ask for confirmation
print("\n⚠️  This will place a REAL bet on Kalshi!")
response = input("Type 'YES' to place the test bet, or anything else to cancel: ")

if response.strip().upper() != "YES":
    print("❌ Bet cancelled by user")
    exit(0)

# Place order
print(f"\n[6] Placing order...")
order_response = client.post(
    '/trade-api/v2/portfolio/orders',
    body={
        'ticker': ticker,
        'action': 'buy',
        'side': side,
        'count': count,
        'type': 'market'
    }
)

order = order_response.get('order', {})

print("\n✅ ORDER PLACED SUCCESSFULLY!")
print(f"\nOrder Details:")
print(f"   Order ID: {order.get('order_id')}")
print(f"   Status: {order.get('status')}")
print(f"   Ticker: {order.get('ticker')}")
print(f"   Side: {order.get('side', '').upper()}")
print(f"   Count: {order.get('count')}")

if order.get('status') == 'executed':
    print(f"   ✅ Order executed immediately")
elif order.get('status') == 'resting':
    print(f"   ⏳ Order is resting (waiting for match)")

print("\n" + "=" * 80)
print("TEST SUCCESSFUL!")
print("Bet placement is working correctly.")
print("=" * 80)
