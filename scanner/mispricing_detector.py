"""
Mispricing Detector
Compares market prices against NWS forecast data to identify arbitrage opportunities
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Optional

from .market_parser import ParsedMarket


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


class MispricingDetector:
    """Detects mispricings by comparing market prices to forecast data"""

    def __init__(
        self,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.25,
        min_edge_threshold: float = 0.20
    ):
        """
        Initialize mispricing detector

        Args:
            bankroll: Total capital available for betting
            kelly_fraction: Fraction of Kelly criterion to use (0.25 = 1/4 Kelly)
            min_edge_threshold: Minimum edge required to flag opportunity (default 20%)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.min_edge_threshold = min_edge_threshold
        self.logger = logging.getLogger(__name__)

    def analyze_temperature_market(
        self,
        market: Dict,
        parsed: ParsedMarket,
        forecast: Dict
    ) -> Optional[Opportunity]:
        """
        Analyze a temperature market for mispricing

        Args:
            market: Market data from Kalshi API
            parsed: Parsed market information
            forecast: Temperature forecast statistics

        Returns:
            Opportunity object if significant mispricing found, None otherwise
        """
        if not parsed.is_parseable:
            self.logger.debug(f"Skipping unparseable market: {market['ticker']}")
            return None

        # Get forecast value for the relevant metric
        forecast_value = forecast.get(parsed.metric)
        if forecast_value is None:
            self.logger.warning(f"Forecast missing metric '{parsed.metric}' for {market['ticker']}")
            return None

        # Calculate true probability based on forecast
        true_prob = self._calculate_probability(
            forecast_value=forecast_value,
            threshold=parsed.threshold,
            threshold_high=parsed.threshold_high,
            comparison=parsed.comparison
        )

        # Get market prices (use bids since that's what we can actually get)
        market_yes_price = market.get("yes_bid", 0)
        market_no_price = market.get("no_bid", 0)

        if market_yes_price == 0 or market_no_price == 0:
            self.logger.warning(f"Market {market['ticker']} has zero bid prices")
            return None

        # Calculate edge for both sides
        yes_edge = true_prob - market_yes_price
        no_edge = (1 - true_prob) - market_no_price

        # Determine which side (if any) has significant edge
        if yes_edge > self.min_edge_threshold:
            recommended_side = "YES"
            edge = yes_edge
            bet_price = market.get("yes_ask", market_yes_price)  # We'd pay the ask
        elif no_edge > self.min_edge_threshold:
            recommended_side = "NO"
            edge = no_edge
            bet_price = market.get("no_ask", market_no_price)
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
            liquidity_pool_size=market.get("liquidity_pool", {}).get("pool_size", 0),
            close_time=datetime.fromisoformat(market["close_time"].replace('Z', '+00:00'))
        )

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
        forecast_value = forecast[parsed.metric]

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
        metric_str = f"forecast {parsed.metric}"
        forecast_value = forecast[parsed.metric]

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
