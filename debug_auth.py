#!/usr/bin/env python3
"""
Debug Authentication - Shows exactly what headers are being sent
"""

import os
import time
from dotenv import load_dotenv
from scanner import KalshiClient

load_dotenv()

# Patch the requests to show headers
import requests
original_request = requests.Session.request

def debug_request(self, method, url, **kwargs):
    print(f"\n{'='*80}")
    print(f"REQUEST: {method} {url}")
    print(f"{'='*80}")
    headers = kwargs.get('headers', {})
    for key, value in headers.items():
        if 'SIGNATURE' in key:
            print(f"{key}: {value[:50]}...{value[-20:]}")
        else:
            print(f"{key}: {value}")
    print(f"{'='*80}\n")
    return original_request(self, method, url, **kwargs)

requests.Session.request = debug_request

# Test the client
api_key_id = os.getenv("KALSHI_API_KEY_ID")
private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")

print("Creating KalshiClient...")
client = KalshiClient(api_key_id=api_key_id, private_key_path=private_key_path)

print("\nAttempting to get balance...")
try:
    balance = client.get_balance()
    print(f"\n✅ SUCCESS! Balance: ${balance.get('balance', 0) / 100:.2f}")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
