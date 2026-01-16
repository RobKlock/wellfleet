"""
Kalshi API Client
Handles authentication and market data retrieval from Kalshi's REST API
"""

import requests
import logging
import time
import base64
from typing import List, Dict, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class KalshiClient:
    """Client for interacting with Kalshi's trading API"""

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key_id: Optional[str] = None,
        private_key_path: Optional[str] = None
    ):
        """
        Initialize client and authenticate

        Two authentication methods supported:
        1. Email/Password (legacy)
        2. API Key + Private Key (recommended)

        Args:
            email: Kalshi account email (for email/password auth)
            password: Kalshi account password (for email/password auth)
            api_key_id: API key ID (for API key auth)
            private_key_path: Path to private key file (for API key auth)
        """
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

        # Authentication state
        self.token = None
        self.member_id = None
        self.api_key_id = api_key_id
        self.private_key = None

        # Determine authentication method
        if api_key_id and private_key_path:
            # API Key authentication
            self.auth_method = "api_key"
            self._load_private_key(private_key_path)
            self.logger.info("Using API key authentication")
        elif email and password:
            # Email/Password authentication
            self.auth_method = "email_password"
            self.email = email
            self.password = password
            self.login()
        else:
            raise AuthenticationError(
                "Must provide either (api_key_id + private_key_path) or (email + password)"
            )

    def _load_private_key(self, private_key_path: str):
        """Load RSA private key from file"""
        try:
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
            self.logger.info(f"Loaded private key from {private_key_path}")
        except Exception as e:
            raise AuthenticationError(f"Failed to load private key: {e}")

    def _sign_request(self, timestamp: str, method: str, path: str) -> str:
        """
        Create RSA-PSS signature for API key authentication

        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            path: Request path without query parameters

        Returns:
            Base64-encoded signature
        """
        # Create message: timestamp + method + path
        message = f"{timestamp}{method}{path}"

        # Sign with RSA-PSS
        signature = self.private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )

        # Encode to base64
        return base64.b64encode(signature).decode('utf-8')

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
                # Prepare headers based on auth method
                headers = {}

                if self.auth_method == "api_key":
                    # Add API key signature headers
                    timestamp = str(int(time.time() * 1000))
                    signature = self._sign_request(timestamp, method.upper(), endpoint)

                    headers.update({
                        "KALSHI-ACCESS-KEY": self.api_key_id,
                        "KALSHI-ACCESS-TIMESTAMP": timestamp,
                        "KALSHI-ACCESS-SIGNATURE": signature
                    })

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
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

    def get_series(self, series_ticker: str) -> Dict:
        """
        Fetch information about a series

        Args:
            series_ticker: Series ticker (e.g., KXLOWTDEN)

        Returns:
            Series dictionary
        """
        endpoint = f"/series/{series_ticker}"
        data = self._make_request("GET", endpoint)

        return data.get("series", {})

    def get_markets_for_series(self, series_ticker: str, status: str = "open") -> List[Dict]:
        """
        Fetch all markets for a specific series

        Args:
            series_ticker: Series ticker (e.g., KXLOWTDEN, KXLOWTMIA)
            status: Market status filter (open, closed, unopened, settled)

        Returns:
            List of market dictionaries
        """
        endpoint = "/markets"
        params = {
            "series_ticker": series_ticker,
            "status": status
        }

        self.logger.info(f"Fetching markets for series {series_ticker} with status={status}")
        data = self._make_request("GET", endpoint, params=params)

        markets = data.get("markets", [])
        self.logger.info(f"Found {len(markets)} markets in series {series_ticker}")

        return markets
