# Kalshi Weather Arbitrage Scanner

A Python-based scanner that identifies mispriced weather markets on Kalshi by comparing market prices against authoritative NWS forecast data.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Kalshi credentials
```

4. Run the scanner:
```bash
python scan.py
```

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

## Features

- Fetches markets with liquidity promotions from Kalshi
- Retrieves weather forecasts from National Weather Service API
- Parses market titles to extract temperature thresholds
- Calculates true probabilities based on forecast data
- Identifies mispricings with significant edge
- Generates detailed reports in Markdown and CSV formats

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## License

MIT
