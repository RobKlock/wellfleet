"""
Market Parser
Extracts structured data from Kalshi market titles
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date


@dataclass
class ParsedMarket:
    """Structured representation of a parsed market"""
    ticker: str
    location: Optional[str] = None
    metric: Optional[str] = None  # "minimum", "maximum", "average"
    comparison: Optional[str] = None  # "above", "below", "between"
    threshold: Optional[float] = None
    threshold_high: Optional[float] = None  # For "between" comparisons
    date: Optional[date] = None
    is_parseable: bool = False

    def __str__(self):
        if not self.is_parseable:
            return f"ParsedMarket(ticker={self.ticker}, unparseable)"

        if self.comparison == "between":
            return (
                f"ParsedMarket({self.location}, {self.metric} {self.comparison} "
                f"{self.threshold}°-{self.threshold_high}° on {self.date})"
            )
        else:
            return (
                f"ParsedMarket({self.location}, {self.metric} {self.comparison} "
                f"{self.threshold}° on {self.date})"
            )


class MarketParser:
    """Parser for extracting structured data from Kalshi market titles"""

    # Pattern 1: Simple threshold (above/below)
    # Example: "Will the minimum temperature in Denver, CO be 31° or above on January 12, 2026?"
    PATTERN_SIMPLE = re.compile(
        r"Will the (minimum|maximum|average) temperature in ([A-Za-z\s,]+?) "
        r"be (\d+)°? or (above|below) on ([A-Za-z]+ \d+, \d{4})",
        re.IGNORECASE
    )

    # Pattern 2: Range (between X and Y)
    # Example: "Will the minimum temperature in Miami, FL be between 65° and 70° on January 15, 2026?"
    PATTERN_RANGE = re.compile(
        r"Will the (minimum|maximum|average) temperature in ([A-Za-z\s,]+?) "
        r"be between (\d+)°? and (\d+)°? on ([A-Za-z]+ \d+, \d{4})",
        re.IGNORECASE
    )

    # Pattern 3: Alternative phrasing with "at least" / "at most"
    # Example: "Will the minimum temperature in Denver, CO be at least 31° on January 12, 2026?"
    PATTERN_AT_LEAST = re.compile(
        r"Will the (minimum|maximum|average) temperature in ([A-Za-z\s,]+?) "
        r"be at (least|most) (\d+)°? on ([A-Za-z]+ \d+, \d{4})",
        re.IGNORECASE
    )

    # Pattern 4: "Lowest/Highest temperature" format
    # Example: "Will the lowest temperature in Denver be 26° or below on January 16?"
    # Example ticker: KXLOWTDEN-26JAN16
    PATTERN_LOWEST_HIGHEST = re.compile(
        r"Will the (lowest|highest|average) temperature in ([A-Za-z\s,]+?) "
        r"be (\d+)°? or (below|above) on ([A-Za-z]+ \d+)",
        re.IGNORECASE
    )

    # Pattern 5: Compact format without location (>X°, <X°, X-Y°)
    # Example: "Will the minimum temperature be  >20° on Jan 17, 2026?"
    # Example: "Will the minimum temperature be  <13° on Jan 17, 2026?"
    # Example: "Will the minimum temperature be  19-20° on Jan 17, 2026?"
    PATTERN_COMPACT = re.compile(
        r"Will the (minimum|maximum|average) temperature be\s+([><])?(\d+)(?:-(\d+))?°?\s+on ([A-Za-z]+ \d+, \d{4})",
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize the market parser"""
        self.logger = logging.getLogger(__name__)

    def parse(self, title: str, ticker: str) -> ParsedMarket:
        """
        Parse a market title to extract structured information

        Args:
            title: Market title string
            ticker: Market ticker symbol

        Returns:
            ParsedMarket object with extracted information
        """
        # Try Pattern 1: Simple threshold (above/below)
        match = self.PATTERN_SIMPLE.search(title)
        if match:
            return self._parse_simple_threshold(match, ticker)

        # Try Pattern 2: Range (between)
        match = self.PATTERN_RANGE.search(title)
        if match:
            return self._parse_range(match, ticker)

        # Try Pattern 3: At least/most
        match = self.PATTERN_AT_LEAST.search(title)
        if match:
            return self._parse_at_least_most(match, ticker)

        # Try Pattern 4: Lowest/Highest (without year)
        match = self.PATTERN_LOWEST_HIGHEST.search(title)
        if match:
            return self._parse_lowest_highest(match, ticker)

        # Try Pattern 5: Compact format (>X°, <X°, X-Y°)
        match = self.PATTERN_COMPACT.search(title)
        if match:
            return self._parse_compact(match, ticker)

        # Unable to parse
        self.logger.warning(f"Unable to parse market title: {title}")
        return ParsedMarket(ticker=ticker, is_parseable=False)

    def _parse_simple_threshold(self, match: re.Match, ticker: str) -> ParsedMarket:
        """Parse simple threshold pattern (above/below)"""
        try:
            metric = match.group(1).lower()
            location = match.group(2).strip()
            threshold = float(match.group(3))
            comparison = match.group(4).lower()
            date_str = match.group(5)

            # Parse date
            parsed_date = datetime.strptime(date_str, "%B %d, %Y").date()

            return ParsedMarket(
                ticker=ticker,
                location=location,
                metric=metric,
                threshold=threshold,
                comparison=comparison,
                date=parsed_date,
                is_parseable=True
            )
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing simple threshold: {e}")
            return ParsedMarket(ticker=ticker, is_parseable=False)

    def _parse_range(self, match: re.Match, ticker: str) -> ParsedMarket:
        """Parse range pattern (between X and Y)"""
        try:
            metric = match.group(1).lower()
            location = match.group(2).strip()
            threshold_low = float(match.group(3))
            threshold_high = float(match.group(4))
            date_str = match.group(5)

            # Parse date
            parsed_date = datetime.strptime(date_str, "%B %d, %Y").date()

            return ParsedMarket(
                ticker=ticker,
                location=location,
                metric=metric,
                threshold=threshold_low,
                threshold_high=threshold_high,
                comparison="between",
                date=parsed_date,
                is_parseable=True
            )
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing range: {e}")
            return ParsedMarket(ticker=ticker, is_parseable=False)

    def _parse_at_least_most(self, match: re.Match, ticker: str) -> ParsedMarket:
        """Parse 'at least' / 'at most' pattern"""
        try:
            metric = match.group(1).lower()
            location = match.group(2).strip()
            modifier = match.group(3).lower()  # "least" or "most"
            threshold = float(match.group(4))
            date_str = match.group(5)

            # Parse date
            parsed_date = datetime.strptime(date_str, "%B %d, %Y").date()

            # Convert "at least" to "above" and "at most" to "below"
            comparison = "above" if modifier == "least" else "below"

            return ParsedMarket(
                ticker=ticker,
                location=location,
                metric=metric,
                threshold=threshold,
                comparison=comparison,
                date=parsed_date,
                is_parseable=True
            )
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing at least/most: {e}")
            return ParsedMarket(ticker=ticker, is_parseable=False)

    def _parse_lowest_highest(self, match: re.Match, ticker: str) -> ParsedMarket:
        """Parse 'lowest/highest temperature' pattern (without year in date)"""
        try:
            metric_word = match.group(1).lower()  # "lowest", "highest", or "average"
            location = match.group(2).strip()
            threshold = float(match.group(3))
            comparison = match.group(4).lower()  # "below" or "above"
            date_str = match.group(5)  # e.g., "January 16"

            # Convert metric word to standard form
            if metric_word == "lowest":
                metric = "minimum"
            elif metric_word == "highest":
                metric = "maximum"
            else:
                metric = "average"

            # Parse date - add current year since it's not specified
            # Format is "January 16" without year
            current_year = datetime.now().year
            try:
                parsed_date = datetime.strptime(f"{date_str}, {current_year}", "%B %d, %Y").date()
            except ValueError:
                # If that fails, try next year (for dates that might have rolled over)
                parsed_date = datetime.strptime(f"{date_str}, {current_year + 1}", "%B %d, %Y").date()

            # Add state if just city name (Denver -> Denver, CO; Miami -> Miami, FL)
            if "," not in location:
                if "denver" in location.lower():
                    location = "Denver, CO"
                elif "miami" in location.lower():
                    location = "Miami, FL"

            return ParsedMarket(
                ticker=ticker,
                location=location,
                metric=metric,
                threshold=threshold,
                comparison=comparison,
                date=parsed_date,
                is_parseable=True
            )
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing lowest/highest: {e}")
            return ParsedMarket(ticker=ticker, is_parseable=False)

    def _parse_compact(self, match: re.Match, ticker: str) -> ParsedMarket:
        """Parse compact format without location (>X°, <X°, X-Y°)"""
        try:
            metric = match.group(1).lower()  # "minimum", "maximum", or "average"
            comparison_symbol = match.group(2)  # ">", "<", or None
            threshold_low = float(match.group(3))
            threshold_high_str = match.group(4)  # For range format like "19-20"
            date_str = match.group(5)  # e.g., "Jan 17, 2026"

            # Parse date
            parsed_date = datetime.strptime(date_str, "%b %d, %Y").date()

            # Infer location from ticker
            # KXLOWTDEN → Denver, CO
            # KXLOWTMIA → Miami, FL
            location = None
            if "DEN" in ticker.upper():
                location = "Denver, CO"
            elif "MIA" in ticker.upper():
                location = "Miami, FL"
            else:
                self.logger.warning(f"Cannot infer location from ticker: {ticker}")
                return ParsedMarket(ticker=ticker, is_parseable=False)

            # Determine comparison type and thresholds
            if threshold_high_str:
                # Range format: "19-20"
                threshold_high = float(threshold_high_str)
                comparison = "between"
                threshold = threshold_low
            elif comparison_symbol == ">":
                # Greater than: ">20" (strictly greater, means ≥21 for integers)
                # Normalize to "at least" form by adding 1
                comparison = "at least"
                threshold = threshold_low + 1
                threshold_high = None
            elif comparison_symbol == "<":
                # Less than: "<13" (strictly less, means ≤12 for integers)
                # Normalize to "at most" form by subtracting 1
                comparison = "at most"
                threshold = threshold_low - 1
                threshold_high = None
            else:
                # No symbol - unclear, skip
                self.logger.warning(f"Cannot determine comparison for: {ticker}")
                return ParsedMarket(ticker=ticker, is_parseable=False)

            return ParsedMarket(
                ticker=ticker,
                location=location,
                metric=metric,
                threshold=threshold,
                threshold_high=threshold_high,
                comparison=comparison,
                date=parsed_date,
                is_parseable=True
            )
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error parsing compact format: {e}")
            return ParsedMarket(ticker=ticker, is_parseable=False)
