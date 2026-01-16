"""
NWS Data Adapter
Fetches and parses National Weather Service forecast data
"""

import requests
import logging
import pytz
from datetime import datetime
from typing import List, Dict, Optional


class NWSAdapter:
    """Adapter for retrieving weather forecast data from National Weather Service API"""

    # Supported locations with their coordinates and timezones
    LOCATIONS = {
        "Denver, CO": {
            "lat": 39.7392,
            "lon": -104.9903,
            "timezone": "America/Denver",
            "station_id": "KDEN"
        },
        "Miami, FL": {
            "lat": 25.7617,
            "lon": -80.1918,
            "timezone": "America/New_York",
            "station_id": "KMIA"
        }
    }

    def __init__(self, user_agent: str = "KalshiWeatherScanner/1.0"):
        """
        Initialize NWS adapter

        Args:
            user_agent: User-Agent string for API requests (NWS requires this)
        """
        self.base_url = "https://api.weather.gov"
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/geo+json"
        })
        self.logger = logging.getLogger(__name__)

        # Cache for gridpoint data (doesn't change)
        self._gridpoint_cache = {}

    def get_gridpoint(self, lat: float, lon: float) -> Dict:
        """
        Convert lat/lon to NWS grid coordinates

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Gridpoint information dictionary
        """
        cache_key = f"{lat},{lon}"

        # Return cached if available
        if cache_key in self._gridpoint_cache:
            self.logger.debug(f"Using cached gridpoint for {cache_key}")
            return self._gridpoint_cache[cache_key]

        url = f"{self.base_url}/points/{lat},{lon}"

        try:
            self.logger.info(f"Fetching gridpoint for lat={lat}, lon={lon}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            properties = data.get("properties", {})

            gridpoint = {
                "gridId": properties.get("gridId"),
                "gridX": properties.get("gridX"),
                "gridY": properties.get("gridY"),
                "forecast": properties.get("forecast"),
                "forecastHourly": properties.get("forecastHourly"),
            }

            # Cache the result
            self._gridpoint_cache[cache_key] = gridpoint
            self.logger.info(f"Gridpoint: {gridpoint['gridId']}/{gridpoint['gridX']},{gridpoint['gridY']}")

            return gridpoint

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch gridpoint: {e}")
            raise

    def get_hourly_forecast(self, lat: float, lon: float) -> List[Dict]:
        """
        Fetch hourly forecast for the next 7 days

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            List of hourly forecast periods
        """
        gridpoint = self.get_gridpoint(lat, lon)
        forecast_url = gridpoint["forecastHourly"]

        try:
            self.logger.info(f"Fetching hourly forecast from {forecast_url}")
            response = self.session.get(forecast_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            periods = data.get("properties", {}).get("periods", [])

            self.logger.info(f"Retrieved {len(periods)} hourly forecast periods")
            return periods

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch hourly forecast: {e}")
            raise

    def get_forecast_for_city(self, city: str, state: str) -> List[Dict]:
        """
        High-level method to get forecast by city name

        Args:
            city: City name (e.g., "Denver")
            state: State abbreviation (e.g., "CO")

        Returns:
            List of hourly forecast periods

        Raises:
            ValueError: If location is not supported
        """
        key = f"{city}, {state}"

        if key not in self.LOCATIONS:
            raise ValueError(f"Unsupported location: {key}. Supported: {list(self.LOCATIONS.keys())}")

        location = self.LOCATIONS[key]
        return self.get_hourly_forecast(location["lat"], location["lon"])

    def extract_temperature_stats_for_date(
        self,
        periods: List[Dict],
        target_date: str,
        timezone: str
    ) -> Optional[Dict]:
        """
        Calculate min/max/avg temperature for a specific date

        Args:
            periods: List of hourly forecast periods from NWS
            target_date: ISO date string (e.g., "2026-01-12")
            timezone: IANA timezone string (e.g., "America/Denver")

        Returns:
            Dictionary with temperature statistics or None if no data available
        """
        try:
            tz = pytz.timezone(timezone)
            target_dt = datetime.fromisoformat(target_date).date()

            temps_for_date = []

            for period in periods:
                # Parse startTime and convert to target timezone
                start_time_str = period.get("startTime")
                if not start_time_str:
                    continue

                # Parse ISO 8601 timestamp (handles timezone offsets)
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                local_time = start_time.astimezone(tz)

                # Check if this period is within target date
                if local_time.date() == target_dt:
                    temp = period.get("temperature")
                    if temp is not None:
                        temps_for_date.append(temp)

            if not temps_for_date:
                self.logger.warning(f"No temperature data found for {target_date} in {timezone}")
                return None

            stats = {
                "date": target_date,
                "min": min(temps_for_date),
                "max": max(temps_for_date),
                "avg": sum(temps_for_date) / len(temps_for_date),
                "hourly_temps": temps_for_date,
                "timezone": timezone,
                "num_periods": len(temps_for_date)
            }

            self.logger.info(
                f"Temperature stats for {target_date}: "
                f"min={stats['min']:.1f}°F, max={stats['max']:.1f}°F, "
                f"avg={stats['avg']:.1f}°F ({stats['num_periods']} periods)"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Error extracting temperature stats: {e}")
            return None

    def get_forecast_stats_for_city_and_date(
        self,
        city: str,
        state: str,
        target_date: str
    ) -> Optional[Dict]:
        """
        Convenience method to get temperature stats for a specific city and date

        Args:
            city: City name (e.g., "Denver")
            state: State abbreviation (e.g., "CO")
            target_date: ISO date string (e.g., "2026-01-12")

        Returns:
            Dictionary with temperature statistics or None if unavailable
        """
        key = f"{city}, {state}"
        if key not in self.LOCATIONS:
            raise ValueError(f"Unsupported location: {key}")

        # Get forecast periods
        periods = self.get_forecast_for_city(city, state)

        # Get timezone for this location
        timezone = self.LOCATIONS[key]["timezone"]

        # Extract stats for target date
        return self.extract_temperature_stats_for_date(periods, target_date, timezone)
