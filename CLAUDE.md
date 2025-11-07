# Hyperbot Development Guide for Claude

This document provides comprehensive guidance for developing and maintaining the Hyperbot trading bot. Always reference the local documentation files when working on features.

## 📋 Implementation Plan & Progress

**IMPORTANT**: Before working on any feature, always check:
- **Strategy & Architecture**: [docs/PLAN.md](docs/PLAN.md) - EPIC-level goals, decisions, ADRs (PM view)
- **Tasks & Progress**: [docs/TODO.md](docs/TODO.md) - Detailed checklists, status, issues (Developer view)

**Current Status** (see TODO.md for details):
- **Current Phase**: ✅ Phase 4 Complete - Code Consolidation & Use Case Layer
- **Next Decision**: Choose between Phase 1B.2 (Dashboard), Phase 2C (Spot Trading), Phase 3 (Telegram Bot), or Phase 1A.7 (Testing)

## Project Overview

Hyperbot is a Python-based trading bot that integrates:
- **Hyperliquid**: Decentralized exchange for crypto trading
- **Web Dashboard**: Primary UI for monitoring and trading (Phase 1B)
- **Telegram**: Mobile interface for alerts and quick actions (Phase 3)
- **TradingView**: Webhook-based trading signals

## Documentation Structure

All documentation is stored locally in the `/docs` directory:

```
docs/
├── PLAN.md                    # ⭐ EPIC-level: Architecture, decisions, strategy (PM view)
├── TODO.md                    # ⭐ Task-level: Checklists, progress, issues (Developer view)
├── hyperliquid/
│   ├── python-sdk.md          # Official SDK documentation
│   └── api-reference.md       # Complete API reference with examples
└── telegram/
    ├── bot-api-reference.md   # Complete Telegram Bot API reference
    ├── best-practices.md      # Security, performance, patterns
    ├── features.md            # All Telegram bot features
    └── faq.md                 # Comprehensive FAQ and troubleshooting
```

### PLAN.md vs TODO.md - Clear Separation

> **Important**: These files have **zero duplication** - each piece of information lives in exactly one place.

#### PLAN.md (PM/EPIC View)
**When to read**: Understanding project strategy, architecture, or design decisions

**Contains**:
- ✅ Architecture diagrams
- ✅ Phase goals and deliverables
- ✅ Tech stack decisions with rationale (FastAPI, HTMX, Tailwind)
- ✅ Decision Log (ADRs - why we chose X over Y)
- ✅ Testing strategy (high-level philosophy)

**Does NOT contain**:
- ❌ Task checklists with file paths
- ❌ Implementation code snippets
- ❌ Current progress tracking (see TODO.md)
- ❌ Granular subtasks

**Use this when**:
- Starting a new phase (understand the goal and architecture)
- Making architectural decisions (check existing ADRs)
- Explaining project structure to others
- You need to understand "why" something was done

---

#### TODO.md (Developer/Task View)
**When to read**: Implementing features, tracking progress, debugging issues

**Contains**:
- ✅ Detailed task checklists with file paths (e.g., `src/use_cases/trading/place_order.py`)
- ✅ Progress tracking (✅ Completed / 🔄 In Progress / 🚫 Blocked)
- ✅ Implementation code snippets and examples
- ✅ Testing lessons learned (mocking patterns, known issues)
- ✅ Known issues and workarounds
- ✅ Session summaries

**Does NOT contain**:
- ❌ Architecture diagrams (see PLAN.md)
- ❌ Tech stack rationale (see PLAN.md)
- ❌ High-level phase goals (see PLAN.md)

**Use this when**:
- Working on a specific task (find your next checkbox)
- Checking progress status
- Debugging (known issues section)
- Writing tests (testing lessons section)
- Completing a task (update checkboxes here only)

---

#### Quick Reference Table

| Information Type | PLAN.md | TODO.md |
|------------------|---------|---------|
| Architecture diagrams | ✅ | ❌ Reference PLAN.md |
| "Why" decisions (ADRs) | ✅ | ❌ Reference PLAN.md |
| Phase goals | ✅ | ❌ Reference PLAN.md |
| Task checkboxes | ❌ Reference TODO.md | ✅ |
| File paths & code | ❌ Reference TODO.md | ✅ |
| Progress status | ❌ Reference TODO.md | ✅ |
| Testing lessons | ❌ Reference TODO.md | ✅ |
| Known issues | ❌ Reference TODO.md | ✅ |

---

#### Workflow Examples

**Example 1: Starting Phase 3 (Telegram Bot)**
```
Step 1: Read PLAN.md → Phase 3 section
  - Understand goal: "Mobile interface for trading and alerts"
  - See tech stack decision: python-telegram-bot library
  - Review ADR: "Why Web Dashboard before Telegram Bot"

Step 2: Read TODO.md → Find Phase 3 tasks
  - [ ] Telegram bot setup
  - [ ] Create src/bot/handlers/
  - [ ] Implement /start command
  - ...

Step 3: Work from TODO.md, checking off tasks as you complete them
```

**Example 2: Understanding Rebalancing Logic**
```
Step 1: Read PLAN.md → Phase 2A section
  - Goal: "Portfolio rebalancing with integrated risk assessment"
  - Key decision: Use Case Layer architecture

Step 2: Read TODO.md → Phase 2A completed tasks
  - [x] Created src/services/rebalance_service.py
  - [x] Implemented preview_rebalance()
  - See testing lessons for risk calculation formulas
```

**Example 3: Completing a Task**
```
✅ DO: Update TODO.md
  - [x] Create src/use_cases/trading/place_order.py

❌ DON'T: Update PLAN.md
  - No duplicate tracking needed!
```

## When to Reference Documentation

### For Hyperliquid Tasks

**Always read**: `docs/hyperliquid/python-sdk.md` and `docs/hyperliquid/api-reference.md`

**Read before:**
- Implementing order placement
- Fetching account information
- Managing positions
- Implementing rebalancing
- Creating scale orders
- Handling market data
- Error handling for API calls

**Key sections to reference:**
- Authentication setup
- Order types (market, limit, stop loss, take profit)
- Position management methods
- Rate limiting
- Error handling patterns
- Testing on testnet

### For Telegram Bot Tasks

**Always read**: `docs/telegram/bot-api-reference.md`, `docs/telegram/best-practices.md`, `docs/telegram/features.md`, `docs/telegram/faq.md`

**Read before:**
- Creating new commands
- Implementing inline keyboards
- Handling user input
- Setting up conversations
- Sending notifications
- Error handling
- Authentication and security
- Performance optimization
- Troubleshooting bot issues

**Key sections to reference:**
- Handler types (Command, Message, Callback)
- Inline keyboard creation
- ConversationHandler for multi-step flows
- Security patterns (authentication decorator)
- Rate limiting (30 msg/sec to different chats, 20/min to same group)
- Error handling
- Logging best practices
- FAQ for common issues and solutions

## Development Workflow

### 1. Understanding Requirements

When given a task:

1. **Identify the components involved**:
   - Is this Hyperliquid-related? → Read Hyperliquid docs
   - Is this Telegram-related? → Read Telegram docs
   - Both? → Read both

2. **Check for existing patterns**:
   - Look in `docs/hyperliquid/api-reference.md` for "Common Patterns"
   - Look in `docs/telegram/best-practices.md` for similar implementations
   - Review existing code in `src/` for established patterns

3. **Plan the implementation**:
   - Break down into sub-tasks
   - Identify which services need modification
   - Consider error cases

### 2. Implementing Features

**Always:**
- Follow the project structure in `src/`
- Use type hints (Python 3.11+)
- Implement proper error handling (see best practices docs)
- Add logging with appropriate levels
- Write docstrings for functions

**For Hyperliquid Integration:**
```python
# Pattern from docs/hyperliquid/api-reference.md
from src.services.hyperliquid_service import hyperliquid_service

async def example_function():
    """Follow patterns from documentation."""
    try:
        # Always check initialization
        if not hyperliquid_service.is_initialized():
            await hyperliquid_service.initialize()

        # Use documented methods
        result = await hyperliquid_service.get_positions()

        # Handle response as documented
        return result

    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

**For Telegram Bot Features:**
```python
# Pattern from docs/telegram/bot-api-reference.md and best-practices.md
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.bot.middleware import authorized_only

@authorized_only
async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Follow security and UX patterns from documentation."""
    try:
        # Show progress
        msg = await update.message.reply_text("⏳ Processing...")

        # Do work
        result = await do_work()

        # Update with result
        await msg.edit_text(f"✅ Success: {result}")

    except Exception as e:
        logger.exception("Handler error")
        await update.message.reply_text(f"❌ Error: {str(e)}")
```

### 3. Testing

Before marking any feature as complete:

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test with real APIs (use testnet!)
3. **Manual Tests**: Test via Telegram bot interface

**Testing Checklist:**
- [ ] Hyperliquid operations tested on testnet
- [ ] Telegram commands tested with real bot
- [ ] Error cases handled gracefully
- [ ] User feedback is clear and informative
- [ ] Logging is appropriate
- [ ] No sensitive data exposed

## Common Scenarios

### Scenario 1: Adding a New Trading Command

**Steps:**
1. Read `docs/hyperliquid/api-reference.md` section on order placement
2. Read `docs/telegram/bot-api-reference.md` section on CommandHandler
3. Read `docs/telegram/best-practices.md` section on security
4. Implement in `src/bot/handlers/` with proper auth
5. Add to bot handler registration in `src/bot/main.py`
6. Test on testnet first

**Code Template:**
```python
# src/bot/handlers/trading.py
from src.bot.middleware import authorized_only
from src.services.hyperliquid_service import hyperliquid_service

@authorized_only
async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /buy <symbol> <size> command.
    Reference: docs/hyperliquid/api-reference.md - Market Orders
    """
    # Validate arguments
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /buy <symbol> <size>\n"
            "Example: /buy BTC 0.1"
        )
        return

    try:
        symbol = context.args[0].upper()
        size = float(context.args[1])

        # Show progress
        msg = await update.message.reply_text("⏳ Placing order...")

        # Place order (following docs pattern)
        result = await hyperliquid_service.place_market_order(
            coin=symbol,
            is_buy=True,
            size=size
        )

        # Provide clear feedback
        await msg.edit_text(
            f"✅ Buy order placed!\n\n"
            f"Symbol: {symbol}\n"
            f"Size: {size}\n"
            f"Status: {result['status']}"
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid size")
    except Exception as e:
        logger.exception("Buy order failed")
        await update.message.reply_text(f"❌ Order failed: {str(e)}")
```

### Scenario 2: Implementing Portfolio Rebalancing

**Steps:**
1. Read `docs/hyperliquid/api-reference.md` section on "Portfolio Rebalancing" pattern
2. Create data models in `src/models/rebalance_config.py`
3. Implement service in `src/services/rebalance_service.py`
4. Create Telegram handlers in `src/bot/handlers/rebalance.py`
5. Add inline keyboard for preset rebalance options
6. Implement confirmation flow

**Reference sections:**
- Hyperliquid: "Pattern 3: Portfolio Rebalancing"
- Telegram: "ConversationHandler" and "Inline Keyboards"
- Best Practices: "Confirmation Dialogs"

### Scenario 3: Adding Real-time Notifications

**Steps:**
1. Read `docs/telegram/features.md` section on "Notifications"
2. Read `docs/telegram/bot-api-reference.md` section on "Job Queue"
3. Implement monitoring service in `src/services/monitor_service.py`
4. Use Job Queue for periodic checks
5. Send notifications via `context.bot.send_message()`

**Code Template:**
```python
# src/services/monitor_service.py
async def monitor_positions():
    """
    Monitor positions and send alerts.
    Reference: docs/telegram/features.md - Notifications
    """
    while True:
        try:
            positions = await hyperliquid_service.get_positions()

            for pos in positions:
                if should_alert(pos):
                    await context.bot.send_message(
                        chat_id=settings.TELEGRAM_CHAT_ID,
                        text=format_alert(pos),
                        parse_mode="Markdown"
                    )

        except Exception as e:
            logger.error(f"Monitor error: {e}")

        await asyncio.sleep(60)  # Check every minute
```

### Scenario 4: Implementing Scale Orders

**Steps:**
1. Read `docs/hyperliquid/api-reference.md` for order placement methods
2. Create `ScaleOrderConfig` model with validation
3. Implement calculation logic in `src/services/scale_order_service.py`
4. Create conversation handler for multi-step input
5. Add preview with confirmation

**Reference sections:**
- Hyperliquid: "Limit Order" and "Order Management"
- Telegram: "ConversationHandler" pattern
- Best Practices: "Validate User Input" and "Confirmation Dialogs"

## API Usage Guidelines

### Hyperliquid

**Rate Limits:**
- Info API (read): 1200 requests/minute per IP
- Exchange API (write): 60 requests/minute per account
- WebSocket: 60 subscriptions per connection

**Key Endpoints:**
- Info API: `user_state()`, `open_orders()`, `user_fills()`, `all_mids()`, `l2_snapshot()`
- Exchange API: `market_open()`, `order()`, `cancel()`, `update_leverage()`, `market_close()`

**Always:**
- Initialize service before use
- Use testnet for development (`HYPERLIQUID_TESTNET=true` → `https://api.hyperliquid-testnet.xyz`)
- Handle rate limits (60 requests/minute for trading)
- Validate order sizes against minimums
- Check slippage on market orders (default 2-5%)
- Log all trading operations
- Use API wallet for enhanced security

**Never:**
- Place orders without confirmation on mainnet
- Ignore error responses
- Bypass size validation
- Skip health checks
- Expose private keys in logs or error messages

### Telegram

**Rate Limits:**
- 30 messages/second to different chats
- 20 messages/minute to same group
- 1 message/second to same private chat

**Message Limits:**
- Text: 4096 characters max
- Captions: 1024 characters max
- File size: 50 MB (photos, videos, documents)
- Inline keyboard: 100 buttons max, 64 bytes per callback_data

**Update Methods:**
- Long Polling (`getUpdates`): Good for development, easier setup
- Webhooks (`setWebhook`): Better for production, requires HTTPS

**Always:**
- Use `@authorized_only` decorator for sensitive commands
- Answer callback queries immediately (avoids "loading" state)
- Provide clear error messages
- Show progress for long operations
- Use markdown formatting for readability
- Log user actions
- Handle `Forbidden` error (user blocked bot)

**Never:**
- Expose API keys or private keys
- Send messages without rate limiting
- Forget to handle exceptions
- Ignore user feedback
- Use blocking operations (use `asyncio.sleep` not `time.sleep`)
- Skip answering callback queries

## Security Checklist

Before deploying or committing:

- [ ] No hardcoded credentials
- [ ] All sensitive data in environment variables
- [ ] Authentication required for all trading commands
- [ ] Input validation on all user inputs
- [ ] Confirmation required for destructive operations
- [ ] Rate limiting implemented
- [ ] Error messages don't expose sensitive info
- [ ] Logs don't contain secrets
- [ ] Testnet testing completed
- [ ] User authorization checked

## Code Quality Standards

**Follow these standards:**

1. **Type Hints**: Use for all function parameters and returns
2. **Docstrings**: Document all public functions
3. **Error Handling**: Try-except with specific exceptions
4. **Logging**: Use appropriate levels (debug, info, warning, error)
5. **Formatting**: Follow PEP 8, use Black formatter
6. **Testing**: Write tests for critical functions
7. **Comments**: Explain complex logic, reference docs when applicable

**Example:**
```python
from typing import Dict, List
from src.config import logger

async def get_user_positions(user_address: str) -> List[Dict[str, Any]]:
    """
    Retrieve all open positions for a user.

    Reference: docs/hyperliquid/api-reference.md - user_state method

    Args:
        user_address: Ethereum wallet address

    Returns:
        List of position dictionaries

    Raises:
        ConnectionError: If API is unreachable
        ValueError: If user_address is invalid

    Example:
        >>> positions = await get_user_positions("0x123...")
        >>> print(f"Found {len(positions)} positions")
    """
    try:
        logger.info(f"Fetching positions for {user_address}")

        if not hyperliquid_service.is_initialized():
            await hyperliquid_service.initialize()

        positions = await hyperliquid_service.get_positions()
        logger.debug(f"Retrieved {len(positions)} positions")

        return positions

    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise
```

## Dead Code Detection with Vulture

### When to Use Vulture

**🔍 Proactively run Vulture when:**

1. **After completing a major refactoring** - Check for orphaned code
2. **Before starting a new phase** - Clean up unused code from previous phases
3. **When codebase feels "bloated"** - Find code that accumulated over time
4. **After removing features** - Ensure related code was fully removed
5. **Periodically during development** - Weekly or bi-weekly scans

**Don't wait for pre-commit hooks** - Vulture in pre-commit is set to 80% confidence (conservative). Run manual scans with lower confidence to find more issues.

### Sensitivity Adjustment Strategy

**Start conservative, then increase sensitivity:**

#### 1️⃣ **First Scan: High Confidence (80-100%)**
```bash
vulture src/ .vulture_whitelist.py --min-confidence=80 --sort-by-size
```

**What to look for:**
- ✅ Definitely unused functions/classes
- ✅ Large unused files (high impact)
- ✅ Obvious dead code from old features

**Action:** Remove these immediately - they're very likely unused.

---

#### 2️⃣ **Second Scan: Medium Confidence (70-79%)**
```bash
vulture src/ .vulture_whitelist.py --min-confidence=70
```

**What to look for:**
- ⚠️ Functions that might be used indirectly
- ⚠️ Utility functions saved for future use
- ⚠️ Code used by external tools/scripts

**Action:**
- Investigate each finding
- Search codebase for usage: `grep -r "function_name" src/`
- Remove if genuinely unused
- Add to `.vulture_whitelist.py` if it's a false positive

---

#### 3️⃣ **Third Scan: Lower Confidence (60-69%)**
```bash
vulture src/ .vulture_whitelist.py --min-confidence=60
```

**What to look for:**
- 🔍 Many false positives (FastAPI routes, Pydantic fields)
- 🔍 Test fixtures and utilities
- 🔍 Some genuinely unused code hidden among false positives

**Action:**
- Review each finding carefully
- High chance of false positives - verify before removing
- Update `.vulture_whitelist.py` for legitimate false positives

---

### Workflow for Dead Code Removal

**Step-by-step process:**

```bash
# 1. Run high-confidence scan
./scripts/check-dead-code.sh

# 2. Review findings
#    - For each unused item, search for usage
grep -r "suspected_function" src/ tests/

# 3. Categorize findings
#    ✅ Definitely unused → Remove
#    ❓ Uncertain → Investigate further
#    ✗ False positive → Add to whitelist

# 4. Remove dead code
#    - Delete unused functions/classes
#    - Delete unused files
#    - Remove unused imports

# 5. Run tests to ensure nothing broke
uv run pytest tests/

# 6. If tests pass, commit
git add -A
git commit -m "Remove dead code found by Vulture scan"

# 7. Lower confidence and repeat
vulture src/ .vulture_whitelist.py --min-confidence=70
```

---

### Common False Positives to Whitelist

**Add these patterns to `.vulture_whitelist.py`:**

1. **FastAPI route handlers** (used via decorators)
   ```python
   _.get_account
   _.post_order
   ```

2. **Pydantic model fields** (used for serialization)
   ```python
   _.total_value
   _.wallet_address
   ```

3. **Pydantic validators** (called by framework)
   ```python
   _.validate_*
   ```

4. **pytest fixtures** (used by test framework)
   ```python
   _.mock_service
   _.sample_data
   ```

5. **Future-use utility functions** (planned features)
   ```python
   _.format_currency
   _.calculate_roi
   ```

6. **CLI entry points** (called from command line)
   ```python
   _.main
   _.run_bot
   ```

---

### Integration with Development Workflow

#### During Feature Development

```bash
# After completing a feature
./scripts/check-dead-code.sh

# Found unused imports from refactoring?
# Let ruff clean them up
ruff check --fix src/

# Found unused functions?
# Investigate and remove if genuinely unused
```

#### Before Commits

Pre-commit hooks run Vulture at **80% confidence**:
- High confidence = low false positive rate
- Won't block commits unnecessarily
- Catches obvious dead code

**If pre-commit finds issues:**
```bash
# Review the findings
vulture src/ .vulture_whitelist.py --min-confidence=80

# Either:
# A) Remove the dead code, OR
# B) Add to whitelist if false positive
```

#### Weekly Maintenance

```bash
# Every week, run a deeper scan
vulture src/ .vulture_whitelist.py --min-confidence=60 | tee vulture-scan.log

# Review log, categorize findings
# Clean up genuinely unused code
# Update whitelist for false positives
```

---

### Examples

#### Example 1: Found Unused Service Method

```bash
$ vulture src/ .vulture_whitelist.py --min-confidence=80
src/services/order_service.py:145: unused function 'calculate_slippage' (85% confidence)
```

**Investigation:**
```bash
# Search for usage
$ grep -r "calculate_slippage" src/ tests/
# No results!

# Check git history - was it ever used?
$ git log --all -S "calculate_slippage" --oneline
# Only added, never actually called
```

**Action:** Remove the function - it's genuinely unused.

---

#### Example 2: False Positive (FastAPI Route)

```bash
$ vulture src/ .vulture_whitelist.py --min-confidence=70
src/api/routes/positions.py:45: unused function 'get_position_details' (75% confidence)
```

**Investigation:**
```python
# Check the code
@router.get("/positions/{coin}")
async def get_position_details(coin: str):  # Used by FastAPI via decorator!
    ...
```

**Action:** Add to `.vulture_whitelist.py`:
```python
_.get_position_details  # FastAPI route handler
```

---

#### Example 3: Uncertain Finding

```bash
$ vulture src/ .vulture_whitelist.py --min-confidence=70
src/bot/utils.py:250: unused function 'format_price_alert' (72% confidence)
```

**Investigation:**
```bash
# Search for usage
$ grep -r "format_price_alert" src/
# Found in commented-out code in src/bot/handlers/alerts.py

# Check TODO.md
# Phase 5 mentions price alerts feature
```

**Action:** Keep it (planned feature) and add to whitelist:
```python
_.format_price_alert  # Reserved for Phase 5 - Price Alerts feature
```

---

### Tips for Claude (AI Assistant)

**When working on this codebase:**

1. **After major refactoring:** Run `./scripts/check-dead-code.sh` proactively
2. **Suggest dead code removal:** If you notice unused code, suggest running Vulture
3. **Adjust sensitivity:** Start at 80%, work down to 60% for thorough scans
4. **Explain findings:** Help user understand if finding is real or false positive
5. **Update whitelist:** When adding known false positives, document why
6. **Test after removal:** Always run tests after removing dead code

**Example proactive suggestion:**
```
"I noticed we just refactored the position service. Let me run Vulture
to check for any orphaned code from the old implementation..."

[Runs vulture scan]

"Found 3 unused functions from the old position calculation logic.
Should we remove them?"
```

---

### Quick Reference

| Confidence | Use Case | False Positive Rate |
|------------|----------|---------------------|
| 90-100% | Obvious dead code | Very low (~5%) |
| 80-89% | **Pre-commit default** | Low (~15%) |
| 70-79% | Regular scans | Medium (~30%) |
| 60-69% | Deep cleaning | High (~50%) |

**Commands:**
```bash
# Quick check (recommended for regular use)
./scripts/check-dead-code.sh

# Conservative (pre-commit level)
vulture src/ .vulture_whitelist.py --min-confidence=80

# Thorough
vulture src/ .vulture_whitelist.py --min-confidence=70

# Deep dive
vulture src/ .vulture_whitelist.py --min-confidence=60

# Find biggest issues first
vulture src/ .vulture_whitelist.py --sort-by-size --min-confidence=80
```

## Testing Best Practices

### Critical Testing Patterns (MUST READ)

**⚠️ IMPORTANT**: These patterns were learned through extensive debugging. Follow them to avoid common testing pitfalls.

#### 1. Service Singleton Mocking Pattern

**Problem**: Services are created at module import time as singletons. Simply patching the module won't work because the service instance already holds a reference to the real dependency.

**❌ WRONG - This will fail**:
```python
@pytest.fixture
def service(self, mock_hyperliquid_service):
    # Patching alone is not enough!
    with patch('src.services.position_service.hyperliquid_service', mock_hyperliquid_service):
        return PositionService()  # Still holds reference to real service
```

**✅ CORRECT - Explicit attribute assignment**:
```python
@pytest.fixture
def service(self, mock_hyperliquid_service, mock_account_service):
    """Create PositionService instance with mocked dependencies."""
    with patch('src.services.position_service.hyperliquid_service', mock_hyperliquid_service):
        with patch('src.services.position_service.account_service', mock_account_service):
            svc = PositionService()
            # CRITICAL: Explicitly assign mocked dependencies
            svc.hyperliquid = mock_hyperliquid_service
            svc.account = mock_account_service
            return svc
```

**Why it matters**: Without explicit assignment, you'll get "HyperliquidService not initialized" errors even with proper mocking.

#### 2. Mock Data Structure Must Match API Response Exactly

**Problem**: Hyperliquid API returns nested structures. Mock data must match this exactly.

**❌ WRONG - Flat structure**:
```python
mock_position_service.list_positions.return_value = [
    {
        "coin": "BTC",
        "size": 1.26,
        "leverage_value": 3
    }
]
```

**✅ CORRECT - Nested structure matching API**:
```python
mock_position_service.list_positions.return_value = [
    {
        "position": {
            "coin": "BTC",
            "size": 1.26,
            "leverage_value": 3,
            "leverage": {"value": 3, "type": "cross"},
            "position_value": 10000.0
        }
    }
]
```

**Why it matters**: Production code accesses `item["position"]["coin"]`, not `item["coin"]`. Mismatched structure causes KeyError.

#### 3. Mock Return Values Must Be Python Types, Not Mock Objects

**Problem**: When code iterates over return values, Mock objects cause `TypeError: 'Mock' object is not iterable`.

**❌ WRONG - Returns Mock object**:
```python
mock_info.spot_user_state.return_value = Mock()  # Will fail when iterated
```

**✅ CORRECT - Returns actual Python types**:
```python
mock_info.spot_user_state.return_value = {
    "balances": []  # Real list that can be iterated
}
```

**Why it matters**: Code like `for item in spot_state.get("balances", [])` requires real Python types.

#### 4. Verify Function Return Types and Unpack Correctly

**Problem**: Tests fail when expecting single value but function returns tuple.

**❌ WRONG - Assumes single return value**:
```python
leverage = service.get_leverage_for_order("BTC", default_leverage=3)
assert leverage == 3  # Fails! Function returns (3, True)
```

**✅ CORRECT - Unpack tuple based on function signature**:
```python
# Check function signature first:
# def get_leverage_for_order(...) -> Tuple[Optional[int], bool]:

leverage, needs_setting = service.get_leverage_for_order("BTC", default_leverage=3)
assert leverage == 3
assert needs_setting is True
```

**Why it matters**: Always check function signatures and type hints before writing tests.

#### 5. Test Expectations Must Match Actual Implementation

**Problem**: Tests fail when expectations are based on incorrect assumptions about formulas or behavior.

**❌ WRONG - Assumptions without verification**:
```python
# Assumed liquidation formula without checking implementation
assert 65000 < result.estimated_liquidation_price < 70000
```

**✅ CORRECT - Verify actual formula first**:
```python
# After checking actual liquidation price formula in implementation:
# liq_price = entry_price * (1 - 1/leverage + maintenance_margin_rate)
# For 3x leverage: 100000 * (1 - 1/3 + 0.05) ≈ 71,667
assert 70000 < result.estimated_liquidation_price < 73000
```

**Why it matters**: Tests should validate correct behavior, not enforce incorrect expectations.

### Bot Handler Testing Synchronization

**⚠️ CRITICAL**: Wizard tests need to stay in sync with code changes.

**When to check wizard tests**:
- Changing service imports in bot handlers
- Modifying handler message flows (adding progress messages)
- Updating callback data formats
- Changing field names in service responses

**Current skipped tests** (see `tests/bot/test_wizards.py`):
1. `test_market_amount_selected_parsing` - Import path changed
2. `test_close_position_execute_uses_size_closed` - Handler calls `edit_message_text` twice

**Action**: Before committing bot handler changes, run wizard tests:
```bash
uv run pytest tests/bot/test_wizards.py -v
```

### Testing Checklist

Before writing tests:
- [ ] Check service dependencies and plan mocking strategy
- [ ] Verify API response structure in actual code
- [ ] Check function signatures and return types
- [ ] Identify if function returns single value or tuple
- [ ] Review actual implementation formulas/logic

Before committing tests:
- [ ] All tests passing locally
- [ ] Mock data structures match API responses
- [ ] Function return types properly unpacked
- [ ] Service singletons mocked with explicit assignment
- [ ] Bot handler tests in sync with code changes

### Test Coverage Guidelines

**Target coverage by service type**:
- Core services (Account, Position, Order): >80%
- Advanced services (Leverage, Risk, Rebalance): >60%
- Utility functions: >90%
- Bot handlers: >50% (focus on critical paths)

**Current coverage** (reference):
- LeverageService: 86% ✅
- PositionService: 53%
- AccountService: 61%
- OrderService: 11% ⚠️ Priority for improvement

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific service tests
uv run pytest tests/services/test_leverage_service.py -v

# Run with coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run only failing tests
uv run pytest tests/ --lf
```

## Project-Specific Patterns

### Service Layer Pattern

All business logic goes in `src/services/`:
- `hyperliquid_service.py`: Hyperliquid API wrapper
- `position_service.py`: Position management logic
- `rebalance_service.py`: Portfolio rebalancing
- `scale_order_service.py`: Scale order execution
- `account_service.py`: Account operations

### Handler Organization

Telegram handlers go in `src/bot/handlers/`:
- `basic.py`: Basic commands (start, help, status)
- `account.py`: Account information commands
- `positions.py`: Position management
- `trading.py`: Trading commands
- `rebalance.py`: Rebalancing handlers
- `scale_orders.py`: Scale order handlers

### Data Models

Pydantic models go in `src/models/`:
- Validation built-in
- Type safety
- Easy serialization

### Wizard Response Pattern

**✅ ALWAYS use these utility functions** when ending ConversationHandlers to ensure the main menu appears:

Located in `src/bot/utils.py`:
- `send_success_and_end()` - For successful completions (orders placed, positions closed)
- `send_error_and_end()` - For errors (API failures, validation errors)
- `send_cancel_and_end()` - For user cancellations

**Why**: These utilities automatically show the main menu, allowing users to immediately take another action without typing `/start`.

**Example - Market Order Wizard:**
```python
from src.bot.utils import send_success_and_end, send_error_and_end

async def market_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the market order."""
    query = update.callback_query
    await query.answer()

    try:
        # Show progress
        await query.edit_message_text("⏳ Placing order...")

        # Do the work
        response = await place_order_use_case.execute(request)

        # Format success message
        success_msg = (
            f"✅ **Market Order Placed**\n\n"
            f"**Coin**: {coin}\n"
            f"**Status**: {response.status}"
        )

        # Clean up
        context.user_data.clear()

        # ✅ Automatically shows main menu!
        return await send_success_and_end(update, success_msg)

    except Exception as e:
        logger.exception("Order failed")
        context.user_data.clear()

        # ✅ Automatically shows main menu!
        return await send_error_and_end(update, f"❌ Failed: {str(e)}")
```

**Example - Cancellation Handler:**
```python
from src.bot.utils import send_cancel_and_end

async def select_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        # ✅ Automatically shows main menu!
        return await send_cancel_and_end(update, "❌ Scale order cancelled.")

    # ... continue wizard ...
```

**When creating new wizards:**
1. ✅ Import the utilities: `from src.bot.utils import send_success_and_end, send_error_and_end, send_cancel_and_end`
2. ✅ Use them for ALL `ConversationHandler.END` returns
3. ✅ NEVER manually add `reply_markup=build_main_menu()` - the utilities handle it
4. ✅ Prefix wizard handler files with `wizard_` if creating new ones

**Benefits:**
- ✨ Consistent UX across all wizards
- 🐛 Prevents forgetting to show the main menu
- 🧹 Cleaner, more maintainable code
- 📝 Self-documenting pattern

## Troubleshooting

**For comprehensive troubleshooting, always check `docs/telegram/faq.md` first!**

### Common Issues

#### Issue: Hyperliquid Connection Fails
1. Check `docs/hyperliquid/python-sdk.md` for configuration
2. Verify environment variables (wallet address, private key, API URL)
3. Test with `scripts/test_hyperliquid.py`
4. Check network/firewall
5. Verify testnet vs mainnet URL

#### Issue: Telegram Bot Not Responding
1. Verify bot token is correct
2. Check authorized users list in `.env`
3. Review logs in `logs/hyperbot.log`
4. Test with `/start` command
5. **Check `docs/telegram/faq.md`** - "Why isn't my bot responding?"
6. If in group: Check privacy mode settings with @BotFather
7. Verify bot not blocked by user

#### Issue: Orders Failing
1. Check testnet vs mainnet setting
2. Verify account has sufficient balance
3. Check order size against minimums (see meta data)
4. Review rate limits (60 req/min for Exchange API)
5. Validate order parameters
6. Check slippage settings

#### Issue: Rate Limiting
**Telegram:**
- Implement exponential backoff on `429` errors
- Check `retry_after` field in error response
- See `docs/telegram/faq.md` - "What happens if I exceed rate limits?"

**Hyperliquid:**
- Implement request queuing
- Monitor requests per minute
- Use caching for frequently accessed data

#### Issue: Messages Too Long
- Split messages over 4096 characters
- Use caption (1024 chars) + document for large content
- Implement pagination for long lists

#### Issue: Callback Queries Loading Forever
- Always call `await query.answer()` immediately
- See `docs/telegram/best-practices.md` - Common Pitfall #1

### Additional Resources

For more troubleshooting help:
- **Telegram issues**: `docs/telegram/faq.md`
- **Hyperliquid issues**: `docs/hyperliquid/api-reference.md` - Error Handling section
- **Best practices**: `docs/telegram/best-practices.md` - Common Pitfalls

## Quick Reference Links

**Within Project:**
- **Implementation**: `docs/PLAN.md`, `docs/TODO.md`
- **Hyperliquid**: `docs/hyperliquid/python-sdk.md`, `docs/hyperliquid/api-reference.md`
- **Telegram**:
  - `docs/telegram/bot-api-reference.md` - Complete API reference
  - `docs/telegram/best-practices.md` - Security, performance, patterns
  - `docs/telegram/features.md` - All bot features
  - `docs/telegram/faq.md` - FAQ and troubleshooting

**External (if needed):**
- Hyperliquid Official: https://hyperliquid.gitbook.io/hyperliquid-docs
- Hyperliquid SDK: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- python-telegram-bot: https://docs.python-telegram-bot.org
- Telegram Bot API: https://core.telegram.org/bots/api
- Telegram BotFather: https://t.me/botfather

## Remember

1. **Always read the docs first** - Don't guess at API usage
2. **Test on testnet** - Never develop on mainnet
3. **Security first** - Validate, authenticate, confirm
4. **User experience matters** - Clear messages, progress indicators, good errors
5. **Log everything** - Debugging is easier with good logs
6. **Handle errors gracefully** - Users should never see stack traces
7. **Follow testing best practices** - Use service singleton mocking pattern, match API response structures exactly
8. **Reference this file** - When in doubt, check Claude.md

---

**This document should be your first reference when working on Hyperbot. Always consult the linked documentation files for detailed implementation guidance.**
