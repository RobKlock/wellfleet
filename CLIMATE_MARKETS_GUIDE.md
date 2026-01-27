# Climate Markets Scanner - Expanded Support Guide

## Overview

The Kalshi Weather Scanner has been expanded to support **all climate markets** across the United States, not just Denver and Miami. The system now dynamically discovers and analyzes temperature markets for any supported city.

## What's New

### 1. **100+ US Cities Supported**

The scanner now supports weather forecasts for over 100 major US cities including:
- All major metropolitan areas (NYC, LA, Chicago, Houston, etc.)
- State capitals
- Major regional hubs
- Alaska and Hawaii

See `scanner/city_config.py` for the complete list of supported cities.

### 2. **Dynamic Location Discovery**

Instead of hardcoding specific cities, the scanner now:
- Automatically detects climate markets for any location in market titles
- Matches city abbreviations (DEN, MIA, PHX, etc.) to full city names
- Handles various city name formats (e.g., "Denver", "Denver, CO", "DEN")

### 3. **Overnight Scanning**

New `scan_overnight.py` script for automated overnight scanning:
- Runs during configurable hours (default: 8pm - 8am)
- Scans at regular intervals (default: every 2 hours)
- Takes advantage of overnight market timing opportunities
- Generates timestamped reports for each scan
- Includes retry logic for API failures

### 4. **Improved Reporting**

Reports now:
- Dynamically list all locations with opportunities
- Show comprehensive climate market coverage
- Include timestamped reports for tracking overnight scans

## Usage

### Quick Scan (All Climate Markets)

Scan all promo markets for temperature opportunities:

```bash
python scan.py
```

This will now scan **all climate markets**, not just Denver/Miami.

### Overnight Scanning

Run continuous overnight scanning:

```bash
python scan_overnight.py
```

Configuration via environment variables:

```bash
# Scan every 90 minutes (default: 120)
export SCAN_INTERVAL_MINUTES=90

# Run from 10pm to 6am (default: 8pm to 8am)
export OVERNIGHT_START_HOUR=22
export OVERNIGHT_END_HOUR=6

# Custom reports directory (default: ./reports)
export REPORTS_DIR=/path/to/reports

python scan_overnight.py
```

### Series Scanning

Scan specific series (e.g., all Denver low temp markets):

```bash
# Scan any series ticker
python scan_series.py KXLOWTPHX KXLOWTNYC KXLOWTCHI
```

### Specific Market Scanning

Scan specific market tickers:

```bash
# Works with any city's markets
python scan_specific.py KXLOWTPHX-27JAN20 KXLOWTNYC-27JAN18
```

## City Configuration

### Supported Cities

The scanner includes comprehensive data for 100+ US cities. Each city has:
- Latitude/longitude coordinates
- Timezone information
- NWS weather station ID
- Common abbreviations (3-letter codes, full names, etc.)

### Adding New Cities

To add support for additional cities, edit `scanner/city_config.py`:

1. Add entry to `CITY_DATABASE`:
```python
"City Name, ST": {
    "lat": latitude,
    "lon": longitude,
    "timezone": "America/Timezone",
    "station_id": "KXXX"  # Airport code or NWS station
}
```

2. Add abbreviations to `CITY_ABBREVIATIONS`:
```python
"ABC": "City Name, ST",
"CITYNAME": "City Name, ST",
```

## How It Works

### 1. Market Discovery

The scanner fetches all promo markets from Kalshi and filters for temperature/weather markets:

```python
# Now scans ALL climate markets
opportunities = scanner.scan(mode="promo")
```

### 2. Location Parsing

The `MarketParser` extracts location from market titles:
- Full format: "Will the minimum temperature in Phoenix, AZ be..."
- Compact format: Infers location from ticker (e.g., KXLOWTPHX → Phoenix, AZ)

### 3. Weather Data Lookup

The `NWSAdapter` fetches forecasts for any supported city:
```python
# Dynamically supports 100+ cities
forecast = nws.get_forecast_for_city("Phoenix", "AZ")
stats = nws.extract_temperature_stats_for_date(forecast, target_date, timezone)
```

### 4. Opportunity Detection

The `MispricingDetector` compares market prices to weather forecasts for all locations.

## Overnight Strategy

The overnight scanner is optimized for timing advantages:

### Why Run Overnight?

1. **Less Competition**: Fewer traders active during overnight hours
2. **Weather Updates**: NWS forecasts update regularly, including overnight
3. **Market Inefficiency**: Markets may not immediately reflect latest forecasts
4. **Global Events**: Overnight weather system changes can create opportunities

### Timing Recommendations

- **Scan Frequency**: 1-3 hours (balance between freshness and API limits)
- **Start Time**: After evening forecast updates (typically 6-8pm local)
- **End Time**: Before morning trading rush (6-8am local)

### Best Practices

1. **Monitor Multiple Scans**: Track how opportunities evolve overnight
2. **Compare Reports**: Look for consistent edges across multiple scans
3. **Act on High-Confidence**: Focus on opportunities with >70% confidence
4. **Check Liquidity**: Ensure adequate liquidity pool size before betting

## Example Overnight Workflow

1. **Setup** (Evening):
```bash
# Configure overnight scanning
export SCAN_INTERVAL_MINUTES=120
export OVERNIGHT_START_HOUR=20
export OVERNIGHT_END_HOUR=7

# Start overnight scanner
python scan_overnight.py &
```

2. **Monitoring** (Morning):
```bash
# Check all overnight reports
ls -lh reports/scan_report_*.md

# Review the most recent scan
cat reports/scan_report_$(ls -t reports/ | head -1)
```

3. **Analysis**:
- Compare opportunities across multiple scans
- Look for persistent edges (appear in multiple scans)
- Verify NWS forecast hasn't changed significantly
- Check market liquidity before placing bets

## Troubleshooting

### "Unsupported location" Error

If you see this error, the city isn't in the database yet. Add it to `scanner/city_config.py`.

### No Markets Found

- Check that promo markets are available on Kalshi
- Verify authentication credentials are correct
- Check scanner logs for API errors

### Overnight Scanner Not Running

- Verify you're within configured hours (`OVERNIGHT_START_HOUR` to `OVERNIGHT_END_HOUR`)
- Check log file: `reports/overnight_scanner.log`
- Ensure Kalshi API credentials are valid

## Monitoring & Alerts

### Log Files

All scans are logged to:
- Console output (real-time)
- `reports/overnight_scanner.log` (persistent log)

### Report Generation

Each scan generates a timestamped Markdown report:
- Format: `scan_report_YYYYMMDD_HHMMSS.md`
- Location: `reports/` directory
- Includes: All opportunities, forecasts, market data

### Integration Ideas

The overnight scanner can be integrated with:
- Cron jobs for scheduled execution
- Email notifications (add SMTP to script)
- Telegram/Discord bots for alerts
- Database storage for historical tracking

## Performance Considerations

### API Rate Limits

- **NWS API**: No official rate limit, but be respectful
- **Kalshi API**: Rate limits apply (check Kalshi documentation)
- **Recommendation**: 1-3 hour scan intervals to avoid issues

### Resource Usage

- CPU: Minimal (mostly I/O waiting for API responses)
- Memory: ~100-200MB per scan
- Network: ~1-5MB data per scan
- Disk: ~10KB per report

### Optimization Tips

1. **Longer Intervals**: 2-3 hours during slow periods
2. **Shorter Intervals**: 1 hour during high volatility (storms, cold snaps)
3. **Selective Scanning**: Use series/specific modes for targeted analysis

## Next Steps

1. **Run Your First Overnight Scan**:
   ```bash
   python scan_overnight.py
   ```

2. **Review Results in the Morning**:
   ```bash
   ls -lht reports/scan_report_*.md | head -5
   ```

3. **Analyze Opportunities**:
   - Look for persistent edges
   - Verify forecasts on weather.gov
   - Check market liquidity on Kalshi
   - Place bets during optimal times

4. **Iterate and Improve**:
   - Adjust scan intervals based on results
   - Add new cities as Kalshi expands markets
   - Track ROI and refine edge thresholds

## Support

For issues or questions:
- Check logs: `reports/overnight_scanner.log`
- Review code: `scanner/` directory
- Test components: `python test_core_components.py`

---

**Happy scanning! May your overnight edges be ever in your favor! 🌙📊**
