# Kalshi API Key Setup Guide

## Getting Your API Key

1. Log into your Kalshi account
2. Go to Settings → API Keys
3. Click "Create New API Key"
4. Save the **Key ID** and **Private Key** shown (you'll only see them once!)

## Setting Up Authentication

### Step 1: Add API Key ID to .env

Edit your `.env` file and add:

```bash
KALSHI_API_KEY_ID=your-actual-key-id-here
```

### Step 2: Save Private Key

Copy the entire private key (including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines) and save it to a file named `kalshi_api_private_key.txt` in the project root.

The file should look like:
```
-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC...
(many lines of random characters)
...
-----END PRIVATE KEY-----
```

### Step 3: Verify Security

Make sure your private key file is protected:

```bash
# Check that .gitignore includes the private key
cat .gitignore | grep kalshi_api_private_key.txt
# Should output: kalshi_api_private_key.txt

# Verify git won't track it
git status
# .env and kalshi_api_private_key.txt should NOT appear

# Optional: Set file permissions (Linux/Mac)
chmod 600 kalshi_api_private_key.txt
```

### Step 4: Test the Connection

Run the test script to verify everything works:

```bash
python3 test_core_components.py
```

You should see output like:
```
Testing KalshiClient
Using API key authentication
✓ Authenticated successfully using api_key
```

## Troubleshooting

### "No module named '_cffi_backend'"
Install the required dependency:
```bash
python3 -m pip install --ignore-installed --user cffi cryptography
```

### "Failed to load private key"
- Make sure the file `kalshi_api_private_key.txt` exists
- Check that it contains the full private key including header/footer lines
- Verify the file path in .env (if you used a different name)

### "Authentication failed"
- Double-check your API Key ID is correct in .env
- Verify the private key file hasn't been modified
- Make sure the API key is still active in your Kalshi account

## Security Notes

✅ **Safe** - These files are in .gitignore and won't be committed:
- `.env`
- `kalshi_api_private_key.txt`

❌ **Never** commit these to git or share publicly!

## Alternative: Email/Password (Legacy)

If you prefer, you can still use email/password authentication:

```bash
# In .env
KALSHI_EMAIL=your-email@example.com
KALSHI_PASSWORD=your-password
```

But API keys are more secure and recommended by Kalshi.
