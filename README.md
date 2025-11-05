# Hyperbot

A Python-based trading bot for Hyperliquid that manages positions and responds to TradingView webhook alerts.

## Features

- **Telegram Bot**: Interactive trading interface with wizards for market orders, scale orders, and portfolio rebalancing
- **Hyperliquid API Integration**: Connect and interact with the Hyperliquid trading platform
- **Position Management**: Automated position entry, exit, and rebalancing
- **Scale Orders**: DCA (Dollar Cost Averaging) in/out with customizable distribution
- **Leverage Management**: Per-coin leverage control with safety validations
- **TradingView Webhooks**: Receive and process POST webhook requests from TradingView alerts
- **Account Monitoring**: View account information, balance, and current positions
- **FastAPI REST API**: Interactive API with Swagger UI
- **Modern Python**: Uses `uv` for fast, reliable dependency management

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Hyperliquid API credentials
- TradingView account (for webhook functionality)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DennisDyallo/hyperbot.git
cd hyperbot
```

2. Install dependencies with uv:
```bash
# Install uv if you haven't already (see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates .venv automatically)
uv sync
```

3. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

### Start the Telegram Bot

```bash
# Using uv (recommended)
uv run python -m src.bot.main

# Or activate venv first
source .venv/bin/activate  # Linux/Mac
python -m src.bot.main
```

The bot will start polling for Telegram messages. Make sure you've configured:
- `TELEGRAM_BOT_TOKEN` in your `.env` file
- `TELEGRAM_AUTHORIZED_USERS` (comma-separated user IDs)

### Start the API Server

```bash
# Using uv (recommended)
uv run python run.py

# Or activate venv first
source .venv/bin/activate  # Linux/Mac
python run.py
```

The server will start on `http://localhost:8000`

### Start Both (API + Bot)

For development, you can run both in separate terminals, or use VS Code tasks:
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Tasks: Run Task"
- Select "Start Both (API + Bot)"

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs (interactive API docs)
- **ReDoc**: http://localhost:8000/redoc (alternative docs)
- **Health Check**: http://localhost:8000/health

### Available Commands

```bash
# Install dependencies
uv sync

# Install with dev tools
uv sync --extra dev

# Run API server
uv run python run.py

# Run Telegram bot
uv run python -m src.bot.main

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Format code
uv run black src/ tests/
```

For more details on using uv, see [README.uv.md](README.uv.md).

### VS Code Tasks

The project includes VS Code tasks for common operations. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type "Tasks: Run Task" to access:

- **Start API Server** - Launch the FastAPI server
- **Start Telegram Bot** - Launch the Telegram bot
- **Start Both (API + Bot)** - Launch both in parallel
- **Run Tests** - Execute all tests with verbose output
- **Run Tests with Coverage** - Run tests and generate coverage report
- **Install Dependencies** - Install/update all dependencies
- **Format Code** - Format code with Black

## Configuration

### Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather) on Telegram:
   - Send `/newbot` to BotFather
   - Follow the instructions to choose a name and username
   - Copy the bot token provided

2. Get your Telegram user ID:
   - Send a message to [@userinfobot](https://t.me/userinfobot)
   - It will reply with your user ID (a number like `123456789`)

3. Add to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_AUTHORIZED_USERS=123456789,987654321  # Comma-separated user IDs
   ```

4. Available bot commands:
   - `/start` - Welcome message and main menu
   - `/help` - Show all available commands
   - `/account` - View account balance and summary
   - `/positions` - List all open positions
   - `/market` - Place market order (wizard)
   - `/close` - Close position (wizard)
   - `/rebalance` - Rebalance portfolio
   - `/scale` - Scale order wizard (DCA in/out)
   - `/leverage` - View/manage leverage settings

### Hyperliquid API Setup

1. Log in to your Hyperliquid account
2. Navigate to API settings
3. Generate API key and secret
4. Add credentials to your `.env` file:
   ```env
   HYPERLIQUID_WALLET_ADDRESS=0x...
   HYPERLIQUID_PRIVATE_KEY=0x...
   HYPERLIQUID_TESTNET=true  # Set to false for mainnet
   ```

### TradingView Webhook Setup

1. Create an alert in TradingView
2. In the alert settings, enable webhook
3. Set webhook URL to: `http://your-server:3000/webhook`
4. Configure the alert message payload (JSON format):

```json
{
  "action": "enter",
  "symbol": "BTC",
  "side": "long",
  "size": 0.1,
  "secret": "your_webhook_secret_here"
}
```

## API Endpoints

### Webhook Endpoint

**POST** `/webhook`

Receives trading signals from TradingView.

**Request Body:**
```json
{
  "action": "enter|exit|rebalance",
  "symbol": "BTC",
  "side": "long|short",
  "size": 0.1,
  "secret": "your_webhook_secret"
}
```

### Account Info

**GET** `/account`

Returns current account information, balance, and positions.

**Response:**
```json
{
  "balance": 10000.00,
  "equity": 10500.00,
  "positions": [
    {
      "symbol": "BTC",
      "side": "long",
      "size": 0.1,
      "entryPrice": 50000.00,
      "unrealizedPnl": 500.00
    }
  ]
}
```

## Position Management Actions

### Enter Position
Opens a new position or adds to an existing one.

### Exit Position
Closes an existing position partially or completely.

### Rebalance
Adjusts position sizes to match target allocations.

## Security Considerations

- Store API credentials securely in environment variables
- Use HTTPS for webhook endpoints in production
- Implement webhook signature verification
- Set up rate limiting for API requests
- Enable IP whitelisting on Hyperliquid if available

## Error Handling

The bot includes comprehensive error handling for:
- API connection failures
- Invalid webhook payloads
- Insufficient balance
- Position size limits
- Network timeouts

## Logging

Logs are written to the console and can be configured for file output. Log levels include:
- `info` - General information
- `warn` - Warnings and non-critical issues
- `error` - Errors and exceptions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

ISC

## Disclaimer

This bot is for educational and informational purposes only. Trading cryptocurrency involves substantial risk of loss. Use at your own risk. The developers are not responsible for any financial losses incurred while using this software.

## Support

For issues, questions, or contributions, please open an issue on GitHub.