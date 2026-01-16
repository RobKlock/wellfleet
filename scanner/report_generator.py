"""
Report Generator
Formats opportunities into human-readable Markdown and CSV reports
"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import List

from .mispricing_detector import Opportunity


class ReportGenerator:
    """Generates formatted reports for identified opportunities"""

    def __init__(self):
        """Initialize report generator"""
        self.logger = logging.getLogger(__name__)

    def generate_daily_report(self, opportunities: List[Opportunity]) -> str:
        """
        Generate a Markdown-formatted daily report

        Args:
            opportunities: List of identified opportunities

        Returns:
            Markdown-formatted report string
        """
        report = []
        report.append("# Kalshi Weather Arbitrage Report")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("**Locations**: Denver, Miami")
        report.append("")

        if not opportunities:
            report.append("## No Opportunities Found")
            report.append("")
            report.append("All markets are efficiently priced or outside edge threshold.")
            return "\n".join(report)

        # Summary section
        report.append("## Summary")
        report.append(f"- **Opportunities Found**: {len(opportunities)}")

        total_edge = sum(opp.edge for opp in opportunities)
        total_bet = sum(opp.recommended_bet_size for opp in opportunities)
        avg_confidence = sum(opp.confidence for opp in opportunities) / len(opportunities)

        report.append(f"- **Total Edge**: {total_edge:.1%}")
        report.append(f"- **Recommended Total Bet**: ${total_bet:.2f}")
        report.append(f"- **Average Confidence**: {avg_confidence:.0%}")
        report.append("")

        # Opportunities sorted by edge (highest first)
        opportunities_sorted = sorted(opportunities, key=lambda x: x.edge, reverse=True)

        report.append("## Opportunities")
        report.append("")

        for i, opp in enumerate(opportunities_sorted, 1):
            report.append(f"### {i}. {opp.title}")
            report.append(f"**Ticker**: `{opp.ticker}`")
            report.append(f"**Location**: {opp.location}")
            report.append(f"**Date**: {opp.date.strftime('%B %d, %Y')}")
            report.append("")

            report.append("**Forecast Data (NWS)**:")
            report.append(f"- Min: {opp.forecast_min:.1f}°F")
            report.append(f"- Max: {opp.forecast_max:.1f}°F")
            report.append(f"- Avg: {opp.forecast_avg:.1f}°F")
            report.append("")

            report.append("**Market Data**:")
            report.append(f"- YES Price: {opp.market_yes_price:.0%} (bid)")
            report.append(f"- NO Price: {opp.market_no_price:.0%} (bid)")
            report.append(f"- Liquidity Pool: ${opp.liquidity_pool_size:.0f}")
            report.append(f"- Closes: {opp.close_time.strftime('%Y-%m-%d %H:%M %Z')}")
            report.append("")

            report.append("**Analysis**:")
            report.append(f"- True Probability: **{opp.true_probability:.0%}**")
            report.append(f"- Edge: **{opp.edge:+.1%}**")
            report.append(f"- Confidence: {opp.confidence:.0%}")
            report.append("")

            report.append("**Recommendation**:")
            report.append(f"- **Side**: {opp.recommended_side}")
            report.append(f"- **Bet Size**: ${opp.recommended_bet_size:.2f}")
            report.append("")

            report.append(f"**Reasoning**: {opp.reasoning}")
            report.append("")
            report.append("---")
            report.append("")

        return "\n".join(report)

    def generate_csv_export(self, opportunities: List[Opportunity]) -> str:
        """
        Generate CSV export of opportunities

        Args:
            opportunities: List of identified opportunities

        Returns:
            CSV-formatted string
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Ticker",
            "Title",
            "Location",
            "Date",
            "Recommended Side",
            "Bet Size",
            "Edge",
            "True Probability",
            "Market Price",
            "Confidence",
            "Forecast Min",
            "Forecast Max",
            "Forecast Avg",
            "Close Time"
        ])

        # Rows
        for opp in opportunities:
            market_price = opp.market_yes_price if opp.recommended_side == "YES" else opp.market_no_price

            writer.writerow([
                opp.ticker,
                opp.title,
                opp.location,
                opp.date.isoformat(),
                opp.recommended_side,
                f"${opp.recommended_bet_size:.2f}",
                f"{opp.edge:+.1%}",
                f"{opp.true_probability:.0%}",
                f"{market_price:.0%}",
                f"{opp.confidence:.0%}",
                f"{opp.forecast_min:.1f}°F",
                f"{opp.forecast_max:.1f}°F",
                f"{opp.forecast_avg:.1f}°F",
                opp.close_time.isoformat()
            ])

        return output.getvalue()

    def generate_summary(self, opportunities: List[Opportunity]) -> str:
        """
        Generate a brief text summary

        Args:
            opportunities: List of identified opportunities

        Returns:
            Summary string
        """
        if not opportunities:
            return "No opportunities found."

        total_edge = sum(opp.edge for opp in opportunities)
        total_bet = sum(opp.recommended_bet_size for opp in opportunities)

        summary_parts = [
            f"Found {len(opportunities)} opportunities",
            f"Total edge: {total_edge:.1%}",
            f"Recommended total bet: ${total_bet:.2f}"
        ]

        # Highlight best opportunity
        best_opp = max(opportunities, key=lambda x: x.edge)
        summary_parts.append(
            f"Best: {best_opp.ticker} ({best_opp.edge:+.1%} edge, {best_opp.recommended_side})"
        )

        return " | ".join(summary_parts)
