#!/usr/bin/env python3
"""
Overnight Climate Markets Scanner
Continuously scans all climate markets overnight to identify opportunities

This script:
- Runs continuously overnight (e.g., 8pm - 8am)
- Scans at optimal intervals (configurable, default 2 hours)
- Works with ALL climate markets, not just Denver/Miami
- Includes retry logic for API failures
- Generates timestamped reports for each scan
- Optimized for timing advantages in overnight markets
"""

import os
import sys
import time
import logging
from datetime import datetime, time as dt_time
from pathlib import Path
from dotenv import load_dotenv

from scanner import KalshiWeatherScanner


# Configuration
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "120"))  # Default: 2 hours
START_HOUR = int(os.getenv("OVERNIGHT_START_HOUR", "20"))  # 8pm
END_HOUR = int(os.getenv("OVERNIGHT_END_HOUR", "8"))  # 8am
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "./reports"))
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 60


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(REPORTS_DIR / "overnight_scanner.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)


def is_overnight_hours() -> bool:
    """
    Check if current time is within overnight scanning hours

    Returns:
        True if within overnight hours
    """
    now = datetime.now()
    current_hour = now.hour

    # Handle overnight range that crosses midnight
    if START_HOUR > END_HOUR:
        # e.g., 20 (8pm) to 8 (8am) - crosses midnight
        return current_hour >= START_HOUR or current_hour < END_HOUR
    else:
        # e.g., 8 (8am) to 20 (8pm) - same day
        return START_HOUR <= current_hour < END_HOUR


def run_single_scan(scanner: KalshiWeatherScanner) -> int:
    """
    Run a single scan with retry logic

    Args:
        scanner: Initialized scanner instance

    Returns:
        Number of opportunities found, or -1 if scan failed
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Starting scan (attempt {attempt}/{MAX_RETRIES})...")

            # Scan all promo markets (now includes all climate markets)
            opportunities = scanner.scan(mode="promo")

            logger.info(f"Scan completed: {len(opportunities)} opportunities found")
            return len(opportunities)

        except Exception as e:
            logger.error(f"Scan attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error(f"All {MAX_RETRIES} scan attempts failed")
                return -1

    return -1


def save_timestamped_report(scanner: KalshiWeatherScanner, opportunities: list) -> Path:
    """
    Save a timestamped report for the current scan

    Args:
        scanner: Scanner instance
        opportunities: List of opportunities found

    Returns:
        Path to saved report
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"scan_report_{timestamp}.md"

    report = scanner.report_generator.generate_daily_report(opportunities)

    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Report saved to {report_path}")
    return report_path


def main():
    """Main overnight scanning loop"""
    # Load environment variables
    load_dotenv()

    # Create reports directory
    REPORTS_DIR.mkdir(exist_ok=True)

    logger.info("=" * 80)
    logger.info("OVERNIGHT CLIMATE MARKETS SCANNER - STARTING")
    logger.info("=" * 80)
    logger.info(f"Scan interval: {SCAN_INTERVAL_MINUTES} minutes")
    logger.info(f"Overnight hours: {START_HOUR}:00 - {END_HOUR}:00")
    logger.info(f"Reports directory: {REPORTS_DIR}")
    logger.info(f"Scanning ALL climate markets (not limited to specific cities)")
    logger.info("=" * 80)

    # Initialize scanner
    try:
        # Check for API key credentials (preferred method)
        api_key_id = os.getenv("KALSHI_API_KEY_ID")
        private_key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_api_private_key.txt")

        # Fallback to email/password
        email = os.getenv("KALSHI_EMAIL")
        password = os.getenv("KALSHI_PASSWORD")

        if api_key_id and os.path.exists(private_key_path):
            logger.info("Authenticating with API key...")
            scanner = KalshiWeatherScanner(
                kalshi_api_key_id=api_key_id,
                kalshi_private_key_path=private_key_path
            )
        elif email and password:
            logger.info("Authenticating with email/password...")
            scanner = KalshiWeatherScanner(
                kalshi_email=email,
                kalshi_password=password
            )
        else:
            logger.error("No Kalshi credentials found!")
            logger.error("Set either:")
            logger.error("  - KALSHI_API_KEY_ID + KALSHI_PRIVATE_KEY_PATH")
            logger.error("  - KALSHI_EMAIL + KALSHI_PASSWORD")
            return 1

        logger.info(f"Authenticated using {scanner.kalshi_client.auth_method}")

    except Exception as e:
        logger.error(f"Failed to initialize scanner: {e}")
        return 1

    # Main scanning loop
    scan_count = 0
    total_opportunities = 0

    try:
        while True:
            now = datetime.now()

            # Check if we're in overnight hours
            if not is_overnight_hours():
                logger.info(f"Outside overnight hours (current: {now.strftime('%H:%M')})")
                logger.info(f"Waiting until {START_HOUR}:00 to start scanning...")

                # Calculate sleep time until start hour
                if now.hour < START_HOUR:
                    # Same day
                    wake_time = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
                else:
                    # Next day
                    from datetime import timedelta
                    wake_time = (now + timedelta(days=1)).replace(hour=START_HOUR, minute=0, second=0, microsecond=0)

                sleep_seconds = (wake_time - now).total_seconds()
                logger.info(f"Sleeping for {sleep_seconds/3600:.1f} hours until {wake_time.strftime('%Y-%m-%d %H:%M')}")
                time.sleep(sleep_seconds)
                continue

            # Run scan
            scan_count += 1
            logger.info("=" * 80)
            logger.info(f"SCAN #{scan_count} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)

            # Execute scan
            opportunities = scanner.scan(mode="promo")
            num_opps = len(opportunities)

            if num_opps > 0:
                total_opportunities += num_opps
                logger.info(f"✓ Found {num_opps} opportunities!")

                # Save timestamped report
                report_path = save_timestamped_report(scanner, opportunities)

                # Log top opportunities
                logger.info("\nTop opportunities:")
                for i, opp in enumerate(opportunities[:5], 1):
                    logger.info(
                        f"  {i}. {opp.ticker}: {opp.edge:+.1%} edge, "
                        f"{opp.location}, {opp.recommended_bet_size:.0f} bet"
                    )
            else:
                logger.info("No opportunities found in this scan")

            # Summary
            logger.info(f"\nTotal scans: {scan_count}")
            logger.info(f"Total opportunities found: {total_opportunities}")

            # Calculate next scan time
            next_scan = now.timestamp() + (SCAN_INTERVAL_MINUTES * 60)
            next_scan_dt = datetime.fromtimestamp(next_scan)

            # Check if next scan would be outside overnight hours
            if not is_overnight_hours():
                logger.info(f"\nReached end of overnight hours ({END_HOUR}:00)")
                logger.info("Stopping overnight scanner")
                break

            logger.info(f"\nNext scan at: {next_scan_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Sleeping for {SCAN_INTERVAL_MINUTES} minutes...")
            logger.info("=" * 80)

            # Sleep until next scan
            time.sleep(SCAN_INTERVAL_MINUTES * 60)

    except KeyboardInterrupt:
        logger.info("\n\nReceived interrupt signal - shutting down gracefully")

    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        return 1

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("OVERNIGHT SCANNER SESSION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total scans completed: {scan_count}")
    logger.info(f"Total opportunities found: {total_opportunities}")
    logger.info(f"Reports saved to: {REPORTS_DIR}")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
