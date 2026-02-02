# Kalshi Weather Arbitrage Scanner

A Python-based scanner that identifies mispriced weather markets on Kalshi by comparing market prices against authoritative NWS forecast data.

**NEW**: Now supports **100+ US cities** with overnight scanning capabilities! See [CLIMATE_MARKETS_GUIDE.md](CLIMATE_MARKETS_GUIDE.md) for details.

## Core Thesis

Kalshi liquidity promotion participants optimize for volume rebates rather than accuracy, creating systematic mispricings that can be exploited by checking actual NWS data.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure Kalshi API credentials** (see [KALSHI_API_SETUP.md](KALSHI_API_SETUP.md)):
```bash
# Add to .env:
KALSHI_API_KEY_ID=your-key-id
# Save private key to kalshi_api_private_key.txt
```

3. **Run the scanner:**
```bash
python scan.py
```

4. **Check results:**
```bash
cat reports/current.md
```

## How It Works

1. **Fetches** markets with liquidity promotions from Kalshi API
2. **Filters** for temperature/weather markets (all US cities supported)
3. **Retrieves** authoritative forecasts from National Weather Service (100+ cities)
4. **Parses** market titles to extract thresholds and conditions
5. **Calculates** true probabilities based on NWS forecasts
6. **Detects** mispricings where market price differs significantly from forecast
7. **Generates** detailed reports with recommended bet sizes (using Kelly criterion)

## Features

- **100+ US Cities**: Supports all major metropolitan areas, state capitals, and regional hubs
- **Overnight Scanning**: Automated scanning during configured hours (e.g., 8pm-8am)
- **Dynamic Location Discovery**: Automatically detects and handles any climate market location
- **Comprehensive Coverage**: No longer limited to Denver/Miami - scans ALL climate markets
- **Timing Optimization**: Takes advantage of overnight market inefficiencies

## Project Structure

```
kalshi-weather-scanner/
├── .env                      # Environment variables (gitignored)
├── .gitignore
├── README.md
├── requirements.txt
├── scan.py                   # Main entry point
├── scanner/
│   ├── __init__.py
│   ├── kalshi_client.py      # Kalshi API client
│   ├── nws_adapter.py        # NWS data adapter
│   ├── market_parser.py      # Market title parser
│   ├── mispricing_detector.py # Arbitrage detection logic
│   ├── report_generator.py   # Report formatting
│   └── main.py               # KalshiWeatherScanner orchestrator
├── reports/                  # Generated reports (gitignored)
└── tests/                    # Test files
```

## Configuration

Edit `.env` to customize scanner behavior:

```bash
# Authentication (see KALSHI_API_SETUP.md)
KALSHI_API_KEY_ID=your-key-id
KALSHI_PRIVATE_KEY_PATH=kalshi_api_private_key.txt

# Scanner settings
BANKROLL=1000              # Total capital available ($)
KELLY_FRACTION=0.25        # Bet sizing (0.25 = 1/4 Kelly, conservative)
MIN_EDGE_THRESHOLD=0.20    # Minimum edge to flag (20% = significant mispricing)
```

## Output

The scanner generates three types of reports in `./reports/`:

### 1. Markdown Report (`current.md`)
Human-readable summary with:
- Forecast data (min/max/avg temperatures)
- Market prices (YES/NO bids)
- Analysis (true probability, edge, confidence)
- Recommendations (side to bet, suggested size)
- Reasoning (why the opportunity exists)

### 2. CSV Export (`kalshi_opportunities_YYYYMMDD_HHMMSS.csv`)
Spreadsheet-compatible format for tracking and analysis

### 3. Log File (`kalshi_scanner.log`)
Detailed execution log for debugging

## Example Output

```
Found 3 opportunities | Total edge: 215.0% | Recommended total bet: $42.50
Best: WEATHER-DENVER-MIN-31 (+95.0% edge, YES)

Top opportunities:
  1. WEATHER-DENVER-MIN-31: +95.0% edge, bet YES $18.75
  2. WEATHER-MIAMI-MAX-85: +70.0% edge, bet NO $15.00
  3. WEATHER-DENVER-AVG-40: +50.0% edge, bet YES $8.75
```

## Components

- **KalshiClient**: API integration with RSA-PSS signature authentication
- **NWSAdapter**: National Weather Service forecast retrieval
- **MarketParser**: Regex-based market title parsing
- **MispricingDetector**: Probability calculation and edge detection
- **ReportGenerator**: Markdown and CSV formatting
- **KalshiWeatherScanner**: Main orchestrator

## Testing

Run component tests:
```bash
python test_core_components.py
```

Expected output:
```
PARSER          ✓ PASSED
NWS             ✓ PASSED
KALSHI          ✓ PASSED
```

## Scheduling

Run automatically every 2 hours during market hours:

```bash
# Add to crontab (crontab -e)
0 9-18/2 * * * cd /path/to/wellfleet && python3 scan.py
```

## Security Notes

✅ **Protected files** (in .gitignore):
- `.env` - Configuration
- `kalshi_api_private_key.txt` - API private key
- `reports/` - Generated reports
- `*.log` - Log files

❌ **Never commit**:
- API credentials
- Private keys
- Real .env file

See [KALSHI_API_SETUP.md](KALSHI_API_SETUP.md) for security best practices.

## License

MIT
