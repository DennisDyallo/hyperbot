# 🚀 Environment Quick Reference

## ⚡ Most Common Commands

```bash
# Verify current environment
./manage-bot.sh verify-env

# Check what's running
./scripts/switch-env.sh status

# Switch to production
./scripts/switch-env.sh prod
./manage-bot.sh restart

# Switch to development
./scripts/switch-env.sh dev
./manage-bot.sh restart
```

## 📋 Environment Variables Checklist

### Production (.env.production)
```bash
ENVIRONMENT=production
HYPERLIQUID_TESTNET=false          # ⚠️ MAINNET = REAL MONEY
HYPERLIQUID_SECRET_KEY=0x...       # Your REAL private key
HYPERLIQUID_WALLET_ADDRESS=0x...   # Your REAL wallet
TELEGRAM_BOT_TOKEN=...             # From @BotFather
TELEGRAM_AUTHORIZED_USERS=123,456  # Your Telegram user IDs
API_KEY=change-this-strong-key     # ⚠️ Change from default!
```

### Development (.env.development)
```bash
ENVIRONMENT=development
HYPERLIQUID_TESTNET=true           # ✅ TESTNET = SAFE
HYPERLIQUID_SECRET_KEY=0x...       # Testnet key
HYPERLIQUID_WALLET_ADDRESS=0x...   # Testnet wallet
TELEGRAM_BOT_TOKEN=...             # Can use same bot
TELEGRAM_AUTHORIZED_USERS=123,456  # Your IDs
API_KEY=dev-key-change-in-production
```

## 🔄 Typical Workflow

### First Time Setup
```bash
# 1. Create production config
cp .env.production.example .env.production
nano .env.production  # Fill in REAL values

# 2. Verify
./scripts/verify-env.sh .env.production

# 3. Switch to it
./scripts/switch-env.sh prod

# 4. Install service
./install-service.sh

# 5. Start bot
./manage-bot.sh start

# 6. Monitor
./manage-bot.sh logs
```

### Daily Operations
```bash
# Start bot
./manage-bot.sh start

# Check status
./manage-bot.sh status

# View logs
./manage-bot.sh logs-tail

# Stop bot
./manage-bot.sh stop
```

### After Code Changes
```bash
git pull
./manage-bot.sh restart
./manage-bot.sh logs
```

### Switch Environments
```bash
# To production
./scripts/switch-env.sh prod
./manage-bot.sh restart

# To development
./scripts/switch-env.sh dev
./manage-bot.sh restart
```

## ⚠️ Safety Checks

### Before Production
```bash
# 1. Verify configuration
./manage-bot.sh verify-env

# 2. Should see:
#    ✅ All variables set
#    ⚠️ MAINNET warning (if on mainnet)
#    ✅ API_KEY changed from default

# 3. Test with small amount first!
```

### Emergency Stop
```bash
# Stop immediately
./manage-bot.sh stop

# Check what was running
./scripts/switch-env.sh status

# Fix configuration
nano .env

# Verify before restarting
./manage-bot.sh verify-env
```

## 🔍 Quick Diagnostics

### Is bot running production settings?
```bash
./scripts/switch-env.sh status
# Look for: ENVIRONMENT=production, TESTNET=false
```

### Check bot is running
```bash
./manage-bot.sh status
# Should show: active (running)
```

### See recent errors
```bash
./manage-bot.sh logs-tail
```

### Live log monitoring
```bash
./manage-bot.sh logs
# Press Ctrl+C to exit
```

## 📁 File Locations

- **Active config**: `.env` (this is what bot uses)
- **Production config**: `.env.production` (create this!)
- **Development config**: `.env.development` (optional)
- **Service file**: `/etc/systemd/system/hyperbot.service`

## 🆘 Common Issues

### "Missing environment variables"
→ Run `./manage-bot.sh verify-env` to see what's missing
→ Edit `.env` to add missing values

### "Bot won't start"
→ Check logs: `./manage-bot.sh logs-tail`
→ Verify env: `./manage-bot.sh verify-env`
→ Check service: `sudo systemctl status hyperbot`

### "Changes not taking effect"
→ Restart bot: `./manage-bot.sh restart`
→ Verify correct env loaded: `./scripts/switch-env.sh status`

### "Using wrong environment"
→ Check: `./scripts/switch-env.sh status`
→ Switch: `./scripts/switch-env.sh [dev|prod]`
→ Restart: `./manage-bot.sh restart`

## 🔗 Full Documentation

- **Complete guide**: `docs/ENVIRONMENT_SETUP.md`
- **Deployment guide**: `DEPLOYMENT.md`
- **Project guide**: `CLAUDE.md`

---

**Remember**: Always verify your environment before starting the bot!
```bash
./manage-bot.sh verify-env
```
