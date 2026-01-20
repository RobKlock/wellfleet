#!/usr/bin/env python3
"""
Preliminary CLI Auto-Betting Scanner

Monitors for NWS preliminary Climate Reports and automatically places bets
based on the preliminary min/max values.

Strategy:
1. Poll for preliminary CLI every 5 minutes starting at 7:00 AM
2. When preliminary is published (~7:30 AM), parse min/max values
3. Find all open markets for that date
4. Place $5 bets on markets that align with preliminary values
5. High confidence (~95%) since preliminary rarely changes

Usage:
    python preliminary_cli_bet.py               # Monitor Denver
    python preliminary_cli_bet.py --station KMIA  # Monitor Miami
    python preliminary_cli_bet.py --bet-size 10  # Custom bet size
"""

import os
import sys
import time
import logging
import argparse
import re
from datetime import datetime, date
from dotenv import load_dotenv
import pytz

from scanner import KalshiClient, NWSAdapter, MarketParser


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class PreliminaryCliScanner:
    """Scanner that bets based on preliminary Climate Reports"""

    def __init__(
        self,
        kalshi_client: KalshiClient,
        nws_adapter: NWSAdapter,
        station_id: str = "KDEN",
        bet_size_dollars: float = 5.0,
        confidence_threshold: float = 0.90
    ):
        """
        Initialize preliminary CLI scanner

        Args:
            kalshi_client: Authenticated Kalshi client
            nws_adapter: NWS data adapter
            station_id: Weather station ID (e.g., "KDEN")
            bet_size_dollars: Bet size in dollars per market
            confidence_threshold: Minimum confidence to place bet (0-1)
        """
        self.kalshi = kalshi_client
        self.nws = nws_adapter
        self.station_id = station_id
        self.bet_size_dollars = bet_size_dollars
        self.confidence_threshold = confidence_threshold
        self.parser = MarketParser()
        self.logger = logging.getLogger(__name__)

        # Track which dates we've already bet on
        self.processed_dates = set()

    def fetch_preliminary_cli(self, target_date: str) -> dict:
        """
        Fetch preliminary CLI from NWS

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            Dictionary with preliminary min/max or None
        """
        return self.nws.get_preliminary_climate_report(self.station_id, target_date)

    def find_matching_markets(
        self,
        preliminary_min: float,
        preliminary_max: float,
        target_date: date
    ) -> list:
        """
        Find markets that match preliminary CLI values

        Args:
            preliminary_min: Preliminary minimum temperature
            preliminary_max: Preliminary maximum temperature
            target_date: Market date

        Returns:
            List of (market, side, confidence) tuples
        """
        # Map station ID to series ticker
        station_to_series = {
            "KDEN": "KXLOWTDEN",
            "KMIA": "KXLOWTMIA",
            "KCYS": "KXLOWTCYS"
        }

        series_ticker = station_to_series.get(self.station_id)
        if not series_ticker:
            self.logger.warning(f"No series mapping for station {self.station_id}")
            return []

        # Get all open markets for this series
        markets = self.kalshi.get_markets_for_series(series_ticker, status="open")

        matching_bets = []

        for market in markets:
            parsed = self.parser.parse(market["title"], market["ticker"])

            if not parsed.is_parseable:
                continue

            # Only bet on markets for the target date
            if parsed.date != target_date:
                continue

            # Determine if market aligns with preliminary
            side, confidence = self._check_market_alignment(
                parsed,
                preliminary_min,
                preliminary_max
            )

            if side and confidence >= self.confidence_threshold:
                matching_bets.append((market, side, confidence))

        return matching_bets

    def _check_market_alignment(
        self,
        parsed,
        prelim_min: float,
        prelim_max: float
    ) -> tuple:
        """
        Check if market aligns with preliminary values

        Returns:
            (side, confidence) tuple where side is "yes"/"no" or None
        """
        metric = parsed.metric
        comparison = parsed.comparison
        threshold = parsed.threshold
        threshold_high = parsed.threshold_high

        # MINIMUM MARKETS
        if metric == "minimum":
            if comparison == "between":
                # Range market: does prelim_min fall in range?
                if threshold <= prelim_min <= threshold_high:
                    return ("yes", 0.95)  # Prelim shows temp IN range
                else:
                    return ("no", 0.95)   # Prelim shows temp OUTSIDE range

            elif comparison in ["above", "at least"]:
                # Will min be >= threshold?
                if prelim_min >= threshold:
                    return ("yes", 0.95)
                else:
                    return ("no", 0.95)

            elif comparison in ["below", "at most"]:
                # Will min be <= threshold?
                if prelim_min <= threshold:
                    return ("yes", 0.95)
                else:
                    return ("no", 0.95)

        # MAXIMUM MARKETS
        elif metric == "maximum":
            if comparison == "between":
                # Range market: does prelim_max fall in range?
                if threshold <= prelim_max <= threshold_high:
                    return ("yes", 0.95)  # Prelim shows temp IN range
                else:
                    return ("no", 0.95)   # Prelim shows temp OUTSIDE range

            elif comparison in ["above", "at least"]:
                # Will max be >= threshold?
                if prelim_max >= threshold:
                    return ("yes", 0.95)
                else:
                    return ("no", 0.95)

            elif comparison in ["below", "at most"]:
                # Will max be <= threshold?
                if prelim_max <= threshold:
                    return ("yes", 0.95)
                else:
                    return ("no", 0.95)

        return (None, 0.0)

    def place_bet(self, market: dict, side: str, confidence: float) -> dict:
        """
        Place a bet on a market

        Args:
            market: Market dictionary
            side: "yes" or "no"
            confidence: Confidence level (0-1)

        Returns:
            Order confirmation
        """
        ticker = market["ticker"]

        # Calculate number of contracts based on bet size
        # Market prices are in cents (0-100)
        if side == "yes":
            price_cents = market.get("yes_ask", market.get("yes_bid", 50))
        else:
            price_cents = market.get("no_ask", market.get("no_bid", 50))

        price_dollars = price_cents / 100.0
        count = max(1, int(self.bet_size_dollars / max(price_dollars, 0.01)))

        self.logger.info(f"Placing bet: {ticker} {side.upper()} x{count} @ ${price_dollars:.2f}")

        order = self.kalshi.place_order(
            ticker=ticker,
            side=side,
            action="buy",
            count=count,
            order_type="market"
        )

        return order

    def run_once(self, target_date: str) -> int:
        """
        Run scanner once for a specific date

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            Number of bets placed
        """
        # Check if we already processed this date
        if target_date in self.processed_dates:
            self.logger.debug(f"Already processed {target_date}, skipping")
            return 0

        # Fetch preliminary CLI
        self.logger.info(f"Checking for preliminary CLI for {target_date}...")
        preliminary = self.fetch_preliminary_cli(target_date)

        if not preliminary:
            self.logger.info(f"No preliminary CLI available yet for {target_date}")
            return 0

        prelim_min = preliminary.get("preliminary_min")
        prelim_max = preliminary.get("preliminary_max")

        if prelim_min is None and prelim_max is None:
            self.logger.warning("Preliminary CLI found but no min/max values")
            return 0

        self.logger.info("=" * 80)
        self.logger.info(f"📊 PRELIMINARY CLI FOUND for {target_date}!")
        self.logger.info("=" * 80)

        if prelim_min is not None:
            self.logger.info(f"   Minimum: {prelim_min}°F at {preliminary.get('min_time', 'unknown')}")
        if prelim_max is not None:
            self.logger.info(f"   Maximum: {prelim_max}°F at {preliminary.get('max_time', 'unknown')}")

        # Find matching markets
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        matching_bets = self.find_matching_markets(prelim_min or 999, prelim_max or 999, target_date_obj)

        if not matching_bets:
            self.logger.info("No matching markets found")
            self.processed_dates.add(target_date)
            return 0

        self.logger.info(f"\nFound {len(matching_bets)} markets to bet on:")
        for i, (market, side, confidence) in enumerate(matching_bets, 1):
            self.logger.info(f"  {i}. {market['ticker']} - {side.upper()} ({confidence:.1%} confidence)")

        # Place bets
        successful_bets = 0
        for market, side, confidence in matching_bets:
            try:
                order = self.place_bet(market, side, confidence)
                self.logger.info(f"✅ Bet placed: {market['ticker']} {side.upper()} - Order ID: {order.get('order_id')}")
                successful_bets += 1
            except Exception as e:
                self.logger.error(f"❌ Failed to place bet on {market['ticker']}: {e}")

        self.logger.info(f"\n✅ Placed {successful_bets}/{len(matching_bets)} bets for {target_date}")

        # Mark as processed
        self.processed_dates.add(target_date)

        return successful_bets

    def monitor(self, start_hour: int = 7, end_hour: int = 9, check_interval_minutes: int = 5):
        """
        Monitor for preliminary CLI and auto-bet

        Args:
            start_hour: Start monitoring at this hour (default: 7 AM)
            end_hour: Stop monitoring at this hour (default: 9 AM)
            check_interval_minutes: Check every N minutes (default: 5)
        """
        # Get timezone for this station
        station_to_tz = {
            "KDEN": "America/Denver",
            "KMIA": "America/New_York",
            "KCYS": "America/Denver"
        }

        tz_str = station_to_tz.get(self.station_id, "America/Denver")
        tz = pytz.timezone(tz_str)

        self.logger.info("=" * 80)
        self.logger.info(f"PRELIMINARY CLI MONITOR - {self.station_id}")
        self.logger.info("=" * 80)
        self.logger.info(f"Monitoring window: {start_hour:02d}:00 - {end_hour:02d}:00 {tz_str}")
        self.logger.info(f"Check interval: {check_interval_minutes} minutes")
        self.logger.info(f"Bet size: ${self.bet_size_dollars:.2f} per market")
        self.logger.info("=" * 80)

        while True:
            current_time = datetime.now(tz)
            current_hour = current_time.hour

            # Only check during monitoring window
            if start_hour <= current_hour < end_hour:
                # Check for today's preliminary
                today = current_time.date().isoformat()

                try:
                    bets_placed = self.run_once(today)

                    if bets_placed > 0:
                        self.logger.info(f"\n🎯 Successfully placed {bets_placed} bets!")
                        self.logger.info("Continuing to monitor for other dates...")

                except Exception as e:
                    self.logger.error(f"Error during scan: {e}")
                    import traceback
                    traceback.print_exc()

            else:
                self.logger.info(f"Outside monitoring window (current: {current_hour:02d}:00)")

            # Sleep until next check
            self.logger.info(f"Sleeping for {check_interval_minutes} minutes...")
            time.sleep(check_interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-bet based on NWS preliminary Climate Reports"
    )
    parser.add_argument(
        "--station",
        default="KDEN",
        help="Weather station ID (default: KDEN for Denver)"
    )
    parser.add_argument(
        "--bet-size",
        type=float,
        default=5.0,
        help="Bet size in dollars per market (default: $5)"
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=7,
        help="Start monitoring at this hour (default: 7)"
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=9,
        help="Stop monitoring at this hour (default: 9)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Check interval in minutes (default: 5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't monitor continuously)"
    )

    args = parser.parse_args()

    load_dotenv()

    # Get credentials
    api_key_id = os.getenv("KALSHI_API_KEY_ID")
    private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")

    if api_key_id and os.path.exists(private_key_path):
        auth_kwargs = {"api_key_id": api_key_id, "private_key_path": private_key_path}
    elif email and password:
        auth_kwargs = {"email": email, "password": password}
    else:
        logger.error("❌ No credentials configured!")
        return 1

    try:
        # Initialize clients
        kalshi_client = KalshiClient(**auth_kwargs)
        nws_adapter = NWSAdapter()

        # Create scanner
        scanner = PreliminaryCliScanner(
            kalshi_client=kalshi_client,
            nws_adapter=nws_adapter,
            station_id=args.station,
            bet_size_dollars=args.bet_size
        )

        if args.once:
            # Run once and exit
            today = datetime.now().date().isoformat()
            bets_placed = scanner.run_once(today)
            logger.info(f"\nPlaced {bets_placed} bets. Exiting.")
            return 0
        else:
            # Monitor continuously
            scanner.monitor(
                start_hour=args.start_hour,
                end_hour=args.end_hour,
                check_interval_minutes=args.interval
            )

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Monitoring stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
