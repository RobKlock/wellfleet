#!/usr/bin/env python3
"""
Test Kalshi API Signature Generation
Shows you how to create the signature headers locally
"""

import os
import time
import json
import base64
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

load_dotenv()

# 1. LOAD YOUR PRIVATE KEY
print("=" * 80)
print("STEP 1: Load Private Key")
print("=" * 80)

private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")
api_key_id = os.getenv("KALSHI_API_KEY_ID")

print(f"Private key path: {private_key_path}")
print(f"API Key ID: {api_key_id}")

with open(private_key_path, 'rb') as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None
    )
print("✅ Private key loaded\n")

# 2. GENERATE TIMESTAMP
print("=" * 80)
print("STEP 2: Generate Timestamp (milliseconds)")
print("=" * 80)

timestamp = str(int(time.time() * 1000))
print(f"KALSHI-ACCESS-TIMESTAMP: {timestamp}\n")

# 3. CREATE THE MESSAGE TO SIGN
print("=" * 80)
print("STEP 3: Create Message to Sign")
print("=" * 80)

# Example: GET /portfolio/balance
method = "GET"
path = "/portfolio/balance"

# Remove query parameters from path (per Kalshi API spec)
path_without_query = path.split('?')[0]

# Message format: timestamp + method + path
# NOTE: JSON body is NOT included in signature (even for POST/PUT)
message = f"{timestamp}{method}{path_without_query}"

print(f"Message: '{message}'")
print(f"\nBreakdown:")
print(f"  - Timestamp: {timestamp}")
print(f"  - Method: {method}")
print(f"  - Path: {path_without_query}")
print()
print("IMPORTANT: Per Kalshi's official API implementation:")
print("  - Query parameters are stripped from path before signing")
print("  - JSON body is NOT included in signature (even for POST/PUT)")
print()

# 4. SIGN THE MESSAGE
print("=" * 80)
print("STEP 4: Sign with RSA-PSS")
print("=" * 80)

signature = private_key.sign(
    message.encode('utf-8'),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.DIGEST_LENGTH
    ),
    hashes.SHA256()
)

# Base64 encode the signature
signature_b64 = base64.b64encode(signature).decode('utf-8')

print(f"KALSHI-ACCESS-SIGNATURE: {signature_b64}\n")

# 5. SHOW COMPLETE HEADERS
print("=" * 80)
print("COMPLETE HEADERS TO USE:")
print("=" * 80)
print(f"KALSHI-ACCESS-KEY: {api_key_id}")
print(f"KALSHI-ACCESS-TIMESTAMP: {timestamp}")
print(f"KALSHI-ACCESS-SIGNATURE: {signature_b64}\n")

# 6. TEST WITH CURL
print("=" * 80)
print("TEST WITH CURL:")
print("=" * 80)
print(f"""curl --request GET \\
  --url https://api.elections.kalshi.com/trade-api/v2/portfolio/balance \\
  --header 'KALSHI-ACCESS-KEY: {api_key_id}' \\
  --header 'KALSHI-ACCESS-TIMESTAMP: {timestamp}' \\
  --header 'KALSHI-ACCESS-SIGNATURE: {signature_b64}'
""")

# 7. TEST WITH PYTHON REQUESTS
print("=" * 80)
print("TESTING WITH PYTHON REQUESTS:")
print("=" * 80)

import requests

url = "https://api.elections.kalshi.com/trade-api/v2/portfolio/balance"
headers = {
    'KALSHI-ACCESS-KEY': api_key_id,
    'KALSHI-ACCESS-TIMESTAMP': timestamp,
    'KALSHI-ACCESS-SIGNATURE': signature_b64
}

print(f"Sending GET request to {url}...\n")

response = requests.get(url, headers=headers, timeout=30)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS!\n")
    data = response.json()
    print(json.dumps(data, indent=2))
    print(f"\nYour balance: ${data.get('balance', 0) / 100:.2f}")
elif response.status_code == 401:
    print("❌ UNAUTHORIZED - Signature failed\n")
    print("Possible issues:")
    print("  1. Wrong API key ID")
    print("  2. Wrong private key")
    print("  3. Clock skew (timestamp too old)")
    print(f"\nResponse: {response.text}")
else:
    print(f"❌ Error: {response.status_code}\n")
    print(response.text)
