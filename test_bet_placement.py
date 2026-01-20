#!/usr/bin/env python3
"""
Test Bet Placement
Places a small $2 test bet to verify Kalshi API integration works

Usage: python test_bet_placement.py
"""

import os
import logging
from dotenv import load_dotenv
from scanner import KalshiClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    load_dotenv()

    logger.info("=" * 80)
    logger.info("TEST BET PLACEMENT - $2 Test Bet")
    logger.info("=" * 80)

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
        # Initialize client
        logger.info("\n[1] Connecting to Kalshi API...")
        client = KalshiClient(**auth_kwargs)
        logger.info("✅ Connected successfully")

        # Get balance
        logger.info("\n[2] Fetching account balance...")
        balance = client.get_balance()
        logger.info(f"✅ Balance: ${balance.get('balance', 0) / 100:.2f}")

        # Find an open market to test with
        logger.info("\n[3] Finding a test market...")
        markets = client.get_markets_for_series("KXLOWTDEN", status="open")

        if not markets:
            logger.error("❌ No open markets found in KXLOWTDEN series")
            return 1

        # Pick the first market with decent liquidity
        test_market = None
        for market in markets:
            liquidity_pool = market.get("liquidity_pool") or {}
            pool_size = liquidity_pool.get("pool_size", 0)

            if pool_size > 1000:  # At least $10 liquidity
                test_market = market
                break

        if not test_market:
            # Just use first market if none have good liquidity
            test_market = markets[0]

        ticker = test_market["ticker"]
        title = test_market["title"]
        yes_bid = test_market.get("yes_bid", 0) / 100.0
        no_bid = test_market.get("no_bid", 0) / 100.0

        logger.info(f"✅ Selected market: {ticker}")
        logger.info(f"   {title}")
        logger.info(f"   Current prices: YES {yes_bid:.1%} / NO {no_bid:.1%}")

        # Determine which side to bet (pick the side with better liquidity)
        if yes_bid > no_bid:
            side = "yes"
            current_price = yes_bid
        else:
            side = "no"
            current_price = no_bid

        # Calculate how many contracts $2 gets us
        # If YES is at 20¢, $2 buys 10 contracts
        count = int(2.00 / max(current_price, 0.01))  # At least 1 contract
        cost = count * current_price

        logger.info(f"\n[4] PREPARING TEST BET:")
        logger.info(f"   Side: {side.upper()}")
        logger.info(f"   Contracts: {count}")
        logger.info(f"   Estimated cost: ${cost:.2f}")
        logger.info(f"   Max payout: ${count:.2f}")

        # Ask for confirmation
        logger.info("\n⚠️  This will place a REAL bet on Kalshi!")
        response = input("\nType 'YES' to place the test bet, or anything else to cancel: ")

        if response.strip().upper() != "YES":
            logger.info("❌ Bet cancelled by user")
            return 0

        # Place the order
        logger.info(f"\n[5] Placing order...")
        order = client.place_order(
            ticker=ticker,
            side=side,
            action="buy",
            count=count,
            order_type="market"
        )

        logger.info("✅ ORDER PLACED SUCCESSFULLY!")
        logger.info(f"\nOrder Details:")
        logger.info(f"   Order ID: {order.get('order_id')}")
        logger.info(f"   Status: {order.get('status')}")
        logger.info(f"   Ticker: {order.get('ticker')}")
        logger.info(f"   Side: {order.get('side', '').upper()}")
        logger.info(f"   Count: {order.get('count')}")

        if order.get('status') == 'executed':
            logger.info(f"   ✅ Order executed immediately")
        elif order.get('status') == 'resting':
            logger.info(f"   ⏳ Order is resting (waiting for match)")

        logger.info("\n" + "=" * 80)
        logger.info("TEST SUCCESSFUL!")
        logger.info("Bet placement is working correctly. You can now use the auto-betting scanner.")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
