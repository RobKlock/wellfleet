"""
Kalshi API Client
Handles authentication and market data retrieval from Kalshi's REST API
"""

import requests
import logging
import time
from typing import List, Dict, Optional


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class KalshiClient:
    """Client for interacting with Kalshi's trading API"""

    def __init__(self, email: str, password: str):
        """
        Initialize client and authenticate

        Args:
            email: Kalshi account email
            password: Kalshi account password
        """
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.email = email
        self.password = password
        self.token = None
        self.member_id = None
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

        # Authenticate on initialization
        self.login()

    def login(self) -> None:
        """
        Authenticate with Kalshi and store bearer token

        Raises:
            AuthenticationError: If login fails
        """
        url = f"{self.base_url}/login"
        payload = {
            "email": self.email,
            "password": self.password
        }

        try:
            self.logger.info("Authenticating with Kalshi...")
            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 401:
                raise AuthenticationError("Invalid credentials")
            elif response.status_code == 429:
                self.logger.warning("Rate limited on login, retrying...")
                time.sleep(2)
                response = requests.post(url, json=payload, timeout=30)

            response.raise_for_status()
            data = response.json()

            self.token = data.get("token")
            self.member_id = data.get("member_id")

            if not self.token:
                raise AuthenticationError("No token received from login")

            # Set authorization header for all future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

            self.logger.info(f"Successfully authenticated as member {self.member_id}")

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Login request failed: {e}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Make authenticated request with retry logic

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=30
                )

                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Handle server errors with retry
                if response.status_code >= 500:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request timeout, retrying...")
                    time.sleep(2)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request failed: {e}, retrying...")
                    time.sleep(2)
                    continue
                raise

        raise Exception(f"Failed after {max_retries} attempts")

    def get_events(self, status: str = "open", limit: int = 200) -> List[Dict]:
        """
        Fetch all events with their nested markets

        Args:
            status: Event status filter ("open", "closed", "settled")
            limit: Maximum number of events to retrieve

        Returns:
            List of event dictionaries with nested markets
        """
        params = {
            "status": status,
            "with_nested_markets": "true",
            "limit": limit
        }

        self.logger.info(f"Fetching events with status={status}, limit={limit}")
        data = self._make_request("GET", "/events", params=params)

        events = data.get("events", [])
        self.logger.info(f"Retrieved {len(events)} events")

        return events

    def get_promo_markets(self) -> List[Dict]:
        """
        Filter events to return only markets with active liquidity pools

        Returns:
            List of market dictionaries with liquidity pool information
        """
        events = self.get_events(status="open")
        promo_markets = []

        for event in events:
            for market in event.get("markets", []):
                # Check if market has an active liquidity pool
                if market.get("liquidity_pool"):
                    promo_markets.append({
                        "ticker": market["ticker"],
                        "title": market["title"],
                        "event_ticker": event["event_ticker"],
                        "close_time": market["close_time"],
                        "expiration_time": market["expiration_time"],
                        "yes_bid": market.get("yes_bid"),
                        "yes_ask": market.get("yes_ask"),
                        "no_bid": market.get("no_bid"),
                        "no_ask": market.get("no_ask"),
                        "volume": market.get("volume", 0),
                        "liquidity_pool": market["liquidity_pool"],
                        "category": event.get("category"),
                        "status": market.get("status"),
                    })

        self.logger.info(f"Found {len(promo_markets)} markets with liquidity pools")
        return promo_markets

    def get_orderbook(self, ticker: str) -> Dict:
        """
        Fetch detailed orderbook for a specific market

        Args:
            ticker: Market ticker symbol

        Returns:
            Orderbook dictionary with yes/no orders
        """
        endpoint = f"/markets/{ticker}/orderbook"
        data = self._make_request("GET", endpoint)

        return data.get("orderbook", {})

    def get_market(self, ticker: str) -> Dict:
        """
        Fetch detailed information for a specific market

        Args:
            ticker: Market ticker symbol

        Returns:
            Market dictionary
        """
        endpoint = f"/markets/{ticker}"
        data = self._make_request("GET", endpoint)

        return data.get("market", {})
