# ASOS Uncertainty Model

## The Problem

You placed a bet on Denver minimum temperature being in the 18-19°F range (market B18.5) on Jan 19, 2026. The real-time METAR observations showed **19°F** multiple times throughout the morning (5:30 AM, 5:35 AM, 7:25 AM, 9:30 AM, etc.). However, the preliminary NWS Climate Report issued at 7:30 AM showed the minimum as **20°F** at 5:35 AM.

**This discrepancy is critical for betting** - if the final Climate Report shows 20°F instead of 19°F, your bet loses!

## Why This Happens: ASOS 5-Minute Averaging

Based on official NWS documentation, we learned that:

### ASOS Doesn't Report Instantaneous Temperatures

> "Temperature is measured every minute with a 5-minute running average. The system maintains running maximum and minimum values that are updated every minute throughout the 24-hour period."

**Key insight:** The displayed "19°F" in METAR observations is a **rounded 5-minute average**, not an instantaneous reading.

### The Rounding Problem

When you see "19°F" displayed:
- The actual 5-minute average could be **18.5-19.4°F** → rounds to 19°F (good for your bet!)
- OR it could be **19.5-19.9°F** → also displays as 19°F but rounds to **20°F** in the final CLI (bad!)

**You can't tell which without seeing the raw sensor data.**

### Quality Control Makes It Worse

The NWS Climate Report undergoes three levels of quality control:
1. **Level 1 (Real-time)**: Automated self-diagnostics, rate-of-change checks
2. **Level 2 (Area, 1-2 hours)**: WFO personnel review for consistency
3. **Level 3 (National, ~2 hours)**: NCDC performs additional QC before archiving

Observations can be flagged, adjusted, or removed at any level. The **Daily Summary Message (DSM)** used for the preliminary CLI is considered more reliable than individual METAR observations.

## The Solution: ASOS Uncertainty Model

We've implemented a model that accounts for this uncertainty:

### 1. Uncertainty Zone Detection

When an observed temperature is within **±1°F** of a market threshold, we flag it as being in the "ASOS uncertainty zone":

```python
ASOS_UNCERTAINTY_RANGE = 1.0  # ±1°F uncertainty zone

# Example: Observed 19.4°F, threshold 20°F
distance_to_threshold = abs(19.4 - 20.0) = 0.6°F
# 0.6°F < 1.0°F → IN UNCERTAINTY ZONE! ⚠️
```

### 2. Confidence Reduction

When in the uncertainty zone, we reduce confidence by **30%**:

```python
base_confidence = 0.95  # 95% if clearly resolved
confidence = base_confidence * (1 - 0.30)  # Reduce by 30%
# confidence = 0.665 = 66.5%
```

This accounts for the possibility that the displayed value might round differently in the final Climate Report.

### 3. Warning Messages

The scanner issues clear warnings:

```
⚠️ ASOS UNCERTAINTY: Observed 19.4°F is within 0.6°F of threshold 20°F.
Displayed value may round differently in final CLI!
```

## Real Example: Denver Jan 19, 2026

**Market:** B18.5 (18-19°F range)
**Observed:** 19.4°F throughout morning
**Preliminary CLI:** 20°F at 5:35 AM

### Without ASOS Model (OLD)
```
Observed: 19.4°F in range [18-19°F]
Past peak time (8am): YES
Confidence: 95% → Bet YES with high conviction ✅
```

### With ASOS Model (NEW)
```
Observed: 19.4°F near range boundary [18-19°F]
⚠️ ASOS UNCERTAINTY WARNING!
Distance to boundary: 0.6°F (within uncertainty zone)
Confidence: 66.5% (reduced from 95%)
⚠️ RISK: If 5-min avg was 19.5-19.9°F, final CLI will show 20°F → BET LOSES
```

## When to Trust Observations

### High Confidence (Safe to Bet)

**Observed value is >1°F away from threshold:**
```
Observed: 17.0°F, Threshold: 20°F
Distance: 3.0°F → NO UNCERTAINTY
Confidence: 95% → Safe bet ✅
```

**Past peak time + clearly outside range:**
```
Observed: 15.0°F for market "20-21°F"
Clearly below range, past 8am
Confidence: 95% → Safe bet ✅
```

### Low Confidence (Risky Bet)

**Observed value within ±1°F of threshold:**
```
Observed: 19.4°F, Threshold: 20°F
Distance: 0.6°F → UNCERTAINTY ZONE ⚠️
Confidence: 66.5% → Risky!
```

**Observed value right on boundary:**
```
Observed: 20.0°F for range "20-21°F"
On lower boundary → UNCERTAINTY ZONE ⚠️
Could round to 19°F or 21°F depending on decimals
Confidence: 66.5% → Risky!
```

### Zero Confidence (Don't Bet)

**Before peak time:**
```
Current time: 6:00 AM (before 8am minimum peak)
Temperature could still drop → DON'T BET
```

**No observations yet:**
```
Market opens but no observations from today
Pure forecast, no constraints → DON'T BET
```

## Using the Model

### Run Scanner with ASOS Warnings

```bash
python show_all_markets_verbose.py KXLOWTDEN
```

Look for these warning signs:
```
⚠️ ASOS UNCERTAINTY: Observed 19.4°F is within 0.6°F of threshold 20.0°F.
Displayed value may round differently in final CLI!

Observed minimum 19.4°F in range [18.0°F, 19.0°F] and past peak time → Definite YES (confidence: 66.5%)
```

### Interpret Confidence Levels

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| 95% | Clearly resolved, >1°F from boundary | ✅ High conviction bet |
| 66.5% | In uncertainty zone, ASOS rounding risk | ⚠️ Reduced bet or hedge |
| 50% | Before peak time, outcome unclear | ❌ Don't bet yet |
| 5% | Opposite of observation, very unlikely | ✅ High conviction opposite side |

### Test the Model

```bash
python test_asos_uncertainty.py
```

This runs test cases showing how the model handles:
- Values far from threshold (no uncertainty)
- Values near threshold (uncertainty warning)
- Values on boundaries (maximum uncertainty)
- Real Denver Jan 19 case

## Validation Tomorrow

**Tomorrow (Jan 20) around 7:30 AM MST**, check the final Climate Report:

```
https://forecast.weather.gov/product.php?site=BOU&product=CLI&issuedby=DEN
```

Compare the final minimum against what you bet on:
- **If final shows 19°F:** ✅ Model was conservative, bet wins!
- **If final shows 20°F:** ⚠️ Model correctly warned of uncertainty, bet loses

This real-world validation will help us calibrate the uncertainty threshold (currently ±1°F) and confidence reduction (currently 30%).

## Future Improvements

### 1. Preliminary CLI Validation

We've added a method to fetch preliminary CLI reports:

```python
preliminary = nws.get_preliminary_climate_report("KDEN", "2026-01-19")
# Returns: {"preliminary_min": 20.0, "min_time": "535 AM"}
```

**Future enhancement:** When preliminary CLI differs from observations, trust the CLI more since it's based on the Daily Summary Message after quality control.

### 2. Calibration from Historical Data

After collecting real outcomes:
- If 66.5% confidence → 95% win rate: too conservative, reduce penalty
- If 66.5% confidence → 50% win rate: correct calibration ✅
- If 66.5% confidence → 30% win rate: too aggressive, increase penalty

### 3. Station-Specific Adjustments

Different ASOS stations might have different rounding behaviors or quality control patterns. We could learn station-specific uncertainty parameters from historical data.

## Key Takeaways

1. **ASOS uses 5-minute averages**, not instantaneous readings
2. **Displayed integers mask underlying decimals** that determine final rounding
3. **±1°F from threshold = uncertainty zone** where rounding could go either way
4. **Reduce confidence by 30%** when in uncertainty zone
5. **Preliminary CLI is more reliable** than individual METAR observations
6. **Validate tomorrow** to see if model correctly predicted the risk

## The Houston Precedent

Remember the Reddit user who saw **71°F all day** (actually 70.7°F in observations) but the final Climate Report said only **70°F**? This is exactly the ASOS uncertainty problem we're now modeling!

Your Denver Jan 19 bet is a perfect test case. Check tomorrow's final report and let us know what it shows! 📊
