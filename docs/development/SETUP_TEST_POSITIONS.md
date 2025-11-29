# Test Position Setup Guide

## Current Account Status

- **Account Value:** ~$416
- **Max at 10x:** ~$4,160 in positions
- **Max at 2x:** ~$832 in positions

## Test Plan

**Goal:** Test leverage change from 10x → 2x with rebalancing

**Strategy:**
- Start with ~$600 total at 10x (70% BTC, 30% SOL) - unbalanced
- Rebalance to ~$600 at 2x (50% BTC, 50% SOL) - balanced
- This fits comfortably within the $832 limit at 2x ✓

## Position Sizes to Open

### BTC Position
- **USD Value:** $420 (70% of $600)
- **Size:** 0.00375 BTC (at ~$112,000/BTC)
- **Leverage:** 10x (Cross margin)
- **Margin needed:** $42

### SOL Position
- **USD Value:** $180 (30% of $600)
- **Size:** 0.96 SOL (at ~$188/SOL)
- **Leverage:** 10x (Cross margin)
- **Margin needed:** $18

**Total margin needed:** ~$60 (plenty available from $416!)

---

## Setup Instructions

### Go to Hyperliquid Testnet

**URL:** https://app.hyperliquid-testnet.xyz

### Step 1: Open BTC Position

1. Click on **BTC** trading pair
2. Set **Leverage:** 10x
3. Select **Cross** margin mode
4. **Side:** LONG (Buy)
5. **Amount:** 0.00375 BTC (or ~$420 USD value)
6. Click **Market Order**
7. Confirm and execute

### Step 2: Open SOL Position

1. Click on **SOL** trading pair
2. Set **Leverage:** 10x
3. Select **Cross** margin mode
4. **Side:** LONG (Buy)
5. **Amount:** 0.96 SOL (or ~$180 USD value)
6. Click **Market Order**
7. Confirm and execute

---

## Verification

### Check Positions

```bash
curl http://localhost:8000/api/positions/ | python3 -m json.tool
```

### Expected Output

```json
[
  {
    "position": {
      "coin": "BTC",
      "position_value": 420.00,  // ~70%
      "leverage_value": 10
    }
  },
  {
    "position": {
      "coin": "SOL",
      "position_value": 180.00,  // ~30%
      "leverage_value": 10
    }
  }
]
```

**Total:** ~$600 at 10x leverage ✓

---

## Run Rebalance Test

Once positions are set up:

```bash
python3 scripts/test_leverage_rebalance.py
```

### What the Test Will Do

1. **Display current state:** 70% BTC, 30% SOL at 10x
2. **Calculate expected:** 50% BTC, 50% SOL at 2x
3. **Preview trades:**
   - CLOSE BTC (10x)
   - CLOSE SOL (10x)
   - Wait 2 seconds
   - Recalculate based on available margin
   - OPEN BTC at 2x (~$300)
   - OPEN SOL at 2x (~$300)

4. **Ask for confirmation** - type "yes" to execute
5. **Execute rebalance**
6. **Verify results:**
   - ✅ BTC: ~$300 (50%) at 2x
   - ✅ SOL: ~$300 (50%) at 2x
   - ✅ Total: ~$600 (preserved)
   - ✅ All within 1% of target

### Expected Final State

```
BTC: $300.00 (50.0%) at 2x leverage ✅
SOL: $300.00 (50.0%) at 2x leverage ✅
Portfolio Value: ~$600 ✅ (within 5% of original)
```

---

## Why This Test Works

### Margin Math

**Starting positions (10x):**
- $600 total / 10 = $60 margin needed ✓

**After rebalance (2x):**
- $600 total / 2 = $300 margin needed ✓
- Available: $416 margin
- Plenty of room! No scaling needed!

### What Gets Tested

1. ✅ **Leverage mismatch detection** - System detects 10x → 2x change
2. ✅ **Close/reopen logic** - Closes all positions before reopening
3. ✅ **Abort on failure** - Stops if any close fails
4. ✅ **Margin calculation** - Waits and refetches after closes
5. ✅ **Allocation accuracy** - Achieves 50/50 within 1%
6. ✅ **Leverage setting** - Sets 2x for new positions

---

## Troubleshooting

### If positions don't show up:
- Wait 10 seconds for API to update
- Refresh with: `curl http://localhost:8000/api/positions/`

### If leverage is wrong:
- Make sure you selected "Cross" margin mode
- Make sure you set 10x BEFORE placing the order

### If sizes are off:
- That's OK! The test will work with any sizes
- Just note the actual allocation percentages

### If test fails:
- Check `REBALANCING_TEST_RESULTS.md` for debugging info
- Look at server logs for detailed execution trace
- All fixes are already in place!

---

## Quick Reference

**Position Setup:**
- BTC: 0.00375 BTC (~$420) at 10x
- SOL: 0.96 SOL (~$180) at 10x

**Test Command:**
```bash
python3 scripts/test_leverage_rebalance.py
```

**Expected Result:**
- 50/50 allocation at 2x leverage ✅
- All within 1% tolerance ✅
