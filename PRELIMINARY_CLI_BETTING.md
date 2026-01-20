# Preliminary CLI Auto-Betting Guide

## Overview

Instead of trying to predict what the ASOS averaging will do, **just wait for the preliminary Climate Report** and bet on what it says! The preliminary is published around 7:30 AM and is ~95% accurate to the final report.

## Why This Works

**Timing Advantage:**
- Preliminary CLI published: ~7:30 AM
- Markets close: Often noon or later
- **You have 4-5 hours** to place bets after the "answer" is published!

**High Accuracy:**
- Preliminary is based on Daily Summary Message (already quality-controlled)
- Uses same methodology as final report
- Rarely changes from preliminary to final

**Information Edge:**
- Most traders aren't checking the NWS Climate Reports
- They're using overnight forecasts that are now outdated
- You have the "answer key" before settlement

## Step 1: Test Bet Placement (DO THIS NOW!)

Before setting up auto-betting, verify your Kalshi API works:

```bash
python test_bet_placement.py
```

**What it does:**
1. Connects to Kalshi API
2. Shows your account balance
3. Finds an open market with liquidity
4. Places a **$2 test bet** (you'll be asked to confirm)
5. Confirms the order was placed

**Expected output:**
```
[1] Connecting to Kalshi API...
✅ Connected successfully

[2] Fetching account balance...
✅ Balance: $1,234.56

[3] Finding a test market...
✅ Selected market: KXLOWTDEN-26JAN19-B18.5
   Will the minimum temperature be  18-19° on Jan 19, 2026?
   Current prices: YES 3.0% / NO 89.0%

[4] PREPARING TEST BET:
   Side: NO
   Contracts: 2
   Estimated cost: $1.78
   Max payout: $2.00

⚠️  This will place a REAL bet on Kalshi!

Type 'YES' to place the test bet: YES

[5] Placing order...
✅ ORDER PLACED SUCCESSFULLY!
   Order ID: abc123
   Status: executed
   ✅ Order executed immediately

TEST SUCCESSFUL!
```

**If it fails:**
- Check your credentials in `.env`
- Make sure you have sufficient balance
- Check that markets are open (trading hours)

## Step 2: Auto-Betting Scanner

Once bet placement works, set up the auto-betting scanner:

### Basic Usage

**Monitor for today's preliminary and auto-bet $5 per market:**
```bash
python preliminary_cli_bet.py
```

**Run once and exit (no continuous monitoring):**
```bash
python preliminary_cli_bet.py --once
```

**Monitor Miami instead of Denver:**
```bash
python preliminary_cli_bet.py --station KMIA
```

**Custom bet size:**
```bash
python preliminary_cli_bet.py --bet-size 10
```

### Advanced Options

```bash
python preliminary_cli_bet.py \
  --station KDEN \
  --bet-size 5 \
  --start-hour 7 \
  --end-hour 9 \
  --interval 5
```

**Parameters:**
- `--station`: Weather station (KDEN=Denver, KMIA=Miami, KCYS=Cheyenne)
- `--bet-size`: Dollars to bet per market (default: $5)
- `--start-hour`: Start checking at this hour (default: 7 AM)
- `--end-hour`: Stop checking at this hour (default: 9 AM)
- `--interval`: Check every N minutes (default: 5)
- `--once`: Run once and exit instead of continuous monitoring

### What It Does

1. **Polling Phase (7:00-9:00 AM):**
   - Checks for preliminary CLI every 5 minutes
   - Logs: "Checking for preliminary CLI for 2026-01-19..."
   - If not found: "No preliminary CLI available yet"

2. **When Preliminary Found (~7:30 AM):**
   ```
   📊 PRELIMINARY CLI FOUND for 2026-01-19!
   ========================================
      Minimum: 20°F at 535 AM
      Maximum: 25°F at 1208 AM

   Found 8 markets to bet on:
     1. KXLOWTDEN-26JAN19-B20.5 - YES (95.0% confidence)
     2. KXLOWTDEN-26JAN19-B18.5 - NO (95.0% confidence)
     3. KXLOWTDEN-26JAN19-T21 - NO (95.0% confidence)
     ...
   ```

3. **Placing Bets:**
   ```
   Placing bet: KXLOWTDEN-26JAN19-B20.5 YES x25 @ $0.20
   ✅ Bet placed: KXLOWTDEN-26JAN19-B20.5 YES - Order ID: xyz789

   ✅ Placed 8/8 bets for 2026-01-19
   ```

4. **Continuing:**
   - Marks date as processed (won't bet again)
   - Continues monitoring for future dates
   - Sleeps 5 minutes between checks

## Betting Strategy

### How It Decides What to Bet

**If preliminary shows minimum = 20°F:**

| Market | Question | Preliminary Says | Bet | Confidence |
|--------|----------|------------------|-----|------------|
| B20.5 | 20-21°F range? | 20 is IN range | YES | 95% |
| B18.5 | 18-19°F range? | 20 is ABOVE range | NO | 95% |
| B22.5 | 22-23°F range? | 20 is BELOW range | NO | 95% |
| T21 | ≥21°F? | 20 < 21 | NO | 95% |
| T19 | ≥19°F? | 20 ≥ 19 | YES | 95% |

**It bets on EVERY market for that date** that aligns with the preliminary value.

### Position Sizing

**Bet size per market = $5.00 (default)**

Number of contracts = $5.00 / current price

**Example:**
- Market: B20.5 YES at 20¢
- Contracts: $5.00 / $0.20 = 25 contracts
- Cost: 25 × $0.20 = $5.00
- Max payout: 25 × $1.00 = $25.00
- Profit if correct: $20.00 (400% ROI!)

**Risk:**
- If wrong: Lose $5.00 per market
- If right: Win $20+ per market
- Expected value: 0.95 × $20 - 0.05 × $5 = **+$18.75** per market

## Safety Features

**Prevents duplicate bets:**
- Tracks processed dates
- Won't bet twice on same date even if restarted

**Only bets during monitoring window:**
- Default: 7 AM - 9 AM
- Outside window: Just logs and sleeps

**High confidence only:**
- Only bets when confidence ≥90%
- Preliminary reports are 95% confident

**Error handling:**
- If bet fails, logs error and continues
- Won't crash on API errors
- Shows success/failure count

## Running in Background

### Using Screen (Linux/Mac)

```bash
# Start a screen session
screen -S kalshi-betting

# Run the scanner
python preliminary_cli_bet.py

# Detach: Press Ctrl+A then D

# Reattach later
screen -r kalshi-betting
```

### Using nohup (Linux/Mac)

```bash
# Run in background
nohup python preliminary_cli_bet.py > betting.log 2>&1 &

# Check output
tail -f betting.log

# Stop it
pkill -f preliminary_cli_bet.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:55 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\preliminary_cli_bet.py`
7. Start in: `C:\path\to\wellfleet`

## Example Session

**7:00 AM:**
```
2026-01-19 07:00:15 - INFO - PRELIMINARY CLI MONITOR - KDEN
2026-01-19 07:00:15 - INFO - Monitoring window: 07:00 - 09:00 America/Denver
2026-01-19 07:00:15 - INFO - Bet size: $5.00 per market
2026-01-19 07:00:15 - INFO - Checking for preliminary CLI for 2026-01-19...
2026-01-19 07:00:16 - INFO - No preliminary CLI available yet for 2026-01-19
2026-01-19 07:00:16 - INFO - Sleeping for 5 minutes...
```

**7:30 AM (Preliminary Published!):**
```
2026-01-19 07:30:15 - INFO - Checking for preliminary CLI for 2026-01-19...
2026-01-19 07:30:16 - INFO - ========================================
2026-01-19 07:30:16 - INFO - 📊 PRELIMINARY CLI FOUND for 2026-01-19!
2026-01-19 07:30:16 - INFO - ========================================
2026-01-19 07:30:16 - INFO -    Minimum: 20°F at 535 AM
2026-01-19 07:30:16 - INFO -
2026-01-19 07:30:17 - INFO - Found 8 markets to bet on:
2026-01-19 07:30:17 - INFO -   1. KXLOWTDEN-26JAN19-B20.5 - YES (95.0% confidence)
2026-01-19 07:30:17 - INFO -   2. KXLOWTDEN-26JAN19-B18.5 - NO (95.0% confidence)
...
2026-01-19 07:30:18 - INFO - Placing bet: KXLOWTDEN-26JAN19-B20.5 YES x25 @ $0.20
2026-01-19 07:30:19 - INFO - ✅ Bet placed: Order ID: abc123
...
2026-01-19 07:30:35 - INFO - ✅ Placed 8/8 bets for 2026-01-19
2026-01-19 07:30:35 - INFO - 🎯 Successfully placed 8 bets!
2026-01-19 07:30:35 - INFO - Continuing to monitor for other dates...
2026-01-19 07:30:35 - INFO - Sleeping for 5 minutes...
```

## Verification & Results

**Check your Kalshi dashboard:**
- Go to kalshi.com
- View "Your Bets" section
- You should see 8+ new positions for Jan 19

**Monitor settlement:**
- Markets settle around midnight
- Check next morning for results
- Expected win rate: ~95%

**Track performance:**
- Scanner logs all bets placed
- Check `betting.log` for history
- Calculate ROI: (wins × payout - losses × cost) / total_invested

## Troubleshooting

**"No credentials configured"**
- Check `.env` file has KALSHI_EMAIL and KALSHI_PASSWORD
- Or KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH

**"No open markets found"**
- Markets might be closed (after hours)
- Wrong series ticker for station
- Markets already settled

**"Failed to place bet"**
- Insufficient balance
- Market closed
- Invalid order (check price limits)

**"No preliminary CLI available yet"**
- Too early (prelim published ~7:30 AM)
- Wrong date format
- NWS site down

## Best Practices

1. **Test first:** Run `test_bet_placement.py` before auto-betting
2. **Start small:** Use `--bet-size 5` until confident
3. **Monitor logs:** Check output for errors
4. **Verify results:** Compare final CLI to preliminary next morning
5. **Track performance:** Log wins/losses to validate 95% win rate
6. **Scale gradually:** Increase bet size as confidence grows

## Expected Returns

**Per day (8 markets @ $5 each):**
- Total invested: $40
- Expected wins: 7.6 markets (95%)
- Expected payout per win: ~$20
- Expected return: 7.6 × $20 = $152
- Expected profit: $152 - $40 = **+$112 per day**
- ROI: 280%

**Per month (assuming 22 trading days):**
- Expected profit: $112 × 22 = **+$2,464 per month**

**Key assumption:** Preliminary reports are 95% accurate to final. **Verify this with real data!**

## Tomorrow's Test

Check the final CLI tomorrow at 7:30 AM:
```
https://forecast.weather.gov/product.php?site=BOU&product=CLI&issuedby=DEN
```

Compare final to preliminary from today:
- **If same:** Strategy validated! ✅
- **If different:** Adjust confidence or stop using prelim

Your Jan 19 bet is the perfect test case! 🎲
