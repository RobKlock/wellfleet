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
        },
        "Cheyenne, WY": {
            "lat": 41.1520,
            "lon": -104.8061,
            "timezone": "America/Denver",
            "station_id": "KCYS"
        }
    }

    # Leading indicator relationships: which stations can predict weather for which locations
    # Format: {target_location: [list of leading indicator stations]}
    LEADING_INDICATORS = {
        "Denver, CO": ["KCYS"],  # Cheyenne weather often precedes Denver by a few hours
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

    def get_observations(self, station_id: str, hours: int = 200) -> List[Dict]:
        """
        Fetch recent temperature observations from NWS station

        Args:
            station_id: NWS station identifier (e.g., "KDEN", "KMIA")
            hours: Number of observations to retrieve (default 200 = ~24-48 hours)

        Returns:
            List of observation dictionaries with timestamps and temperatures

        Note: NWS provides observations roughly hourly, so 200 observations
        gives us about 24-48 hours of data to capture full daily min/max
        """
        url = f"{self.base_url}/stations/{station_id}/observations"
        params = {"limit": hours}

        try:
            self.logger.info(f"Fetching observations from station {station_id}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            observations = data.get("features", [])

            # Extract temperature data
            temps = []
            for obs in observations:
                props = obs.get("properties", {})
                timestamp = props.get("timestamp")
                temp_c = props.get("temperature", {}).get("value")

                if timestamp and temp_c is not None:
                    # Convert Celsius to Fahrenheit
                    temp_f = (temp_c * 9/5) + 32
                    temps.append({
                        "timestamp": timestamp,
                        "temperature": temp_f
                    })

            self.logger.info(f"Retrieved {len(temps)} observations from {station_id}")
            return temps

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch observations: {e}")
            return []

    def get_current_conditions(self, station_id: str) -> Optional[Dict]:
        """
        Get latest weather observation including sky cover, wind, and dewpoint

        Args:
            station_id: NWS station identifier (e.g., "KDEN", "KMIA")

        Returns:
            Dictionary with current conditions or None if unavailable
        """
        url = f"{self.base_url}/stations/{station_id}/observations/latest"

        try:
            self.logger.info(f"Fetching current conditions from {station_id}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            props = data.get("properties", {})

            # Extract key meteorological parameters
            temp_c = props.get("temperature", {}).get("value")
            dewpoint_c = props.get("dewpoint", {}).get("value")
            wind_speed_kph = props.get("windSpeed", {}).get("value")

            # Sky cover as percentage (0-100)
            text_description = props.get("textDescription", "").lower()
            if "clear" in text_description or "sunny" in text_description:
                sky_cover = 0
            elif "few" in text_description:
                sky_cover = 25
            elif "scattered" in text_description or "partly" in text_description:
                sky_cover = 50
            elif "broken" in text_description or "mostly" in text_description:
                sky_cover = 75
            elif "overcast" in text_description or "cloudy" in text_description:
                sky_cover = 100
            else:
                sky_cover = 50  # Default to partly cloudy

            # Convert units to Fahrenheit and mph
            conditions = {
                "timestamp": props.get("timestamp"),
                "temperature": (temp_c * 9/5) + 32 if temp_c is not None else None,
                "dewpoint": (dewpoint_c * 9/5) + 32 if dewpoint_c is not None else None,
                "wind_speed": wind_speed_kph * 0.621371 if wind_speed_kph is not None else 0,
                "sky_cover": sky_cover,
                "description": props.get("textDescription", "")
            }

            self.logger.info(
                f"Current: {conditions['temperature']:.1f}°F, "
                f"dewpoint={conditions['dewpoint']:.1f}°F, "
                f"wind={conditions['wind_speed']:.1f}mph, "
                f"sky={conditions['sky_cover']}%"
            )

            return conditions

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch current conditions: {e}")
            return None

    def extract_temperature_stats_for_date(
        self,
        periods: List[Dict],
        target_date: str,
        timezone: str,
        include_meteorology: bool = False,
        observations: Optional[List[Dict]] = None,
        preliminary_report: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Calculate min/max/avg temperature for a specific date

        Combines actual observations (if target_date is today) with forecast data
        to get accurate min/max values that account for temperatures that already occurred.

        Args:
            periods: List of hourly forecast periods from NWS
            target_date: ISO date string (e.g., "2026-01-12")
            timezone: IANA timezone string (e.g., "America/Denver")
            include_meteorology: If True, include sky cover, wind, and dewpoint data
            observations: Optional list of recent observations to merge with forecast
            preliminary_report: Optional preliminary CLI report with min/max temps

        Returns:
            Dictionary with temperature statistics or None if no data available
        """
        try:
            tz = pytz.timezone(timezone)
            target_dt = datetime.fromisoformat(target_date).date()
            today = datetime.now(tz).date()

            temps_for_date = []
            sky_covers = []
            wind_speeds = []
            dewpoints = []

            # If target date is TODAY and we have observations, include actual temps from earlier today
            if target_dt == today and observations:
                self.logger.info(f"Target date {target_date} is today - merging observations with forecast")

                for obs in observations:
                    obs_time_str = obs.get("timestamp")
                    if not obs_time_str:
                        continue

                    # Parse observation timestamp
                    obs_time = datetime.fromisoformat(obs_time_str.replace('Z', '+00:00'))
                    obs_local_time = obs_time.astimezone(tz)

                    # Only include observations from TODAY
                    if obs_local_time.date() == target_dt:
                        temp = obs.get("temperature")
                        if temp is not None:
                            temps_for_date.append(temp)
                            self.logger.debug(f"Added observed temp: {temp:.1f}°F at {obs_local_time}")

                if temps_for_date:
                    self.logger.info(f"Included {len(temps_for_date)} observed temperatures from today")

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

                    if include_meteorology:
                        # Extract sky cover from forecast
                        short_forecast = period.get("shortForecast", "").lower()
                        if "clear" in short_forecast or "sunny" in short_forecast:
                            sky_covers.append(0)
                        elif "few" in short_forecast:
                            sky_covers.append(25)
                        elif "scattered" in short_forecast or "partly" in short_forecast:
                            sky_covers.append(50)
                        elif "broken" in short_forecast or "mostly" in short_forecast:
                            sky_covers.append(75)
                        elif "overcast" in short_forecast or "cloudy" in short_forecast:
                            sky_covers.append(100)
                        else:
                            sky_covers.append(50)

                        # Extract wind speed
                        wind_str = period.get("windSpeed", "0 mph")
                        try:
                            wind_speed = float(wind_str.split()[0])
                            wind_speeds.append(wind_speed)
                        except (ValueError, IndexError):
                            wind_speeds.append(0)

                        # Extract dewpoint (if available)
                        dewpoint = period.get("dewpoint", {})
                        if isinstance(dewpoint, dict):
                            dewpoint_value = dewpoint.get("value")
                            if dewpoint_value is not None:
                                # Convert Celsius to Fahrenheit
                                dewpoints.append((dewpoint_value * 9/5) + 32)

            if not temps_for_date:
                self.logger.warning(f"No temperature data found for {target_date} in {timezone}")
                return None

            # Track if we used actual observations from today
            used_observations = target_dt == today and observations and any(
                datetime.fromisoformat(obs.get("timestamp", "").replace('Z', '+00:00')).astimezone(tz).date() == target_dt
                for obs in observations if obs.get("timestamp")
            )

            stats = {
                "date": target_date,
                "min": min(temps_for_date),
                "max": max(temps_for_date),
                "avg": sum(temps_for_date) / len(temps_for_date),
                "hourly_temps": temps_for_date,
                "timezone": timezone,
                "num_periods": len(temps_for_date),
                "includes_observations": used_observations  # Flag if actual temps from today were used
            }

            # Add preliminary CLI report data if available (more reliable than observations)
            if preliminary_report:
                if "preliminary_min" in preliminary_report:
                    stats["preliminary_min"] = preliminary_report["preliminary_min"]
                if "preliminary_max" in preliminary_report:
                    stats["preliminary_max"] = preliminary_report["preliminary_max"]
                self.logger.info(
                    f"Added preliminary CLI data: "
                    f"MIN={preliminary_report.get('preliminary_min', 'N/A')}°F, "
                    f"MAX={preliminary_report.get('preliminary_max', 'N/A')}°F"
                )

            if include_meteorology:
                stats["sky_covers"] = sky_covers
                stats["wind_speeds"] = wind_speeds
                stats["dewpoints"] = dewpoints
                stats["avg_sky_cover"] = sum(sky_covers) / len(sky_covers) if sky_covers else 50
                stats["avg_wind_speed"] = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
                stats["avg_dewpoint"] = sum(dewpoints) / len(dewpoints) if dewpoints else None

            obs_note = " (includes actual observations from today)" if used_observations else ""
            self.logger.info(
                f"Temperature stats for {target_date}: "
                f"min={stats['min']:.1f}°F, max={stats['max']:.1f}°F, "
                f"avg={stats['avg']:.1f}°F ({stats['num_periods']} periods){obs_note}"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Error extracting temperature stats: {e}")
            return None

    def analyze_temperature_trend(
        self,
        observations: List[Dict],
        hours_back: int = 6
    ) -> Dict:
        """
        Analyze temperature trend from recent observations

        Detects if temperature is rising, falling, or stable, and calculates
        the rate of change. Useful for detecting incoming weather systems.

        Args:
            observations: List of observation dictionaries with timestamps and temperatures
            hours_back: How many hours back to analyze (default: 6)

        Returns:
            Dictionary with trend analysis:
            - trend: "rising", "falling", or "stable"
            - rate_per_hour: Temperature change in °F per hour
            - change_total: Total temperature change over the period
            - hours_analyzed: Actual hours of data analyzed
            - current_temp: Most recent temperature
            - oldest_temp: Temperature at start of analysis period
        """
        if not observations:
            return {
                "trend": "unknown",
                "rate_per_hour": 0,
                "change_total": 0,
                "hours_analyzed": 0,
                "current_temp": None,
                "oldest_temp": None
            }

        # Sort observations by timestamp (newest first)
        sorted_obs = sorted(
            observations,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        # Get current (most recent) temperature
        current_temp = sorted_obs[0].get("temperature")
        current_time = datetime.fromisoformat(sorted_obs[0].get("timestamp").replace('Z', '+00:00'))

        # Find temperature from hours_back ago
        cutoff_time = current_time.timestamp() - (hours_back * 3600)

        # Find the observation closest to hours_back ago
        oldest_temp = None
        oldest_time = None
        for obs in reversed(sorted_obs):
            obs_time_str = obs.get("timestamp")
            if not obs_time_str:
                continue
            obs_time = datetime.fromisoformat(obs_time_str.replace('Z', '+00:00'))

            if obs_time.timestamp() <= cutoff_time:
                oldest_temp = obs.get("temperature")
                oldest_time = obs_time
                break

        # If we didn't find an observation old enough, use the oldest available
        if oldest_temp is None and len(sorted_obs) > 1:
            oldest_obs = sorted_obs[-1]
            oldest_temp = oldest_obs.get("temperature")
            oldest_time = datetime.fromisoformat(oldest_obs.get("timestamp").replace('Z', '+00:00'))

        if oldest_temp is None or current_temp is None:
            return {
                "trend": "unknown",
                "rate_per_hour": 0,
                "change_total": 0,
                "hours_analyzed": 0,
                "current_temp": current_temp,
                "oldest_temp": None
            }

        # Calculate temperature change
        change_total = current_temp - oldest_temp
        hours_analyzed = (current_time.timestamp() - oldest_time.timestamp()) / 3600
        rate_per_hour = change_total / hours_analyzed if hours_analyzed > 0 else 0

        # Determine trend (±1°F/hour is significant)
        if rate_per_hour > 1.0:
            trend = "rising"
        elif rate_per_hour < -1.0:
            trend = "falling"
        else:
            trend = "stable"

        self.logger.info(
            f"Temperature trend: {trend} at {rate_per_hour:.1f}°F/hr "
            f"(from {oldest_temp:.1f}°F to {current_temp:.1f}°F over {hours_analyzed:.1f}hrs)"
        )

        return {
            "trend": trend,
            "rate_per_hour": rate_per_hour,
            "change_total": change_total,
            "hours_analyzed": hours_analyzed,
            "current_temp": current_temp,
            "oldest_temp": oldest_temp
        }

    def get_leading_indicator_insights(
        self,
        target_station_id: str,
        target_city_state: str
    ) -> Optional[Dict]:
        """
        Check leading indicator stations for incoming weather patterns

        For example, Cheyenne, WY weather often precedes Denver, CO weather
        by a few hours due to prevailing wind patterns.

        Args:
            target_station_id: Station ID for the target location (e.g., "KDEN")
            target_city_state: City and state key (e.g., "Denver, CO")

        Returns:
            Dictionary with leading indicator insights:
            - has_leading_indicators: bool
            - leading_stations: list of station IDs
            - insights: list of dictionaries with trend data for each leading station
            - recommendation: "expect_warming", "expect_cooling", or "no_change"
        """
        # Check if this location has leading indicators
        leading_station_ids = self.LEADING_INDICATORS.get(target_city_state, [])

        if not leading_station_ids:
            return {
                "has_leading_indicators": False,
                "leading_stations": [],
                "insights": [],
                "recommendation": "no_change"
            }

        # Get observations from target station
        target_obs = self.get_observations(target_station_id, hours=200)
        target_trend = self.analyze_temperature_trend(target_obs, hours_back=6)

        insights = []
        for leading_station_id in leading_station_ids:
            # Get observations from leading indicator station
            leading_obs = self.get_observations(leading_station_id, hours=200)
            leading_trend = self.analyze_temperature_trend(leading_obs, hours_back=6)

            # Calculate temperature difference between stations
            temp_diff = None
            if leading_trend["current_temp"] and target_trend["current_temp"]:
                temp_diff = leading_trend["current_temp"] - target_trend["current_temp"]

            insights.append({
                "station_id": leading_station_id,
                "trend": leading_trend["trend"],
                "rate_per_hour": leading_trend["rate_per_hour"],
                "current_temp": leading_trend["current_temp"],
                "temp_diff_from_target": temp_diff
            })

        # Determine recommendation based on leading indicator trends
        recommendation = "no_change"

        # If leading indicator shows strong cooling/warming trend that target doesn't have yet
        for insight in insights:
            if insight["trend"] == "falling" and target_trend["trend"] != "falling":
                if insight["rate_per_hour"] < -2.0:  # Significant cooling
                    recommendation = "expect_cooling"
                    self.logger.info(
                        f"Leading indicator {insight['station_id']} shows cooling at "
                        f"{insight['rate_per_hour']:.1f}°F/hr, may affect {target_city_state}"
                    )
            elif insight["trend"] == "rising" and target_trend["trend"] != "rising":
                if insight["rate_per_hour"] > 2.0:  # Significant warming
                    recommendation = "expect_warming"
                    self.logger.info(
                        f"Leading indicator {insight['station_id']} shows warming at "
                        f"{insight['rate_per_hour']:.1f}°F/hr, may affect {target_city_state}"
                    )

        return {
            "has_leading_indicators": True,
            "leading_stations": leading_station_ids,
            "insights": insights,
            "target_trend": target_trend,
            "recommendation": recommendation
        }

    def get_preliminary_climate_report(self, station_id: str, date_str: str) -> Optional[Dict]:
        """
        Fetch preliminary Climate Report (CLI product) from NWS text products

        The CLI report is issued around 7:30 AM and contains the preliminary min/max
        based on the Daily Summary Message (DSM). This is more reliable than
        individual METAR observations due to quality control.

        Args:
            station_id: Station ID (e.g., "KDEN")
            date_str: Date in YYYY-MM-DD format

        Returns:
            Dictionary with preliminary min/max or None if not available

        Note: ASOS uses 5-minute running averages, not instantaneous readings.
        Display values are rounded but internal precision is higher.
        """
        # Format: https://forecast.weather.gov/product.php?site=NWS&product=CLI&issuedby=DEN
        # Use site=NWS (generic) for CLI products, not the WFO code
        station_code = station_id[1:]  # Remove 'K' prefix (KDEN -> DEN)
        url = f"{self.base_url.replace('api.', 'forecast.')}/product.php"
        params = {
            "site": "NWS",  # Use generic NWS site for CLI products
            "product": "CLI",
            "issuedby": station_code
        }

        try:
            self.logger.info(f"Fetching preliminary CLI for {station_id} on {date_str}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse the HTML response - CLI text is in a <pre> tag
            html = response.text
            import re

            # Extract text from <pre> tag
            pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', html, re.DOTALL)
            if not pre_match:
                self.logger.warning("Could not find CLI text in <pre> tag")
                return None

            text = pre_match.group(1)

            # Look for temperature section
            # Example: "  MINIMUM         13    138 AM -14    1962  19     -6       16"
            # Pattern: MINIMUM <temp> <time> AM/PM
            min_pattern = r"MINIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"
            max_pattern = r"MAXIMUM\s+(\d+)\s+(\d+)\s+(AM|PM)"

            min_match = re.search(min_pattern, text)
            max_match = re.search(max_pattern, text)

            result = {}

            if min_match:
                result["preliminary_min"] = float(min_match.group(1))
                # Format time (e.g., "138" -> "1:38")
                time_raw = min_match.group(2)
                if len(time_raw) == 3:
                    time_formatted = f"{time_raw[0]}:{time_raw[1:]}"
                elif len(time_raw) == 4:
                    time_formatted = f"{time_raw[:2]}:{time_raw[2:]}"
                else:
                    time_formatted = time_raw
                result["min_time"] = f"{time_formatted} {min_match.group(3)}"
                self.logger.info(
                    f"Preliminary CLI: MIN={result['preliminary_min']}°F at {result['min_time']}"
                )

            if max_match:
                result["preliminary_max"] = float(max_match.group(1))
                # Format time (e.g., "240" -> "2:40")
                time_raw = max_match.group(2)
                if len(time_raw) == 3:
                    time_formatted = f"{time_raw[0]}:{time_raw[1:]}"
                elif len(time_raw) == 4:
                    time_formatted = f"{time_raw[:2]}:{time_raw[2:]}"
                else:
                    time_formatted = time_raw
                result["max_time"] = f"{time_formatted} {max_match.group(3)}"
                self.logger.info(
                    f"Preliminary CLI: MAX={result['preliminary_max']}°F at {result['max_time']}"
                )

            return result if result else None

        except Exception as e:
            self.logger.warning(f"Could not fetch preliminary CLI: {e}")
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
