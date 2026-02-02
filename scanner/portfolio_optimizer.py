"""
Portfolio Optimizer
Analyzes correlated markets and suggests optimal allocation strategies with hedging
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import math

from .mispricing_detector import Opportunity


@dataclass
class PortfolioGroup:
    """Group of correlated markets (same location, date, and metric)"""
    location: str
    date: date
    metric: str  # "minimum", "maximum", or "average"
    opportunities: List[Opportunity]

    # Portfolio metrics
    total_edge: float
    expected_return: float
    min_return: float
    max_return: float
    recommended_allocation: float
    sharpe_ratio: float

    # Risk metrics
    variance: float
    std_dev: float
    max_drawdown: float

    # Hedging strategy
    primary_bet: Optional[Opportunity] = None
    hedge_bets: List[Tuple[Opportunity, float]] = None  # [(opp, allocation_weight), ...]
    hedge_description: str = ""


@dataclass
class HedgingStrategy:
    """Recommended hedging strategy for a portfolio group"""
    primary: Opportunity
    hedges: List[Tuple[Opportunity, float, str]]  # [(opp, dollars, reason), ...]
    total_investment: float
    expected_return_range: Tuple[float, float]  # (min, max)
    risk_level: str  # "Low", "Medium", "High"
    confidence: float
    description: str


class PortfolioOptimizer:
    """
    Analyzes correlated markets and suggests optimal portfolio allocation

    Temperature markets for the same location/date/metric are perfectly correlated
    since they all settle based on the same observed value. This creates opportunities
    for hedging and portfolio optimization.
    """

    def __init__(self, bankroll: float = 1000.0):
        """
        Initialize portfolio optimizer

        Args:
            bankroll: Total available capital for allocation
        """
        self.bankroll = bankroll
        self.logger = logging.getLogger(__name__)

    def group_correlated_markets(
        self,
        opportunities: List[Opportunity]
    ) -> List[PortfolioGroup]:
        """
        Group opportunities by correlation (same location, date, and metric)

        Args:
            opportunities: List of identified opportunities

        Returns:
            List of portfolio groups with correlated markets
        """
        # Group by (location, date, metric)
        groups = defaultdict(list)

        for opp in opportunities:
            # Extract metric from ticker or use a default grouping
            # For temperature markets, we can infer from the ticker pattern
            key = (opp.location, opp.date, self._infer_metric(opp))
            groups[key].append(opp)

        # Convert to PortfolioGroup objects
        portfolio_groups = []

        for (location, date_val, metric), opps in groups.items():
            if len(opps) < 2:
                # Not interesting for hedging if only one market
                continue

            # Sort by edge (best to worst)
            opps_sorted = sorted(opps, key=lambda x: x.edge, reverse=True)

            # Calculate portfolio metrics
            group = self._analyze_portfolio_group(location, date_val, metric, opps_sorted)
            portfolio_groups.append(group)

        # Sort groups by Sharpe ratio (best risk-adjusted returns first)
        return sorted(portfolio_groups, key=lambda g: g.sharpe_ratio, reverse=True)

    def _infer_metric(self, opp: Opportunity) -> str:
        """Infer metric (min/max/avg) from ticker"""
        ticker = opp.ticker.upper()

        if "LOW" in ticker or "MIN" in ticker:
            return "minimum"
        elif "HIGH" in ticker or "MAX" in ticker:
            return "maximum"
        elif "AVG" in ticker or "MEAN" in ticker:
            return "average"
        else:
            # Default: check forecast values to guess
            if abs(opp.forecast_min - opp.forecast_max) < 5:
                return "average"  # Small range, probably average temp
            else:
                return "minimum"  # Default to minimum

    def _analyze_portfolio_group(
        self,
        location: str,
        date_val: date,
        metric: str,
        opportunities: List[Opportunity]
    ) -> PortfolioGroup:
        """
        Analyze a group of correlated markets

        Args:
            location: Location (e.g., "Denver, CO")
            date_val: Market date
            metric: Metric type (minimum/maximum/average)
            opportunities: List of opportunities in this group

        Returns:
            PortfolioGroup with calculated metrics
        """
        # Calculate total edge
        total_edge = sum(opp.edge for opp in opportunities)

        # Find primary bet (highest edge with reasonable liquidity)
        primary = self._select_primary_bet(opportunities)

        # Calculate optimal allocation
        recommended_allocation = self._calculate_optimal_allocation(opportunities)

        # Calculate expected returns
        expected_return, min_return, max_return = self._calculate_return_range(
            opportunities,
            recommended_allocation
        )

        # Calculate risk metrics
        variance, std_dev = self._calculate_risk_metrics(opportunities, recommended_allocation)
        max_drawdown = self._calculate_max_drawdown(opportunities, recommended_allocation)

        # Calculate Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = expected_return / std_dev if std_dev > 0 else 0

        # Generate hedging strategy
        hedge_bets, hedge_description = self._generate_hedging_strategy(
            opportunities,
            primary,
            recommended_allocation
        )

        return PortfolioGroup(
            location=location,
            date=date_val,
            metric=metric,
            opportunities=opportunities,
            total_edge=total_edge,
            expected_return=expected_return,
            min_return=min_return,
            max_return=max_return,
            recommended_allocation=recommended_allocation,
            sharpe_ratio=sharpe_ratio,
            variance=variance,
            std_dev=std_dev,
            max_drawdown=max_drawdown,
            primary_bet=primary,
            hedge_bets=hedge_bets,
            hedge_description=hedge_description
        )

    def _select_primary_bet(self, opportunities: List[Opportunity]) -> Opportunity:
        """
        Select the primary bet (highest edge with sufficient liquidity)

        Args:
            opportunities: List of opportunities sorted by edge

        Returns:
            Primary opportunity to bet on
        """
        # Prefer high edge with decent liquidity
        for opp in opportunities:
            if opp.edge > 0.1:  # At least 10% edge
                return opp

        # Fall back to highest edge
        return opportunities[0] if opportunities else None

    def _calculate_optimal_allocation(self, opportunities: List[Opportunity]) -> float:
        """
        Calculate optimal portfolio allocation using Kelly criterion

        Args:
            opportunities: List of opportunities

        Returns:
            Recommended total allocation as fraction of bankroll
        """
        # Use fractional Kelly for the portfolio
        # Sum of individual Kelly fractions, capped at reasonable limits
        total_kelly = sum(
            opp.recommended_bet_size / self.bankroll
            for opp in opportunities
            if opp.edge > 0
        )

        # Cap at 20% of bankroll for safety (diversification across dates)
        return min(total_kelly, 0.20)

    def _calculate_return_range(
        self,
        opportunities: List[Opportunity],
        allocation_fraction: float
    ) -> Tuple[float, float, float]:
        """
        Calculate expected return range for the portfolio

        Args:
            opportunities: List of opportunities
            allocation_fraction: Fraction of bankroll to allocate

        Returns:
            Tuple of (expected_return, min_return, max_return) in dollars
        """
        total_allocation = allocation_fraction * self.bankroll

        # Calculate expected value
        expected_return = sum(
            opp.edge * opp.recommended_bet_size
            for opp in opportunities
            if opp.edge > 0
        )

        # Best case: All positive edge bets win
        max_return = sum(
            (1.0 / (opp.market_yes_price if opp.recommended_side == "YES" else opp.market_no_price) - 1.0) * opp.recommended_bet_size
            for opp in opportunities
            if opp.edge > 0
        )

        # Worst case: All bets lose
        min_return = -sum(
            opp.recommended_bet_size
            for opp in opportunities
            if opp.edge > 0
        )

        return expected_return, min_return, max_return

    def _calculate_risk_metrics(
        self,
        opportunities: List[Opportunity],
        allocation_fraction: float
    ) -> Tuple[float, float]:
        """
        Calculate portfolio variance and standard deviation

        Args:
            opportunities: List of opportunities
            allocation_fraction: Fraction of bankroll allocated

        Returns:
            Tuple of (variance, std_dev) in dollars
        """
        # For perfectly correlated markets (temperature ranges), variance is tricky
        # We'll use a simplified approach based on confidence levels

        total_allocation = allocation_fraction * self.bankroll

        # Weighted variance based on confidence
        weighted_variance = sum(
            (opp.recommended_bet_size ** 2) * (1 - opp.confidence)
            for opp in opportunities
        )

        std_dev = math.sqrt(weighted_variance)

        return weighted_variance, std_dev

    def _calculate_max_drawdown(
        self,
        opportunities: List[Opportunity],
        allocation_fraction: float
    ) -> float:
        """
        Calculate maximum potential loss (worst case scenario)

        Args:
            opportunities: List of opportunities
            allocation_fraction: Fraction of bankroll allocated

        Returns:
            Maximum drawdown in dollars
        """
        # Worst case: all bets lose
        return sum(
            opp.recommended_bet_size
            for opp in opportunities
            if opp.edge > 0
        )

    def _generate_hedging_strategy(
        self,
        opportunities: List[Opportunity],
        primary: Opportunity,
        allocation_fraction: float
    ) -> Tuple[List[Tuple[Opportunity, float]], str]:
        """
        Generate hedging strategy recommendations

        Args:
            opportunities: List of opportunities
            primary: Primary bet
            allocation_fraction: Total allocation fraction

        Returns:
            Tuple of (hedge_bets, description)
            hedge_bets: List of (opportunity, weight) tuples
            description: Human-readable hedging strategy
        """
        if not primary:
            return [], "No primary bet identified"

        hedge_bets = []
        total_allocation = allocation_fraction * self.bankroll

        # Find complementary bets (opposite side or adjacent ranges)
        for opp in opportunities:
            if opp.ticker == primary.ticker:
                continue

            # Check if this is a good hedge
            if opp.edge > 0.05:  # At least 5% edge
                # Calculate hedge weight (proportional to edge)
                weight = (opp.edge / sum(o.edge for o in opportunities if o.edge > 0))
                hedge_bets.append((opp, weight))

        # Generate description
        if not hedge_bets:
            description = f"Single position: {primary.ticker} {primary.recommended_side}"
        elif len(hedge_bets) == 1:
            hedge_opp, weight = hedge_bets[0]
            description = (
                f"Primary: {primary.ticker} {primary.recommended_side} (80% weight)\n"
                f"Hedge: {hedge_opp.ticker} {hedge_opp.recommended_side} (20% weight)"
            )
        else:
            description = (
                f"Primary: {primary.ticker} {primary.recommended_side}\n"
                f"Hedges: {len(hedge_bets)} complementary positions for portfolio diversification"
            )

        return hedge_bets, description

    def generate_hedging_strategy(
        self,
        group: PortfolioGroup,
        budget: float
    ) -> HedgingStrategy:
        """
        Generate detailed hedging strategy for a portfolio group

        Args:
            group: Portfolio group to analyze
            budget: Total budget to allocate

        Returns:
            HedgingStrategy with detailed recommendations
        """
        if not group.primary_bet:
            return None

        primary = group.primary_bet

        # Allocate budget: 60% to primary, 40% to hedges
        primary_allocation = budget * 0.60
        hedge_budget = budget * 0.40

        hedges = []

        # Sort opportunities by edge (excluding primary)
        other_opps = [opp for opp in group.opportunities if opp.ticker != primary.ticker]
        other_opps_sorted = sorted(other_opps, key=lambda x: x.edge, reverse=True)

        # Allocate hedge budget proportionally
        if other_opps_sorted:
            total_edge = sum(max(opp.edge, 0) for opp in other_opps_sorted)

            for opp in other_opps_sorted[:3]:  # Top 3 hedges
                if opp.edge > 0:
                    allocation = hedge_budget * (opp.edge / total_edge) if total_edge > 0 else 0

                    # Determine hedge reason
                    if opp.recommended_side != primary.recommended_side:
                        reason = "Opposite side hedge"
                    else:
                        reason = "Complementary range"

                    hedges.append((opp, allocation, reason))

        # Calculate return range
        min_ret = -budget  # Worst case: everything loses
        max_ret = primary_allocation * (1.0 / primary.market_yes_price - 1.0) if primary.recommended_side == "YES" else primary_allocation * (1.0 / primary.market_no_price - 1.0)

        for opp, allocation, _ in hedges:
            price = opp.market_yes_price if opp.recommended_side == "YES" else opp.market_no_price
            max_ret += allocation * (1.0 / price - 1.0)

        # Calculate expected return
        expected_ret = primary.edge * primary_allocation
        for opp, allocation, _ in hedges:
            expected_ret += opp.edge * allocation

        # Determine risk level
        if group.sharpe_ratio > 2.0:
            risk_level = "Low"
        elif group.sharpe_ratio > 1.0:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # Generate description
        description = (
            f"Hedge portfolio for {group.location} {group.metric} on {group.date.strftime('%b %d')}.\n"
            f"Primary position: {primary.ticker} {primary.recommended_side} at {primary.market_yes_price:.1%} "
            f"(true prob: {primary.true_probability:.1%}).\n"
        )

        if hedges:
            description += f"\nRecommended hedges:\n"
            for opp, allocation, reason in hedges:
                price = opp.market_yes_price if opp.recommended_side == "YES" else opp.market_no_price
                description += f"  - ${allocation:.2f} on {opp.ticker} {opp.recommended_side} at {price:.1%} ({reason})\n"

        return HedgingStrategy(
            primary=primary,
            hedges=hedges,
            total_investment=budget,
            expected_return_range=(min_ret, max_ret),
            risk_level=risk_level,
            confidence=group.primary_bet.confidence,
            description=description
        )
