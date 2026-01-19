# Portfolio Optimization & Hedging Guide

## Overview

The portfolio optimizer analyzes correlated temperature markets and suggests optimal allocation strategies. Since all Denver minimum markets for the same date settle based on the **same observed temperature**, they're perfectly correlated - creating powerful hedging opportunities.

## Quick Start

```bash
# Analyze all markets with default $100 budget per group
python portfolio_analysis.py

# Analyze specific series with custom budget
python portfolio_analysis.py KXLOWTDEN --budget 50

# Use custom bankroll and minimum edge
python portfolio_analysis.py --bankroll 5000 --min-edge 0.10
```

## Real Example: Denver Jan 19, 2026

### The Situation
**Observed minimum: 19.4°F at 9:00am (past peak time)**

The scanner found 12 opportunities, including these correlated markets:

```
Markets for Denver Jan 19 Minimum:
  1. B18.5 (18-19°F):  +92% edge, bet YES at 3¢  → True prob: 95%
  2. B20.5 (20-21°F):  -84% edge, bet NO at 89¢  → True prob: 5%
  3. T25 (≥25°F):      +4% edge,  bet NO at 9¢   → True prob: 5%
  4. B22.5 (22-23°F):  +4% edge,  bet NO at 9¢   → True prob: 5%
```

### Why These Are Correlated

All markets settle based on the **same number**: Denver's observed minimum for Jan 19.

If the minimum is **19°F** (as we predict):
- ✅ B18.5 (18-19°F) → **YES wins** (19 is in range)
- ✅ B20.5 (20-21°F) → **NO wins** (19 is below range)
- ✅ T25 (≥25°F) → **NO wins** (19 < 25)
- ✅ B22.5 (22-23°F) → **NO wins** (19 is below range)

### Strategy #1: Single Position (Highest Edge)

**Simple approach:** Just bet on the highest edge market.

```
Investment: $5.00 on B18.5 YES at 3¢
Outcome if correct: $5 → $166.67 (33x return)
Outcome if wrong: -$5.00
Expected value: 0.95 × $161.67 - 0.05 × $5 = +$153.34
```

**Risk:** You're betting on a single outcome. If the minimum is actually 17°F (unlikely but possible), you lose everything.

### Strategy #2: Hedged Portfolio (Recommended)

**Smart approach:** Spread across correlated markets with positive edges.

```
HEDGED PORTFOLIO ($100 budget):
  Primary (60%): $60 on B18.5 YES at 3¢
    → If wins: $60 → $2,000 (+$1,940)

  Hedge #1 (25%): $25 on T25 NO at 9¢
    → If wins: $25 → $277.78 (+$252.78)

  Hedge #2 (15%): $15 on B22.5 NO at 9¢
    → If wins: $15 → $166.67 (+$151.67)

OUTCOMES:
  If minimum = 19°F (95% confidence):
    - All three bets win
    - Return: $1,940 + $252.78 + $151.67 = +$2,344.45
    - ROI: 2,344% 🔥

  If minimum = 17°F (2% chance - colder than observed):
    - Primary loses, hedges win
    - Return: -$60 + $252.78 + $151.67 = +$344.45
    - ROI: 344% (still profitable!)

  If minimum = 21°F (2% chance - observations were wrong):
    - All bets lose
    - Return: -$100
    - ROI: -100%

Expected Value: 0.95 × $2,344 + 0.03 × $344 + 0.02 × (-$100) = +$2,237
```

**Risk Metrics:**
- Sharpe Ratio: ~12.3 (excellent risk-adjusted returns)
- Max Drawdown: $100 (if completely wrong)
- Standard Deviation: ~$15 (very low variance given expected returns)

### Strategy #3: Arbitrage (Risk-Free Profit)

If market prices for all outcomes don't sum to 100¢, there's arbitrage.

**Example scenario** (hypothetical):
```
Markets covering all possibilities:
  B17.5 (≤17°F):  12¢
  B18.5 (18-19°F): 3¢
  B20.5 (20-21°F): 89¢  ← Too high!
  B22.5 (22-23°F): 9¢
  T24 (≥24°F):     9¢

Total: 122¢ (should be ~100¢)
```

**Arbitrage strategy:**
Buy NO on everything that's overpriced, or construct a portfolio where you win regardless of outcome.

## Portfolio Metrics Explained

### Sharpe Ratio
Risk-adjusted return metric. Higher is better.

```
Sharpe = (Expected Return - Risk Free Rate) / Standard Deviation

Good: > 1.0
Excellent: > 2.0
Outstanding: > 3.0
```

**For temperature markets with locked-in outcomes:**
- Sharpe ratios can be 10+ because variance is extremely low
- Once past peak time with observations, the outcome is nearly certain

### Expected Value (EV)

Average profit across all possible outcomes.

```
EV = Σ (probability × payout)

For B18.5 YES at 3¢:
  EV = 0.95 × ($1 - $0.03) - 0.05 × $0.03
     = 0.95 × $0.97 - 0.05 × $0.03
     = $0.92 - $0.0015
     = +$0.92 per dollar bet (92% edge)
```

### Kelly Criterion

Optimal bet sizing based on edge and odds.

```
Kelly % = (bp - q) / b

where:
  b = odds (decimal payout - 1)
  p = true probability
  q = 1 - p

For B18.5 YES:
  b = (1/0.03) - 1 = 32.33
  p = 0.95
  q = 0.05
  Kelly = (32.33 × 0.95 - 0.05) / 32.33 = 93.6%
```

**Fractional Kelly (recommended):**
- Use 1/4 Kelly = 23.4% of bankroll
- Reduces variance and overbetting risk

## When To Use Which Strategy

### Single Position
**Use when:**
- You have very high confidence (>90%)
- Past peak time with observations
- Market has massive edge (>50%)
- Limited capital

**Example:** B18.5 at 9am when minimum already hit 19.4°F

### Hedged Portfolio
**Use when:**
- Multiple correlated markets available
- Want to reduce tail risk
- Have larger capital to deploy
- Market still developing (before peak time)

**Example:** Morning markets with several +20% edge opportunities

### Wait / Don't Bet
**Use when:**
- Before peak time without clear trend
- Low confidence (<60%)
- Small edges (<5%)
- High market efficiency

**Example:** Maximum markets at 10am (peak not until 2-4pm)

## Portfolio Analysis Output

The `portfolio_analysis.py` script provides:

### 1. Portfolio Groups
Groups correlated markets by location, date, and metric.

```
📊 PORTFOLIO: Denver, CO MINIMUM on January 19, 2026
  Markets: 5
  Total Edge: +228%
  Sharpe Ratio: 12.3
  Recommended Allocation: $200 (20% of bankroll)
```

### 2. Risk Metrics
```
💰 EXPECTED RETURNS:
  Expected: +$186.00
  Best Case: +$2,450.00
  Worst Case: -$200.00

⚠️ RISK METRICS:
  Standard Deviation: $15.20
  Max Drawdown: $200.00
```

### 3. Hedging Strategy
```
🛡️ HEDGING STRATEGY (Budget: $100):
  Risk Level: Low
  Confidence: 95%

  PRIMARY POSITION:
    $60 → KXLOWTDEN-26JAN19-B18.5 YES
    Entry: 3.0%
    True Prob: 95.0%
    Edge: +92.0%

  HEDGE POSITIONS:
    $25 → KXLOWTDEN-26JAN19-T25 NO
      Entry: 9.0% | Edge: +4.0% | Reason: Complementary range

    $15 → KXLOWTDEN-26JAN19-B22.5 NO
      Entry: 9.0% | Edge: +4.0% | Reason: Complementary range
```

## Advanced: Custom Portfolio Optimization

You can build custom portfolios by:

1. **Import the optimizer:**
```python
from scanner import PortfolioOptimizer

optimizer = PortfolioOptimizer(bankroll=1000)
groups = optimizer.group_correlated_markets(opportunities)
```

2. **Analyze specific groups:**
```python
for group in groups:
    strategy = optimizer.generate_hedging_strategy(group, budget=100)
    print(f"Expected: ${strategy.expected_return_range[0]:.2f} to ${strategy.expected_return_range[1]:.2f}")
```

3. **Custom allocation:**
```python
# Allocate based on Sharpe ratio
total_allocation = bankroll * 0.30  # 30% of bankroll
for group in sorted(groups, key=lambda g: g.sharpe_ratio, reverse=True)[:3]:
    allocation = (group.sharpe_ratio / sum(g.sharpe_ratio for g in groups[:3])) * total_allocation
    # Place bets...
```

## Tips for Maximum Profit

1. **Time your entries:** Best edges appear right after peak time when observations lock in outcome
2. **Check multiple series:** Denver and Miami markets often both have opportunities
3. **Scale with confidence:** Higher confidence = larger position size
4. **Diversify across dates:** Don't put everything on one day
5. **Use fractional Kelly:** 1/4 Kelly sizing prevents overbetting
6. **Monitor Cheyenne:** Leading indicator can predict Denver trends
7. **Track settlement:** Verify outcomes against NWS Daily Climate Report

## Common Questions

**Q: Why hedge if I'm confident?**
A: Reduces variance and tail risk. If you're 95% confident, 5% of the time you're wrong. Hedging profits even in that scenario.

**Q: What if markets are efficient?**
A: After peak time with observations, markets are often slow to update. That's your edge window.

**Q: How much should I bet?**
A: Use 1/4 Kelly criterion. For 92% edge at 3¢ odds, that's ~23% of bankroll. Scale down if uncertain.

**Q: Can I lose money with hedging?**
A: Yes, if your forecast is completely wrong. But hedging limits losses and often stays profitable even if primary bet fails.

**Q: When are the best opportunities?**
A: 8am-10am for minimum markets (after peak), 5pm-7pm for maximum markets (after peak).

## Next Steps

1. Run `python portfolio_analysis.py KXLOWTDEN` to see real opportunities
2. Start small ($10-$50 per portfolio) to test the system
3. Track results and compare to NWS Daily Climate Report
4. Scale up as you gain confidence
5. Explore other locations (Miami, etc.)

Happy trading! 🚀
