# Hyperbot

A Python-based trading bot for Hyperliquid that manages positions and responds to TradingView webhook alerts.

## Features

- **Hyperliquid API Integration**: Connect and interact with the Hyperliquid trading platform
- **Position Management**: Automated position entry, exit, and rebalancing
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

### Start the API Server

```bash
# Using uv (recommended)
uv run python run.py

# Or activate venv first
source .venv/bin/activate  # Linux/Mac
python run.py
```

The server will start on `http://localhost:8000`

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

# Run server
uv run python run.py

# Run tests (when available)
uv run pytest
```

For more details on using uv, see [README.uv.md](README.uv.md).

## Configuration

### Hyperliquid API Setup

1. Log in to your Hyperliquid account
2. Navigate to API settings
3. Generate API key and secret
4. Add credentials to your `.env` file

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