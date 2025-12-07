# Hyperbot Scripts

This directory contains various test and utility scripts for the Hyperbot trading bot.

## 🚀 Quick Start

### Run All API Integration Tests
```bash
bash scripts/run_all_api_tests.sh
```

This runs all 6 API integration tests and shows a summary. All tests connect to **Hyperliquid Testnet**.

---

## 📋 API Integration Tests

These test scripts verify the bot's integration with Hyperliquid testnet using real API calls. They test the **Use Case Layer** - the same code paths used by the Telegram bot.

### Core Tests

| Script | Purpose | What It Tests |
|--------|---------|---------------|
| `test_hyperliquid.py` | Basic connectivity | Info/Exchange API clients, health check |
| `test_market_data.py` | Market data service | Prices, metadata, order book |
| `test_order_operations.py` | Order placement | Market buy/sell, position close |
| `test_error_handling.py` | Error handling | API failures, invalid inputs |

### Use Case Tests

| Script | Purpose | What It Tests |
|--------|---------|---------------|
| `test_portfolio_use_cases.py` | Portfolio operations | Position summary, risk analysis, rebalance preview |
| `test_scale_order_use_cases.py` | Scale orders | Preview, place, list, status, cancel |

### Running Individual Tests

```bash
# Test a specific feature
uv run python scripts/test_portfolio_use_cases.py
uv run python scripts/test_scale_order_use_cases.py
uv run python scripts/test_order_operations.py
```

---

## 🛠️ Utility Scripts

### Debugging & Inspection

| Script | Purpose |
|--------|---------|
| `check_api_data.py` | Check API response structures |
| `debug_account_balance.py` | Debug account balance issues |
| `debug_position_structure.py` | Inspect position data structure |
| `discover_api_methods.py` | List available API methods |
| `inspect_exchange_methods.py` | Inspect Exchange API methods |

### Manual Testing

| Script | Purpose |
|--------|---------|
| `manual_test_rebalancing.py` | Manual rebalance testing |
| `open_test_positions.py` | Open test positions on testnet |
| `setup_test_positions.py` | Setup initial test positions |

### Code Quality

| Script | Purpose |
|--------|---------|
| `lint.sh` | Run ruff linter |
| `lint-fix.sh` | Run ruff with auto-fix |
| `check-dead-code.sh` | Check for unused code with vulture |

---

## ⚠️ Important Notes

### Testnet vs Mainnet

**All scripts use TESTNET by default** (configured in `.env`):
- Testnet URL: `https://api.hyperliquid-testnet.xyz`
- Testnet faucet: Get free test USDC

### Safety Checks

1. **Always verify environment**: Check `.env` has `HYPERLIQUID_TESTNET=true`
2. **Never run on mainnet without review**: Scripts place real orders
3. **Check logs**: All tests log to console with detailed output

### Test Order Sizes

Scripts use small order sizes for testing:
- Market orders: ~$20 USD
- Positions: Minimal size (0.0002 BTC)
- Scale orders: 5 orders @ $10 each

---

## 📊 Expected Results

All API integration tests should **PASS** on testnet:

```
==========================================
SUMMARY
==========================================
✅ PASS: test_hyperliquid.py
✅ PASS: test_market_data.py
✅ PASS: test_order_operations.py
✅ PASS: test_error_handling.py
✅ PASS: test_portfolio_use_cases.py
✅ PASS: test_scale_order_use_cases.py

Results: 6/6 tests passed
🎉 ALL TESTS PASSED!
```

---

## 🧪 Unit Tests

For mocked unit tests (no API calls), see `tests/` directory and run:

```bash
uv run pytest tests/ -v
```

**Current unit test status**:
- ✅ 595 passing
- ❌ 16 failing (trading use cases - async mock issues)
- 📊 67% coverage

---

## 🔍 Troubleshooting

### Tests Failing?

1. **Check Hyperliquid testnet status**: API might be down
2. **Verify credentials**: `.env` must have wallet address and private key
3. **Check testnet balance**: Need USDC for orders
4. **Review logs**: Tests log detailed output showing exact failures

### Common Issues

| Issue | Solution |
|-------|----------|
| `HyperliquidService not initialized` | Check `.env` credentials |
| `Insufficient balance` | Get testnet USDC from faucet |
| `API timeout` | Testnet may be slow, retry |
| `Invalid order size` | Check asset metadata for minimums |

---

## 📚 Documentation

For more details, see:
- **Roadmap**: `docs/PLAN.md`
- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Development Guide**: `CLAUDE.md`
- **Hyperliquid API**: `docs/hyperliquid/api-reference.md`

---

**Last Updated**: 2025-11-07
**Status**: ✅ All API integration tests passing
