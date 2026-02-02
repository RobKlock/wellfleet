"""
Main Scanner Orchestrator
Coordinates all components to scan for weather arbitrage opportunities
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .kalshi_client import KalshiClient
from .nws_adapter import NWSAdapter
from .market_parser import MarketParser
from .mispricing_detector import MispricingDetector, Opportunity
from .report_generator import ReportGenerator


class KalshiWeatherScanner:
    """Main orchestrator for the Kalshi weather arbitrage scanner"""

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key_id: Optional[str] = None,
        private_key_path: Optional[str] = None,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.25,
        min_edge_threshold: float = 0.20
    ):
        """
        Initialize the scanner with all components

        Args:
            email: Kalshi account email (for email/password auth)
            password: Kalshi account password (for email/password auth)
            api_key_id: API key ID (for API key auth)
            private_key_path: Path to private key file (for API key auth)
            bankroll: Total capital available for betting
            kelly_fraction: Fraction of Kelly criterion to use
            min_edge_threshold: Minimum edge required to flag opportunities
        """
        # Initialize components
        self.kalshi = KalshiClient(
            email=email,
            password=password,
            api_key_id=api_key_id,
            private_key_path=private_key_path
        )
        self.nws = NWSAdapter()
        self.parser = MarketParser()
        self.detector = MispricingDetector(
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            min_edge_threshold=min_edge_threshold
        )
        self.reporter = ReportGenerator()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def scan(
        self,
        specific_tickers: Optional[List[str]] = None,
        series_tickers: Optional[List[str]] = None
    ) -> List[Opportunity]:
        """
        Main scanning process

        Args:
            specific_tickers: Optional list of specific market tickers to scan
            series_tickers: Optional list of series tickers to scan (e.g., KXLOWTDEN)

        Returns:
            List of identified opportunities
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Kalshi Weather Scanner")
        self.logger.info("=" * 60)

        # Determine which fetching method to use
        if series_tickers:
            self.logger.info(f"Scanning {len(series_tickers)} series...")
            weather_markets = self._fetch_markets_from_series(series_tickers)
        elif specific_tickers:
            self.logger.info(f"Scanning {len(specific_tickers)} specific markets...")
            weather_markets = self._fetch_specific_markets(specific_tickers)
        else:
            # Step 1: Fetch promo markets
            self.logger.info("Fetching promo markets from Kalshi...")
            promo_markets = self.kalshi.get_promo_markets()
            self.logger.info(f"Found {len(promo_markets)} promo markets")

            # Step 2: Filter for weather markets in Denver/Miami
            weather_markets = self._filter_weather_markets(promo_markets)
            self.logger.info(f"Found {len(weather_markets)} weather markets for Denver/Miami")

        if not weather_markets:
            self.logger.warning("No weather markets found. Scan complete.")
            return []

        # Step 3: Analyze each market
        opportunities = []

        for market in weather_markets:
            self.logger.info("\n")
            self.logger.info("-"*100)
            self.logger.info(f"Analyzing: {market['title'][:80]}...")

            try:
                # Parse market
                parsed = self.parser.parse(market["title"], market["ticker"])

                if not parsed.is_parseable:
                    self.logger.warning(f"  ⚠ Could not parse market: {market['ticker']}")
                    continue

                self.logger.info(
                    f"  ✓ Parsed: {parsed.location}, {parsed.metric} "
                    f"{parsed.comparison} {parsed.threshold}°F on {parsed.date}"
                )

                # Get NWS forecast
                city, state = self._parse_location(parsed.location)
                if not city or not state:
                    self.logger.warning(f"  ⚠ Could not parse location: {parsed.location}")
                    continue

                forecast_periods = self.nws.get_forecast_for_city(city, state)

                # Get current conditions and observations FIRST (needed for today's actual temps)
                current_conditions = None
                observations = None
                preliminary_report = None

                location_info = self.nws.LOCATIONS.get(parsed.location)
                if location_info and "station_id" in location_info:
                    station_id = location_info["station_id"]
                    timezone = location_info["timezone"]

                    try:
                        # Fetch current conditions
                        current_conditions = self.nws.get_current_conditions(station_id)

                        # Fetch recent observations (last 200 = ~24-48 hours of hourly data)
                        # Critical for today's markets - gives us actual temps from earlier today
                        # Need enough observations to capture overnight lows/highs
                        observations = self.nws.get_observations(station_id)

                        if current_conditions:
                            self.logger.info(
                                f"  ✓ Current: {current_conditions['temperature']:.1f}°F, "
                                f"wind={current_conditions['wind_speed']:.1f}mph, "
                                f"sky={current_conditions['sky_cover']}%"
                            )
                    except Exception as e:
                        self.logger.warning(f"  ⚠ Could not fetch current conditions: {e}")

                    # Fetch preliminary CLI report for today's markets
                    # This is more reliable than individual observations due to quality control
                    if parsed.date.isoformat() == datetime.now(pytz.timezone(timezone)).date().isoformat():
                        try:
                            preliminary_report = self.nws.get_preliminary_climate_report(
                                station_id=station_id,
                                date_str=parsed.date.isoformat()
                            )
                            if preliminary_report:
                                self.logger.info(
                                    f"  ✓ Preliminary CLI: "
                                    f"MIN={preliminary_report.get('preliminary_min', 'N/A')}°F, "
                                    f"MAX={preliminary_report.get('preliminary_max', 'N/A')}°F"
                                )
                        except Exception as e:
                            self.logger.warning(f"  ⚠ Could not fetch preliminary CLI: {e}")

                # Extract stats for target date with meteorological data
                # Pass observations so we include actual temps from earlier today (if target_date is today)
                # Also pass preliminary CLI report if available (more reliable than observations)
                timezone = self.nws.LOCATIONS[parsed.location]["timezone"]
                forecast = self.nws.extract_temperature_stats_for_date(
                    forecast_periods,
                    parsed.date.isoformat(),
                    timezone,
                    include_meteorology=True,  # Include sky cover, wind, dewpoint
                    observations=observations,  # Include actual observations for today
                    preliminary_report=preliminary_report  # Include preliminary CLI report
                )

                if not forecast:
                    self.logger.warning(f"  ⚠ No forecast data available for {parsed.date}")
                    continue

                self.logger.info(
                    f"  ✓ Forecast: min={forecast['min']:.1f}°F, "
                    f"max={forecast['max']:.1f}°F, avg={forecast['avg']:.1f}°F"
                )

                # Check for leading indicator insights (e.g., Cheyenne → Denver)
                leading_indicator_insights = None
                if location_info and "station_id" in location_info:
                    try:
                        leading_indicator_insights = self.nws.get_leading_indicator_insights(
                            target_station_id=station_id,
                            target_city_state=parsed.location
                        )

                        if leading_indicator_insights and leading_indicator_insights.get("has_leading_indicators"):
                            recommendation = leading_indicator_insights.get("recommendation")
                            if recommendation != "no_change":
                                insights = leading_indicator_insights.get("insights", [])
                                if insights:
                                    primary = insights[0]
                                    self.logger.info(
                                        f"  🌡️ Leading indicator {primary['station_id']}: "
                                        f"{primary['trend']} at {primary['rate_per_hour']:+.1f}°F/hr "
                                        f"→ {recommendation.replace('_', ' ')}"
                                    )
                    except Exception as e:
                        self.logger.warning(f"  ⚠ Could not fetch leading indicators: {e}")

                # Detect mispricing
                opp = self.detector.analyze_temperature_market(
                    market,
                    parsed,
                    forecast,
                    current_conditions=current_conditions,
                    observations=observations,
                    leading_indicator_insights=leading_indicator_insights
                )

                if opp:
                    opportunities.append(opp)
                    self.logger.info(
                        f"  🎯 OPPORTUNITY: {opp.edge:+.1%} edge, "
                        f"bet {opp.recommended_side} for ${opp.recommended_bet_size:.2f}"
                    )
                else:
                    self.logger.info("  ✓ Market efficiently priced")
                    self.logger.info("_"*100)

            except Exception as e:
                self.logger.error(f"  ✗ Error analyzing market: {e}", exc_info=True)
                continue

        self.logger.info("=" * 60)
        self.logger.info(f"Scan complete. Found {len(opportunities)} opportunities.")
        self.logger.info("=" * 60)

        return opportunities

    def _fetch_markets_from_series(self, series_tickers: List[str]) -> List[dict]:
        """
        Fetch all markets from specified series

        Args:
            series_tickers: List of series tickers (e.g., KXLOWTDEN, KXLOWTMIA)

        Returns:
            List of market dictionaries
        """
        all_markets = []
        for series_ticker in series_tickers:
            try:
                self.logger.info(f"Fetching series: {series_ticker}")

                # Get all open markets for this series
                markets = self.kalshi.get_markets_for_series(series_ticker, status="open")

                # Format each market
                for market in markets:
                    formatted_market = {
                        "ticker": market["ticker"],
                        "title": market["title"],
                        "event_ticker": market.get("event_ticker", ""),
                        "close_time": market["close_time"],
                        "expiration_time": market.get("expiration_time", ""),
                        "yes_bid": market.get("yes_bid"),
                        "yes_ask": market.get("yes_ask"),
                        "no_bid": market.get("no_bid"),
                        "no_ask": market.get("no_ask"),
                        "volume": market.get("volume", 0),
                        "liquidity_pool": market.get("liquidity_pool"),
                        "category": market.get("category"),
                        "status": market.get("status"),
                    }
                    all_markets.append(formatted_market)

                self.logger.info(f"  ✓ Found {len(markets)} markets in {series_ticker}")

            except Exception as e:
                self.logger.error(f"  ✗ Failed to fetch series {series_ticker}: {e}")
                continue

        self.logger.info(f"Total markets fetched from series: {len(all_markets)}")
        return all_markets

    def _fetch_specific_markets(self, tickers: List[str]) -> List[dict]:
        """
        Fetch specific markets by ticker

        Args:
            tickers: List of market tickers to fetch

        Returns:
            List of market dictionaries
        """
        markets = []
        for ticker in tickers:
            try:
                self.logger.info(f"Fetching market: {ticker}")
                market = self.kalshi.get_market(ticker)

                # Format market data to match promo_markets structure
                formatted_market = {
                    "ticker": market["ticker"],
                    "title": market["title"],
                    "event_ticker": market.get("event_ticker", ""),
                    "close_time": market["close_time"],
                    "expiration_time": market.get("expiration_time", ""),
                    "yes_bid": market.get("yes_bid"),
                    "yes_ask": market.get("yes_ask"),
                    "no_bid": market.get("no_bid"),
                    "no_ask": market.get("no_ask"),
                    "volume": market.get("volume", 0),
                    "liquidity_pool": market.get("liquidity_pool"),
                    "category": market.get("category"),
                    "status": market.get("status"),
                }
                markets.append(formatted_market)
                self.logger.info(f"  ✓ Fetched: {market['title'][:70]}")

            except Exception as e:
                self.logger.error(f"  ✗ Failed to fetch {ticker}: {e}")
                continue

        return markets

    def _filter_weather_markets(self, markets: List[dict]) -> List[dict]:
        """
        Filter for weather/temperature markets

        Args:
            markets: List of all markets

        Returns:
            List of weather/temperature markets (all locations)
        """
        weather_markets = []
        for market in markets:
            title = market["title"].lower()

            # Check if it's a temperature/weather market
            is_weather = any(keyword in title for keyword in [
                "temperature", "weather", "lowest", "highest", "warmest", "coldest"
            ])

            if is_weather:
                weather_markets.append(market)

        self.logger.info(f"Found {len(weather_markets)} weather/temperature markets")
        return weather_markets

    def _parse_location(self, location: str) -> tuple:
        """
        Parse location string into city and state

        Args:
            location: Location string (e.g., "Denver, CO")

        Returns:
            Tuple of (city, state)
        """
        parts = location.split(",")
        if len(parts) != 2:
            return None, None

        city = parts[0].strip()
        state = parts[1].strip()

        return city, state

    def run_and_save(self, output_dir: str = "./reports") -> List[Opportunity]:
        """
        Run scan and save reports to disk

        Args:
            output_dir: Directory to save reports

        Returns:
            List of identified opportunities
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Run scan
        opportunities = self.scan()

        # Generate reports
        report_md = self.reporter.generate_daily_report(opportunities)
        report_csv = self.reporter.generate_csv_export(opportunities)

        # Save files with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_path = f"{output_dir}/kalshi_report_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(report_md)
        self.logger.info(f"Saved Markdown report: {md_path}")

        csv_path = f"{output_dir}/kalshi_opportunities_{timestamp}.csv"
        with open(csv_path, "w") as f:
            f.write(report_csv)
        self.logger.info(f"Saved CSV export: {csv_path}")

        # Also save latest as current.md
        current_path = f"{output_dir}/current.md"
        with open(current_path, "w") as f:
            f.write(report_md)
        self.logger.info(f"Saved current report: {current_path}")

        # Print summary
        if opportunities:
            summary = self.reporter.generate_summary(opportunities)
            self.logger.info(f"\n{summary}\n")

        return opportunities
