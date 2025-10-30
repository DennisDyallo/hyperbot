# Hyperbot Development Guide for Claude

This document provides comprehensive guidance for developing and maintaining the Hyperbot trading bot. Always reference the local documentation files when working on features.

## Project Overview

Hyperbot is a Python-based trading bot that integrates:
- **Hyperliquid**: Decentralized exchange for crypto trading
- **Telegram**: User interface for bot control and notifications
- **TradingView**: Webhook-based trading signals

## Documentation Structure

All documentation is stored locally in the `/docs` directory:

```
docs/
├── hyperliquid/
│   ├── python-sdk.md          # Official SDK documentation
│   └── api-reference.md       # Complete API reference with examples
└── telegram/
    ├── bot-api-reference.md   # python-telegram-bot library guide
    ├── best-practices.md      # Security, performance, patterns
    └── features.md            # All Telegram bot features
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

**Always read**: `docs/telegram/bot-api-reference.md`, `docs/telegram/best-practices.md`, `docs/telegram/features.md`

**Read before:**
- Creating new commands
- Implementing inline keyboards
- Handling user input
- Setting up conversations
- Sending notifications
- Error handling
- Authentication and security
- Performance optimization

**Key sections to reference:**
- Handler types (Command, Message, Callback)
- Inline keyboard creation
- ConversationHandler for multi-step flows
- Security patterns (authentication decorator)
- Rate limiting
- Error handling
- Logging best practices

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

**Always:**
- Initialize service before use
- Use testnet for development (`HYPERLIQUID_TESTNET=true`)
- Handle rate limits (60 requests/minute)
- Validate order sizes against minimums
- Check slippage on market orders
- Log all trading operations

**Never:**
- Place orders without confirmation on mainnet
- Ignore error responses
- Bypass size validation
- Skip health checks

### Telegram

**Always:**
- Use `@authorized_only` decorator for sensitive commands
- Answer callback queries immediately
- Provide clear error messages
- Show progress for long operations
- Use markdown formatting for readability
- Log user actions

**Never:**
- Expose API keys or private keys
- Send messages without rate limiting
- Forget to handle exceptions
- Ignore user feedback
- Use blocking operations

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

## Troubleshooting

### Issue: Hyperliquid Connection Fails
1. Check `docs/hyperliquid/python-sdk.md` for configuration
2. Verify environment variables
3. Test with `scripts/test_hyperliquid.py`
4. Check network/firewall

### Issue: Telegram Bot Not Responding
1. Verify bot token
2. Check authorized users list
3. Review logs in `logs/hyperbot.log`
4. Test with `/start` command

### Issue: Orders Failing
1. Check testnet vs mainnet setting
2. Verify account has sufficient balance
3. Check order size against minimums
4. Review rate limits

## Quick Reference Links

**Within Project:**
- Hyperliquid SDK: `docs/hyperliquid/python-sdk.md`
- Hyperliquid API: `docs/hyperliquid/api-reference.md`
- Telegram API: `docs/telegram/bot-api-reference.md`
- Best Practices: `docs/telegram/best-practices.md`
- Features: `docs/telegram/features.md`

**External (if needed):**
- Hyperliquid Official: https://hyperliquid.gitbook.io/hyperliquid-docs
- python-telegram-bot: https://docs.python-telegram-bot.org
- Telegram Bot API: https://core.telegram.org/bots/api

## Remember

1. **Always read the docs first** - Don't guess at API usage
2. **Test on testnet** - Never develop on mainnet
3. **Security first** - Validate, authenticate, confirm
4. **User experience matters** - Clear messages, progress indicators, good errors
5. **Log everything** - Debugging is easier with good logs
6. **Handle errors gracefully** - Users should never see stack traces
7. **Reference this file** - When in doubt, check Claude.md

---

**This document should be your first reference when working on Hyperbot. Always consult the linked documentation files for detailed implementation guidance.**
