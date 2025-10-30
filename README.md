# Hyperbot

A TypeScript-based trading bot for Hyperliquid that manages positions and responds to TradingView webhook alerts.

## Features

- **Hyperliquid API Integration**: Connect and interact with the Hyperliquid trading platform
- **Position Management**: Automated position entry, exit, and rebalancing
- **TradingView Webhooks**: Receive and process POST webhook requests from TradingView alerts
- **Account Monitoring**: View account information, balance, and current positions

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Hyperliquid API credentials
- TradingView account (for webhook functionality)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DennisDyallo/hyperbot.git
cd hyperbot
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory:
```env
HYPERLIQUID_API_KEY=your_api_key_here
HYPERLIQUID_SECRET_KEY=your_secret_key_here
WEBHOOK_PORT=3000
WEBHOOK_SECRET=your_webhook_secret_here
```

## Usage

### Development Mode

Run the bot in development mode with auto-reload:
```bash
npm run dev
```

### Production Mode

Build and run the bot:
```bash
npm run build
npm start
```

### Available Scripts

- `npm run build` - Compile TypeScript to JavaScript
- `npm run start` - Run the compiled application
- `npm run dev` - Run in development mode with ts-node
- `npm run watch` - Compile TypeScript in watch mode
- `npm run clean` - Remove build artifacts

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