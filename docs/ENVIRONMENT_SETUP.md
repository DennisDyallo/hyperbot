# Environment Configuration Guide

This guide explains how to manage environment variables for development and production deployments.

## 🔑 How Environment Variables Work

### Loading Order

1. **systemd service** loads `.env` via `EnvironmentFile` directive
2. **Python code** loads `.env` via `python-dotenv` in `src/config/settings.py`
3. **Environment variables** are read by `Settings` class

### Configuration Flow

```
.env file → systemd → Python process → Settings class → Your code
```

## 📁 Environment Files

### Available Files

- **`.env`** - Active configuration (used by bot)
- **`.env.example`** - Template for development
- **`.env.production.example`** - Template for production
- **`.env.development`** - Development configuration (optional)
- **`.env.production`** - Production configuration (create this!)

### File Priority

The bot uses **`.env`** file. You can:
1. Edit `.env` directly, OR
2. Create environment-specific files and switch between them

## 🚀 Quick Start

### Option 1: Direct Configuration (Simple)

Edit `.env` directly with your production values:

```bash
# Edit .env
nano .env

# Verify configuration
./manage-bot.sh verify-env

# Start bot
./manage-bot.sh start
```

### Option 2: Multiple Environments (Recommended)

Create separate environment files:

```bash
# 1. Create production config
cp .env.production.example .env.production
nano .env.production  # Fill in production values

# 2. Create development config (if different)
cp .env .env.development

# 3. Switch to production
./scripts/switch-env.sh prod

# 4. Verify
./manage-bot.sh verify-env

# 5. Start bot
./manage-bot.sh start
```

## ⚙️ Configuration Variables

### Critical Variables

#### `ENVIRONMENT`
- **Values**: `development`, `production`
- **Purpose**: Identifies runtime environment
- **Production**: `ENVIRONMENT=production`

#### `HYPERLIQUID_TESTNET`
- **Values**: `true`, `false`
- **Purpose**: Switch between testnet (safe) and mainnet (real money)
- **Development**: `HYPERLIQUID_TESTNET=true`
- **Production**: `HYPERLIQUID_TESTNET=false` ⚠️ **REAL MONEY**

#### `HYPERLIQUID_SECRET_KEY`
- **Format**: Hex string (0x...)
- **Purpose**: Private key for signing transactions
- **Security**: **NEVER commit this to git!**

#### `HYPERLIQUID_WALLET_ADDRESS`
- **Format**: Ethereum address (0x...)
- **Purpose**: Your trading wallet address

#### `TELEGRAM_BOT_TOKEN`
- **Format**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- **Purpose**: Bot authentication token from @BotFather
- **Get it**: Message @BotFather on Telegram

#### `TELEGRAM_AUTHORIZED_USERS`
- **Format**: Comma-separated user IDs: `123456789,987654321`
- **Purpose**: Only these users can control the bot
- **Get your ID**: Message @userinfobot on Telegram

### Optional Variables

#### `DEFAULT_LEVERAGE`
- **Default**: `3`
- **Purpose**: Default leverage for trades
- **Recommendation**: 3-5x for conservative trading

#### `MAX_LEVERAGE_WARNING`
- **Default**: `5`
- **Purpose**: Show warning above this leverage

#### `LOG_LEVEL`
- **Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Default**: `INFO`
- **Production**: `INFO` or `WARNING`

#### `API_KEY`
- **Purpose**: API authentication key
- **Production**: Change from default value!

## 🔍 Verification Tools

### Verify Current Configuration

```bash
# Quick verification
./manage-bot.sh verify-env

# Or directly
./scripts/verify-env.sh

# Verify specific file
./scripts/verify-env.sh .env.production
```

This checks:
- ✅ All required variables are set
- ✅ Secret keys are valid length
- ✅ Configuration is consistent (testnet vs mainnet)
- ✅ Python can load settings correctly

### Check Current Environment

```bash
# Show active configuration
./scripts/switch-env.sh status
```

## 🔄 Switching Environments

### Switch to Production

```bash
./scripts/switch-env.sh prod
./manage-bot.sh restart  # If bot is running
```

### Switch to Development

```bash
./scripts/switch-env.sh dev
./manage-bot.sh restart  # If bot is running
```

### What Switching Does

1. Backs up current `.env` to `.env.backup`
2. Copies target environment file to `.env`
3. Verifies new configuration
4. Shows environment summary

## 🔐 Production Checklist

Before running in production:

### 1. Configuration
- [ ] Created `.env.production` with production values
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `HYPERLIQUID_TESTNET=false` (if using mainnet)
- [ ] Changed `API_KEY` from default value
- [ ] Added authorized Telegram user IDs

### 2. Security
- [ ] Never committed `.env` or `.env.production` to git
- [ ] Private keys are secure
- [ ] Only trusted users in `TELEGRAM_AUTHORIZED_USERS`
- [ ] Strong API key (20+ characters)

### 3. Verification
```bash
# Verify configuration
./manage-bot.sh verify-env

# Check for real money warning
# Should see: "⚠️ Hyperliquid: MAINNET (real money)"
```

### 4. Testing
```bash
# Start bot
./manage-bot.sh start

# Watch logs
./manage-bot.sh logs

# Test with small amounts first!
```

## 🛡️ Security Best Practices

### Protect Your Keys

**❌ NEVER:**
- Commit `.env` files to git (they're in `.gitignore`)
- Share your private keys
- Post keys in Telegram/Slack/Discord
- Use production keys in development

**✅ ALWAYS:**
- Use separate keys for testnet and mainnet
- Rotate keys periodically
- Use API wallet (not main wallet) for trading
- Keep backup of keys in secure location (password manager)

### `.gitignore` Protection

Your `.gitignore` should include:
```gitignore
.env
.env.production
.env.development
.env.test
.env.local
.env.backup
```

### Environment File Permissions

```bash
# Restrict access to environment files
chmod 600 .env
chmod 600 .env.production

# Only owner can read/write
```

## 🧪 Development Workflow

### Recommended Setup

```bash
# 1. Development environment (testnet)
cp .env.example .env.development
nano .env.development
# Set HYPERLIQUID_TESTNET=true

# 2. Production environment (mainnet)
cp .env.production.example .env.production
nano .env.production
# Set HYPERLIQUID_TESTNET=false
# Use REAL production keys

# 3. Use development by default
./scripts/switch-env.sh dev

# 4. Run bot for testing
uv run python -m src.bot.main

# 5. When ready for production
./scripts/switch-env.sh prod
./install-service.sh
./manage-bot.sh start
```

## 🐛 Troubleshooting

### Bot Won't Start - Missing Variables

**Error**: `Missing required environment variables`

**Solution**:
```bash
# Check what's missing
./manage-bot.sh verify-env

# Look for ❌ marks
# Fill in missing values in .env
```

### Bot Using Wrong Environment

**Problem**: Bot is on testnet but I want production

**Solution**:
```bash
# Check current environment
./scripts/switch-env.sh status

# Switch to production
./scripts/switch-env.sh prod

# Restart bot
./manage-bot.sh restart
```

### Changes Not Taking Effect

**Problem**: Edited `.env` but bot still uses old values

**Solution**:
```bash
# Restart bot to reload environment
./manage-bot.sh restart

# Verify new settings loaded
./manage-bot.sh logs-tail
```

### Service Can't Read `.env`

**Problem**: `EnvironmentFile` error in systemd

**Check**:
1. `.env` file exists in project directory
2. File has read permissions
3. No syntax errors in `.env` (no spaces around `=`)

```bash
# Check file exists
ls -l .env

# Check permissions
chmod 644 .env

# Verify syntax (no spaces!)
# ✅ CORRECT: ENVIRONMENT=production
# ❌ WRONG: ENVIRONMENT = production
```

### Testnet vs Mainnet Confusion

**Symptoms**:
- Orders failing
- Can't find positions
- API errors

**Check**:
```bash
./scripts/switch-env.sh status

# Should show:
# HYPERLIQUID_TESTNET: true  (for testnet)
# HYPERLIQUID_TESTNET: false (for mainnet)
```

## 📊 Environment Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **ENVIRONMENT** | `development` | `production` |
| **HYPERLIQUID_TESTNET** | `true` | `false` |
| **API_KEY** | Default OK | **Must change!** |
| **Keys** | Testnet keys | Real keys |
| **Risk** | Zero (testnet) | **Real money!** |
| **Monitoring** | Optional | **Critical** |
| **Logs** | `DEBUG` OK | `INFO` recommended |

## 🔄 Update Workflow

### After Code Changes

```bash
# 1. Pull latest code
git pull

# 2. Check for new env vars
diff .env .env.example

# 3. Add any new variables to .env

# 4. Restart bot
./manage-bot.sh restart

# 5. Verify
./manage-bot.sh logs-tail
```

### After Environment Changes

```bash
# 1. Edit .env
nano .env

# 2. Verify syntax
./manage-bot.sh verify-env

# 3. Restart bot
./manage-bot.sh restart

# 4. Check logs
./manage-bot.sh logs
```

## 📞 Support Commands

```bash
# Show current environment
./scripts/switch-env.sh status

# Verify configuration
./manage-bot.sh verify-env

# Check bot status
./manage-bot.sh status

# View logs
./manage-bot.sh logs-tail

# Test configuration in Python
uv run python -c "from src.config.settings import settings; print(settings.ENVIRONMENT, settings.HYPERLIQUID_TESTNET)"
```

## ❓ FAQ

**Q: Does the systemd service use `.env`?**
A: Yes! The service file has `EnvironmentFile=/home/dyallo/Code/hyperbot/.env`

**Q: Can I use environment variables instead of `.env`?**
A: Yes, but `.env` is more convenient. systemd loads `.env` automatically.

**Q: What if I want different settings for API vs Bot?**
A: Both use the same `.env` file. They're designed to share configuration.

**Q: How do I know which environment is active?**
A: Run `./scripts/switch-env.sh status` or `./manage-bot.sh verify-env`

**Q: Can I run both testnet and mainnet simultaneously?**
A: Not with one service. You'd need separate service files and directories.

**Q: Is it safe to commit `.env.example`?**
A: Yes! `.env.example` has no real keys. Never commit `.env` or `.env.production`.

## 🚨 Emergency: Rolled Out Wrong Environment

If you accidentally started the bot with wrong settings:

```bash
# 1. STOP THE BOT IMMEDIATELY
./manage-bot.sh stop

# 2. Check what was running
./scripts/switch-env.sh status

# 3. Switch to correct environment
./scripts/switch-env.sh [dev|prod]

# 4. Verify before starting
./manage-bot.sh verify-env

# 5. Restart with correct config
./manage-bot.sh start

# 6. Monitor closely
./manage-bot.sh logs
```

---

**Remember**: Always verify your environment configuration before starting the bot, especially when using mainnet (real money)!
