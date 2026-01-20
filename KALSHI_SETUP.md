# Kalshi API Setup Guide

## Quick Setup

### 1. Get Your API Credentials

1. Log in to Kalshi: https://kalshi.com
2. Go to Settings → API Keys
3. Generate a new API key
4. Download the private key file (it will be a `.txt` or `.pem` file)
5. Copy your API Key ID (looks like: `1304e7e4-75e2-4ae2-88fd-35d45d57e14b`)

### 2. Add Private Key to Project

Save your downloaded private key file as:
```
/home/user/wellfleet/kalshi_api_private_key.txt
```

Or update `.env` to point to wherever you saved it:
```bash
KALSHI_PRIVATE_KEY_PATH=/path/to/your/kalshi_private_key.txt
```

### 3. Update .env File

The `.env` file should already have your API Key ID set:
```bash
KALSHI_API_KEY_ID=1304e7e4-75e2-4ae2-88fd-35d45d57e14b
KALSHI_PRIVATE_KEY_PATH=kalshi_api_private_key.txt
```

### 4. Test Your Setup

Run the official client test:
```bash
python test_kalshi_official.py
```

Or run the signature test:
```bash
python test_signature.py
```

## Environment Options

### Production (Real Money)
```bash
env = Environment.PROD
```
Uses: `KALSHI_API_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH`

### Demo (Paper Trading)
```bash
env = Environment.DEMO
```
Uses: `DEMO_KEYID` and `DEMO_KEYFILE`

## Troubleshooting

### FileNotFoundError: kalshi_api_private_key.txt
- Make sure you've downloaded your private key from Kalshi
- Save it to the project directory
- Or update `KALSHI_PRIVATE_KEY_PATH` in `.env` with the full path

### 401 Unauthorized
- Verify your API Key ID is correct
- Make sure the private key matches the API key
- Check that you're using the right environment (PROD vs DEMO)

### ImportError: websockets
```bash
pip install websockets
```

## File Structure

```
wellfleet/
├── .env                          # Your credentials (DO NOT COMMIT)
├── kalshi_api_private_key.txt   # Your private key (DO NOT COMMIT)
├── clients.py                    # Kalshi official client
├── test_kalshi_official.py      # Test script
└── scanner/
    └── kalshi_client.py         # Scanner integration
```

## Security Notes

- **NEVER** commit your `.env` file or private key to git
- Keep your API credentials secure
- Use demo environment for testing
- Production environment uses real money
