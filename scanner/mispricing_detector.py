"""
Mispricing Detector
Compares market prices against NWS forecast data to identify arbitrage opportunities
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Optional, List

from .market_parser import ParsedMarket

try:
    from scipy.stats import norm
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class Opportunity:
    """Represents a potential arbitrage opportunity"""
    ticker: str
    title: str
    location: str
    date: date

    # Market data
    market_yes_price: float  # Best bid on YES
    market_no_price: float   # Best bid on NO

    # Forecast data
    forecast_min: float
    forecast_max: float
    forecast_avg: float

    # Analysis
    true_probability: float  # Our estimate
    edge: float             # true_prob - market_price
    recommended_side: str   # "YES" or "NO"
    recommended_bet_size: float  # Dollars

    # Metadata
    confidence: float       # 0-1, how confident we are
    reasoning: str
    data_source: str
    liquidity_pool_size: float
    close_time: datetime


class BoundaryForecastModel:
    """
    Enhanced forecast model for markets within ±3°F of NWS forecasts

    Uses current conditions, observations, and meteorological adjustments
    to calculate refined probabilities for boundary cases.
    """

    def __init__(self):
        """Initialize boundary forecast model"""
        self.logger = logging.getLogger(__name__)

        # Base forecast uncertainty (standard deviation in °F)
        self.base_uncertainty = 2.5

    def calculate_boundary_probability(
        self,
        forecast_value: float,
        threshold: float,
        threshold_high: Optional[float],
        comparison: str,
        current_conditions: Optional[Dict] = None,
        observations: Optional[List[Dict]] = None,
        forecast_stats: Optional[Dict] = None
    ) -> float:
        """
        Calculate refined probability for markets near forecast boundaries

        Args:
            forecast_value: NWS forecast temperature (°F)
            threshold: Market threshold temperature (°F)
            threshold_high: Upper threshold for "between" markets
            comparison: Comparison operator ("above", "below", "between")
            current_conditions: Current weather conditions (temp, dewpoint, wind, sky)
            observations: Recent temperature observations (last 48 hours)
            forecast_stats: Forecast meteorological data (sky covers, wind speeds, dewpoints)

        Returns:
            Probability between 0 and 1
        """
        if not SCIPY_AVAILABLE:
            self.logger.warning("scipy not available, using simple heuristics")
            return self._simple_probability(forecast_value, threshold, threshold_high, comparison)

        # Calculate meteorological adjustments
        adjustment = self._calculate_meteorological_adjustment(
            forecast_value=forecast_value,
            current_conditions=current_conditions,
            forecast_stats=forecast_stats
        )

        # Calculate NWS bias from observations
        bias = self._calculate_nws_bias(
            forecast_value=forecast_value,
            observations=observations
        )

        # Adjusted forecast
        adjusted_forecast = forecast_value + adjustment + bias

        # Calculate uncertainty (standard deviation)
        uncertainty = self._calculate_uncertainty(
            current_conditions=current_conditions,
            forecast_stats=forecast_stats
        )

        # Calculate probability using normal distribution
        if comparison in ["above", "at least"]:
            # P(temp >= threshold)
            prob = 1 - norm.cdf(threshold, loc=adjusted_forecast, scale=uncertainty)
        elif comparison == "below":
            # P(temp < threshold)
            prob = norm.cdf(threshold, loc=adjusted_forecast, scale=uncertainty)
        elif comparison == "between":
            # P(threshold <= temp <= threshold_high)
            prob_below_high = norm.cdf(threshold_high, loc=adjusted_forecast, scale=uncertainty)
            prob_below_low = norm.cdf(threshold, loc=adjusted_forecast, scale=uncertainty)
            prob = prob_below_high - prob_below_low
        else:
            self.logger.warning(f"Unknown comparison: {comparison}")
            return 0.50

        # Clamp to [0.05, 0.95] for safety
        prob = max(0.05, min(0.95, prob))

        self.logger.info(
            f"Boundary model: forecast={forecast_value:.1f}°F, "
            f"adjusted={adjusted_forecast:.1f}°F (adj={adjustment:+.1f}, bias={bias:+.1f}), "
            f"uncertainty={uncertainty:.1f}°F, threshold={threshold:.0f}°F, "
            f"prob={prob:.1%}"
        )

        return prob

    def _calculate_meteorological_adjustment(
        self,
        forecast_value: float,
        current_conditions: Optional[Dict],
        forecast_stats: Optional[Dict]
    ) -> float:
        """
        Calculate temperature adjustment based on meteorological factors

        Factors:
        1. Current temperature constraint
        2. Radiative cooling (clear skies overnight)
        3. Atmospheric mixing (wind speed)
        4. Dewpoint spread (humidity effects)

        Returns:
            Temperature adjustment in °F (can be positive or negative)
        """
        total_adjustment = 0.0

        if not current_conditions or not forecast_stats:
            return total_adjustment

        current_temp = current_conditions.get("temperature")
        if current_temp is None:
            return total_adjustment

        # 1. Current temperature constraint
        # If current temp is already near threshold, adjust forecast
        temp_diff = current_temp - forecast_value
        if abs(temp_diff) > 5:
            # Current temp significantly different from forecast
            # Give current temp 20% weight
            total_adjustment += 0.2 * temp_diff

        # 2. Radiative cooling adjustment (for overnight minimum temps)
        sky_cover = forecast_stats.get("avg_sky_cover", 50)
        if sky_cover is not None and sky_cover < 30:
            # Clear skies enhance radiative cooling
            # Can drop temperature 1-3°F more than forecast
            clear_sky_adjustment = -1.5 * (1 - sky_cover / 100)
            total_adjustment += clear_sky_adjustment

        # 3. Wind mixing adjustment
        wind_speed = forecast_stats.get("avg_wind_speed", 0)
        if wind_speed is not None and wind_speed > 10:
            # High winds reduce temperature extremes
            # Warming effect on minimums, cooling effect on maximums
            # For now, assume we're looking at minimums (most common)
            wind_adjustment = min(2.0, 0.1 * (wind_speed - 10))
            total_adjustment += wind_adjustment

        # 4. Dewpoint spread adjustment
        current_dewpoint = current_conditions.get("dewpoint")
        if current_temp is not None and current_dewpoint is not None:
            dewpoint_spread = current_temp - current_dewpoint

            if dewpoint_spread > 20:
                # Very dry air, enhances radiative cooling
                total_adjustment -= 1.0
            elif dewpoint_spread < 5:
                # High humidity, moderates temperature swings
                total_adjustment += 0.5

        return total_adjustment

    def _calculate_nws_bias(
        self,
        forecast_value: float,
        observations: Optional[List[Dict]]
    ) -> float:
        """
        Calculate NWS forecast bias from recent observations

        Compares recent forecasts to actual observations to detect
        systematic over/under-prediction.

        Args:
            forecast_value: Current NWS forecast
            observations: Recent temperature observations

        Returns:
            Bias adjustment in °F (positive if NWS tends to under-predict)
        """
        if not observations or len(observations) < 10:
            return 0.0

        # For simplicity, assume NWS has been accurate recently
        # In production, would compare recent forecasts to actual temps
        # and calculate running bias

        # Placeholder: check if observations show consistent pattern
        recent_temps = [obs["temperature"] for obs in observations[:24]]
        avg_recent = sum(recent_temps) / len(recent_temps)

        # If recent average is consistently different from forecast,
        # apply small bias adjustment
        bias = 0.1 * (avg_recent - forecast_value)

        # Limit bias to ±1°F
        bias = max(-1.0, min(1.0, bias))

        return bias

    def _calculate_uncertainty(
        self,
        current_conditions: Optional[Dict],
        forecast_stats: Optional[Dict]
    ) -> float:
        """
        Calculate forecast uncertainty (standard deviation)

        Uncertainty decreases with:
        - Current observations available
        - Stable weather patterns
        - Low wind variability

        Returns:
            Standard deviation in °F
        """
        uncertainty = self.base_uncertainty

        if current_conditions:
            # Having current conditions reduces uncertainty
            uncertainty *= 0.9

        if forecast_stats:
            # Check wind variability
            wind_speeds = forecast_stats.get("wind_speeds", [])
            if wind_speeds and len(wind_speeds) > 1:
                wind_std = math.sqrt(
                    sum((w - sum(wind_speeds)/len(wind_speeds))**2 for w in wind_speeds) / len(wind_speeds)
                )
                if wind_std > 5:
                    # High wind variability increases uncertainty
                    uncertainty *= 1.2

        # Clamp uncertainty to reasonable range
        uncertainty = max(1.5, min(4.0, uncertainty))

        return uncertainty

    def _simple_probability(
        self,
        forecast_value: float,
        threshold: float,
        threshold_high: Optional[float],
        comparison: str
    ) -> float:
        """
        Fallback simple probability calculation (when scipy unavailable)

        Uses same heuristics as original MispricingDetector
        """
        if comparison in ["above", "at least"]:
            distance = forecast_value - threshold

            if distance > 5:
                return 0.95
            elif distance > 2:
                return 0.85
            elif distance > 0:
                return 0.70
            elif distance > -2:
                return 0.50
            elif distance > -5:
                return 0.15
            else:
                return 0.05

        elif comparison == "below":
            distance = threshold - forecast_value

            if distance > 5:
                return 0.95
            elif distance > 2:
                return 0.85
            elif distance > 0:
                return 0.70
            elif distance > -2:
                return 0.50
            elif distance > -5:
                return 0.15
            else:
                return 0.05

        elif comparison == "between":
            if threshold <= forecast_value <= threshold_high:
                margin = min(forecast_value - threshold, threshold_high - forecast_value)

                if margin > 3:
                    return 0.90
                elif margin > 1:
                    return 0.75
                else:
                    return 0.60

            elif forecast_value < threshold:
                distance = threshold - forecast_value

                if distance < 2:
                    return 0.40
                elif distance < 5:
                    return 0.15
                else:
                    return 0.05
            else:
                distance = forecast_value - threshold_high

                if distance < 2:
                    return 0.40
                elif distance < 5:
                    return 0.15
                else:
                    return 0.05

        return 0.50


class MispricingDetector:
    """Detects mispricings by comparing market prices to forecast data"""

    def __init__(
        self,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.25,
        min_edge_threshold: float = 0.20,
        use_boundary_model: bool = True
    ):
        """
        Initialize mispricing detector

        Args:
            bankroll: Total capital available for betting
            kelly_fraction: Fraction of Kelly criterion to use (0.25 = 1/4 Kelly)
            min_edge_threshold: Minimum edge required to flag opportunity (default 20%)
            use_boundary_model: Use enhanced boundary model for markets within ±3°F
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.min_edge_threshold = min_edge_threshold
        self.use_boundary_model = use_boundary_model
        self.logger = logging.getLogger(__name__)

        # Initialize boundary model if enabled
        if self.use_boundary_model:
            self.boundary_model = BoundaryForecastModel()
        else:
            self.boundary_model = None

    def analyze_temperature_market(
        self,
        market: Dict,
        parsed: ParsedMarket,
        forecast: Dict,
        current_conditions: Optional[Dict] = None,
        observations: Optional[List[Dict]] = None
    ) -> Optional[Opportunity]:
        """
        Analyze a temperature market for mispricing

        Args:
            market: Market data from Kalshi API
            parsed: Parsed market information
            forecast: Temperature forecast statistics
            current_conditions: Current weather conditions (for boundary model)
            observations: Recent temperature observations (for boundary model)

        Returns:
            Opportunity object if significant mispricing found, None otherwise
        """
        if not parsed.is_parseable:
            self.logger.debug(f"Skipping unparseable market: {market['ticker']}")
            return None

        # Map metric names: "minimum" → "min", "maximum" → "max", "average" → "avg"
        metric_map = {
            "minimum": "min",
            "maximum": "max",
            "average": "avg"
        }
        forecast_metric_key = metric_map.get(parsed.metric, parsed.metric)

        # Get forecast value for the relevant metric
        forecast_value = forecast.get(forecast_metric_key)
        if forecast_value is None:
            self.logger.warning(
                f"Forecast missing metric '{forecast_metric_key}' (parsed as '{parsed.metric}') "
                f"for {market['ticker']}"
            )
            return None

        # CRITICAL: Check if observations from today already determine the outcome
        # For intraday markets, once we've observed a certain min/max, that constrains the answer
        if forecast.get("includes_observations"):
            constrained_prob = self._check_observation_constraints(
                forecast=forecast,
                parsed=parsed,
                forecast_metric_key=forecast_metric_key
            )
            if constrained_prob is not None:
                # Observations definitively answer the question
                self.logger.info(
                    f"Market {market['ticker']} outcome constrained by observations: "
                    f"prob={constrained_prob:.1%}"
                )
                true_prob = constrained_prob
                # Skip probabilistic calculation - we know the answer from observations
            else:
                # Observations don't constrain - continue with normal probability calculation
                # Determine if this is a boundary case (within ±3°F of threshold)
                is_boundary_case = self._is_boundary_case(
                    forecast_value=forecast_value,
                    threshold=parsed.threshold,
                    threshold_high=parsed.threshold_high,
                    comparison=parsed.comparison
                )

                # Calculate true probability
                if is_boundary_case and self.boundary_model and (current_conditions or observations):
                    # Use enhanced boundary model
                    self.logger.info(f"Using boundary model for {market['ticker']} (boundary case)")
                    true_prob = self.boundary_model.calculate_boundary_probability(
                        forecast_value=forecast_value,
                        threshold=parsed.threshold,
                        threshold_high=parsed.threshold_high,
                        comparison=parsed.comparison,
                        current_conditions=current_conditions,
                        observations=observations,
                        forecast_stats=forecast
                    )
                else:
                    # Use simple heuristic model
                    true_prob = self._calculate_probability(
                        forecast_value=forecast_value,
                        threshold=parsed.threshold,
                        threshold_high=parsed.threshold_high,
                        comparison=parsed.comparison
                    )
        else:
            # No observations from today - use normal probability calculation
            # Determine if this is a boundary case (within ±3°F of threshold)
            is_boundary_case = self._is_boundary_case(
                forecast_value=forecast_value,
                threshold=parsed.threshold,
                threshold_high=parsed.threshold_high,
                comparison=parsed.comparison
            )

            # Calculate true probability
            if is_boundary_case and self.boundary_model and (current_conditions or observations):
                # Use enhanced boundary model
                self.logger.info(f"Using boundary model for {market['ticker']} (boundary case)")
                true_prob = self.boundary_model.calculate_boundary_probability(
                    forecast_value=forecast_value,
                    threshold=parsed.threshold,
                    threshold_high=parsed.threshold_high,
                    comparison=parsed.comparison,
                    current_conditions=current_conditions,
                    observations=observations,
                    forecast_stats=forecast
                )
            else:
                # Use simple heuristic model
                true_prob = self._calculate_probability(
                    forecast_value=forecast_value,
                    threshold=parsed.threshold,
                    threshold_high=parsed.threshold_high,
                    comparison=parsed.comparison
                )

        # Get market prices (Kalshi API returns prices in cents 0-100)
        # Convert to decimal form (0-1.0) by dividing by 100
        # Prefer bids (what we can get), but fall back to asks (what we'd pay) if no bids
        market_yes_bid = market.get("yes_bid", 0) / 100.0 if market.get("yes_bid", 0) else 0
        market_no_bid = market.get("no_bid", 0) / 100.0 if market.get("no_bid", 0) else 0
        market_yes_ask = market.get("yes_ask", 0) / 100.0 if market.get("yes_ask", 0) else 0
        market_no_ask = market.get("no_ask", 0) / 100.0 if market.get("no_ask", 0) else 0

        # Use bids if available, otherwise use asks
        market_yes_price = market_yes_bid if market_yes_bid > 0 else market_yes_ask
        market_no_price = market_no_bid if market_no_bid > 0 else market_no_ask

        # Track if we're using asks (lower liquidity)
        using_asks = (market_yes_bid == 0 or market_no_bid == 0)

        if market_yes_price == 0 or market_no_price == 0:
            self.logger.warning(f"Market {market['ticker']} has no bid or ask prices")
            return None

        # Calculate edge for both sides
        yes_edge = true_prob - market_yes_price
        no_edge = (1 - true_prob) - market_no_price

        # Determine which side (if any) has significant edge
        if yes_edge > self.min_edge_threshold:
            recommended_side = "YES"
            edge = yes_edge
            # We'd pay the ask to buy
            bet_price = market_yes_ask if market_yes_ask > 0 else market_yes_price
        elif no_edge > self.min_edge_threshold:
            recommended_side = "NO"
            edge = no_edge
            # We'd pay the ask to buy
            bet_price = market_no_ask if market_no_ask > 0 else market_no_price
        else:
            # No significant edge
            self.logger.debug(
                f"No opportunity in {market['ticker']}: "
                f"yes_edge={yes_edge:.1%}, no_edge={no_edge:.1%}"
            )
            return None

        # Calculate position size using Kelly criterion
        bet_size = self._kelly_bet_size(
            edge=edge,
            price=bet_price,
            bankroll=self.bankroll,
            kelly_fraction=self.kelly_fraction
        )

        # Calculate confidence
        confidence = self._calculate_confidence(forecast, parsed)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            parsed=parsed,
            forecast=forecast,
            true_prob=true_prob,
            market_price=market_yes_price if recommended_side == "YES" else market_no_price,
            recommended_side=recommended_side
        )

        # Add liquidity warning if using asks
        if using_asks:
            reasoning += " [LOW LIQUIDITY: No bids available, using ask prices]"

        # Create opportunity
        return Opportunity(
            ticker=market["ticker"],
            title=market["title"],
            location=parsed.location,
            date=parsed.date,
            market_yes_price=market_yes_price,
            market_no_price=market_no_price,
            forecast_min=forecast["min"],
            forecast_max=forecast["max"],
            forecast_avg=forecast["avg"],
            true_probability=true_prob,
            edge=edge,
            recommended_side=recommended_side,
            recommended_bet_size=bet_size,
            confidence=confidence,
            reasoning=reasoning,
            data_source="NWS",
            liquidity_pool_size=(market.get("liquidity_pool") or {}).get("pool_size", 0),
            close_time=datetime.fromisoformat(market["close_time"].replace('Z', '+00:00'))
        )

    def _check_observation_constraints(
        self,
        forecast: Dict,
        parsed: ParsedMarket,
        forecast_metric_key: str
    ) -> Optional[float]:
        """
        Check if observations from today already determine the market outcome

        Key insight: Minimums can only go lower, maximums can only go higher
        - If observed_min < threshold and market asks "min > threshold" → Definite NO
        - If observed_max > threshold and market asks "max < threshold" → Definite NO

        Args:
            forecast: Forecast dict with min/max/avg and includes_observations flag
            parsed: Parsed market information
            forecast_metric_key: The metric key to use ("min", "max", or "avg")

        Returns:
            Probability if constrained (0.05 for NO, 0.95 for YES), None if not constrained
        """
        observed_value = forecast.get(forecast_metric_key)
        if observed_value is None:
            return None

        threshold = parsed.threshold
        threshold_high = parsed.threshold_high
        comparison = parsed.comparison

        # For MINIMUM temperature markets
        if parsed.metric == "minimum":
            if comparison in ["above", "at least"]:
                # Market asks: "Will minimum be >= threshold?"
                # If observed_min < threshold, minimum is ALREADY below threshold
                # Minimum can only go lower, so answer is definitely NO
                if observed_value < threshold:
                    self.logger.info(
                        f"Observed minimum {observed_value:.1f}°F < {threshold}°F "
                        f"(minimum can only go lower) → Definite NO"
                    )
                    return 0.05  # Definite NO (5% for uncertainty)

            elif comparison == "below":
                # Market asks: "Will minimum be < threshold?"
                # If observed_min < threshold, answer is ALREADY YES
                if observed_value < threshold:
                    self.logger.info(
                        f"Observed minimum {observed_value:.1f}°F < {threshold}°F "
                        f"(already below) → Definite YES"
                    )
                    return 0.95  # Definite YES

            elif comparison == "between":
                # Market asks: "Will minimum be between threshold and threshold_high?"
                # If observed_min < threshold, minimum is ALREADY too low
                if observed_value < threshold:
                    self.logger.info(
                        f"Observed minimum {observed_value:.1f}°F < {threshold}°F "
                        f"(already below range) → Definite NO"
                    )
                    return 0.05  # Definite NO
                # If observed_min > threshold_high, minimum is ALREADY too high
                # (but minimum can still drop into range)
                # So we DON'T constrain this case

        # For MAXIMUM temperature markets
        elif parsed.metric == "maximum":
            if comparison in ["above", "at least"]:
                # Market asks: "Will maximum be >= threshold?"
                # If observed_max >= threshold, answer is ALREADY YES
                if observed_value >= threshold:
                    self.logger.info(
                        f"Observed maximum {observed_value:.1f}°F >= {threshold}°F "
                        f"(already above) → Definite YES"
                    )
                    return 0.95  # Definite YES

            elif comparison == "below":
                # Market asks: "Will maximum be < threshold?"
                # If observed_max >= threshold, maximum is ALREADY at/above threshold
                # Maximum can only go higher, so answer is definitely NO
                if observed_value >= threshold:
                    self.logger.info(
                        f"Observed maximum {observed_value:.1f}°F >= {threshold}°F "
                        f"(maximum can only go higher) → Definite NO"
                    )
                    return 0.05  # Definite NO

            elif comparison == "between":
                # Market asks: "Will maximum be between threshold and threshold_high?"
                # If observed_max > threshold_high, maximum is ALREADY too high
                if threshold_high and observed_value > threshold_high:
                    self.logger.info(
                        f"Observed maximum {observed_value:.1f}°F > {threshold_high}°F "
                        f"(already above range) → Definite NO"
                    )
                    return 0.05  # Definite NO
                # If observed_max < threshold, maximum might still rise into range
                # So we DON'T constrain this case

        # No constraints apply - observations don't definitively answer the question
        return None

    def _is_boundary_case(
        self,
        forecast_value: float,
        threshold: float,
        threshold_high: Optional[float],
        comparison: str,
        boundary_distance: float = 3.0
    ) -> bool:
        """
        Determine if market is a boundary case (within ±3°F of threshold)

        Args:
            forecast_value: NWS forecast temperature
            threshold: Market threshold
            threshold_high: Upper threshold (for "between" markets)
            comparison: Comparison operator
            boundary_distance: Distance threshold in °F (default 3.0)

        Returns:
            True if within boundary distance, False otherwise
        """
        if comparison in ["above", "at least", "below"]:
            # Check distance to single threshold
            distance = abs(forecast_value - threshold)
            return distance <= boundary_distance

        elif comparison == "between":
            # Check distance to nearest boundary
            distance_to_lower = abs(forecast_value - threshold)
            distance_to_upper = abs(forecast_value - threshold_high) if threshold_high else float('inf')
            min_distance = min(distance_to_lower, distance_to_upper)
            return min_distance <= boundary_distance

        return False

    def _calculate_probability(
        self,
        forecast_value: float,
        threshold: float,
        threshold_high: Optional[float],
        comparison: str
    ) -> float:
        """
        Calculate true probability based on forecast and threshold

        Weather forecasts have ~2-3°F error margin, so we account for uncertainty.

        Args:
            forecast_value: Forecasted temperature (min/max/avg)
            threshold: Temperature threshold from market
            threshold_high: Upper threshold (for "between" comparisons)
            comparison: Comparison operator ("above", "below", "between")

        Returns:
            Probability between 0 and 1
        """
        if comparison in ["above", "at least"]:
            # Question: Will temp be >= threshold?
            distance = forecast_value - threshold

            if distance > 5:
                return 0.95  # Very confident YES
            elif distance > 2:
                return 0.85  # Confident YES
            elif distance > 0:
                return 0.70  # Likely YES, but within error margin
            elif distance > -2:
                return 0.50  # Uncertain (within forecast error)
            elif distance > -5:
                return 0.15  # Unlikely
            else:
                return 0.05  # Very unlikely

        elif comparison == "below":
            # Question: Will temp be < threshold?
            distance = threshold - forecast_value

            if distance > 5:
                return 0.95  # Very confident YES
            elif distance > 2:
                return 0.85  # Confident YES
            elif distance > 0:
                return 0.70  # Likely YES, but within error margin
            elif distance > -2:
                return 0.50  # Uncertain
            elif distance > -5:
                return 0.15  # Unlikely
            else:
                return 0.05  # Very unlikely

        elif comparison == "between":
            # Question: Will threshold <= temp <= threshold_high?
            if threshold <= forecast_value <= threshold_high:
                # Forecast is within range
                margin = min(forecast_value - threshold, threshold_high - forecast_value)

                if margin > 3:
                    return 0.90  # Well within range
                elif margin > 1:
                    return 0.75  # Within range but near edge
                else:
                    return 0.60  # Just barely in range

            elif forecast_value < threshold:
                # Below range
                distance = threshold - forecast_value

                if distance < 2:
                    return 0.40  # Close to lower bound
                elif distance < 5:
                    return 0.15
                else:
                    return 0.05
            else:
                # Above range
                distance = forecast_value - threshold_high

                if distance < 2:
                    return 0.40  # Close to upper bound
                elif distance < 5:
                    return 0.15
                else:
                    return 0.05

        else:
            self.logger.warning(f"Unknown comparison operator: {comparison}")
            return 0.50  # Default to uncertain

    def _kelly_bet_size(
        self,
        edge: float,
        price: float,
        bankroll: float,
        kelly_fraction: float
    ) -> float:
        """
        Calculate optimal bet size using fractional Kelly criterion

        Args:
            edge: Our edge (true_prob - market_price)
            price: Price we'd pay for the bet
            bankroll: Total capital available
            kelly_fraction: Fraction of Kelly to use (0.25 = 1/4 Kelly)

        Returns:
            Recommended bet size in dollars
        """
        # Simplified Kelly for prediction markets: edge * fraction * bankroll
        kelly_pct = kelly_fraction * edge
        bet_amount = kelly_pct * bankroll

        # Cap at 5% of bankroll per bet (risk management)
        max_bet = 0.05 * bankroll

        # Minimum bet of $1
        min_bet = 1.0

        return max(min_bet, min(bet_amount, max_bet))

    def _calculate_confidence(
        self,
        forecast: Dict,
        parsed: ParsedMarket
    ) -> float:
        """
        Calculate confidence in our probability estimate

        Factors:
        1. Time until event (closer = more confident)
        2. Distance from threshold (further = more confident)

        Args:
            forecast: Forecast data
            parsed: Parsed market information

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence for NWS forecasts
        base_confidence = 0.80

        # Adjust based on time until event
        days_until = (parsed.date - datetime.now().date()).days

        if days_until == 0:
            time_confidence = 0.95  # Today's forecast is very reliable
        elif days_until == 1:
            time_confidence = 0.90
        elif days_until <= 3:
            time_confidence = 0.80
        elif days_until <= 5:
            time_confidence = 0.70
        else:
            time_confidence = 0.60  # 6+ days out, more uncertainty

        # Adjust based on distance from threshold
        # Map metric names: "minimum" → "min", "maximum" → "max", "average" → "avg"
        metric_map = {
            "minimum": "min",
            "maximum": "max",
            "average": "avg"
        }
        forecast_metric_key = metric_map.get(parsed.metric, parsed.metric)
        forecast_value = forecast.get(forecast_metric_key, 0)

        if parsed.comparison == "between":
            # For "between", check distance to nearest boundary
            distance_to_lower = abs(forecast_value - parsed.threshold)
            distance_to_upper = abs(forecast_value - parsed.threshold_high) if parsed.threshold_high else float('inf')
            distance = min(distance_to_lower, distance_to_upper)
        else:
            distance = abs(forecast_value - parsed.threshold)

        if distance > 5:
            distance_confidence = 0.95  # Very clear
        elif distance > 3:
            distance_confidence = 0.85
        elif distance > 1:
            distance_confidence = 0.70
        else:
            distance_confidence = 0.50  # Too close to threshold

        # Combined confidence (geometric mean)
        return math.sqrt(time_confidence * distance_confidence)

    def _generate_reasoning(
        self,
        parsed: ParsedMarket,
        forecast: Dict,
        true_prob: float,
        market_price: float,
        recommended_side: str
    ) -> str:
        """
        Generate human-readable reasoning for the opportunity

        Args:
            parsed: Parsed market information
            forecast: Forecast data
            true_prob: Our calculated probability
            market_price: Current market price
            recommended_side: Which side we recommend

        Returns:
            Reasoning string
        """
        # Map metric names: "minimum" → "min", "maximum" → "max", "average" → "avg"
        metric_map = {
            "minimum": "min",
            "maximum": "max",
            "average": "avg"
        }
        forecast_metric_key = metric_map.get(parsed.metric, parsed.metric)
        forecast_value = forecast.get(forecast_metric_key, 0)

        metric_str = f"forecast {parsed.metric}"

        reasoning_parts = []

        # State the forecast
        reasoning_parts.append(
            f"NWS forecasts {metric_str} of {forecast_value:.1f}°F for "
            f"{parsed.location} on {parsed.date.strftime('%B %d')}"
        )

        # State the threshold
        if parsed.comparison == "between":
            reasoning_parts.append(
                f"Market asks if temp will be between {parsed.threshold:.0f}° and "
                f"{parsed.threshold_high:.0f}°"
            )
        else:
            reasoning_parts.append(
                f"Market asks if temp will be {parsed.comparison} {parsed.threshold:.0f}°"
            )

        # State the mispricing
        reasoning_parts.append(
            f"Market prices this at {market_price:.0%}, but forecast suggests "
            f"{true_prob:.0%} probability"
        )

        # Explain the edge
        edge = abs(true_prob - market_price)
        reasoning_parts.append(
            f"This represents a {edge:.0%} edge on the {recommended_side} side"
        )

        return ". ".join(reasoning_parts) + "."
