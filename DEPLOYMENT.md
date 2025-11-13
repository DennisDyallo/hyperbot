# Hyperbot Deployment Guide

This guide explains how to run Hyperbot as a persistent background service that survives computer sleep/wake cycles.

## 🎯 Problem Solved

Running the bot via VS Code tasks.json means:
- ❌ Process dies if VS Code closes
- ❌ Process suspends when computer sleeps
- ❌ No automatic restart on crashes
- ❌ No automatic start on boot

**systemd service solves all of these!**

## 🚀 Quick Start (Recommended Method)

### 1. Install the Service

```bash
./install-service.sh
```

This will:
- Copy the service file to `/etc/systemd/system/`
- Enable the service to auto-start on boot
- Configure automatic restart on crashes

### 2. Start the Bot

```bash
./manage-bot.sh start
```

### 3. Check Status

```bash
./manage-bot.sh status
```

### 4. View Logs

```bash
# Live logs (Ctrl+C to exit)
./manage-bot.sh logs

# Last 50 lines
./manage-bot.sh logs-tail
```

## 📚 Management Commands

Use `./manage-bot.sh` for easy management:

```bash
./manage-bot.sh start       # Start the bot
./manage-bot.sh stop        # Stop the bot
./manage-bot.sh restart     # Restart the bot
./manage-bot.sh status      # Show bot status
./manage-bot.sh logs        # Show live logs
./manage-bot.sh logs-tail   # Show last 50 log lines
./manage-bot.sh enable      # Enable auto-start on boot
./manage-bot.sh disable     # Disable auto-start on boot
./manage-bot.sh uninstall   # Remove the service
```

## 🔄 Raw systemctl Commands

If you prefer using systemctl directly:

```bash
# Start/stop/restart
sudo systemctl start hyperbot
sudo systemctl stop hyperbot
sudo systemctl restart hyperbot

# Status
sudo systemctl status hyperbot

# Enable/disable auto-start
sudo systemctl enable hyperbot
sudo systemctl disable hyperbot

# View logs
sudo journalctl -u hyperbot -f          # Live logs
sudo journalctl -u hyperbot -n 100      # Last 100 lines
sudo journalctl -u hyperbot --since today  # Today's logs
```

## ✅ Benefits of systemd Service

1. **Survives Sleep/Wake**: Bot keeps running when computer sleeps
2. **Auto-Restart**: Automatically restarts if it crashes
3. **Auto-Start**: Starts automatically on boot (if enabled)
4. **Proper Logging**: All logs go to systemd journal
5. **Easy Management**: Start/stop/restart with simple commands
6. **Security**: Runs with proper permissions and isolation

## 🔧 Configuration

### Environment Variables

The service loads environment variables from `.env` in the project directory.

Make sure your `.env` contains:
```bash
HYPERLIQUID_WALLET_ADDRESS=your_address
HYPERLIQUID_PRIVATE_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_AUTHORIZED_USERS=["user_id"]
# ... other variables
```

### Service File Location

- Service definition: `/etc/systemd/system/hyperbot.service`
- Source file: `/home/dyallo/Code/hyperbot/hyperbot.service`

### Modifying the Service

If you need to modify the service (e.g., change WorkingDirectory or User):

1. Edit `hyperbot.service` in the project directory
2. Reinstall: `./install-service.sh`
3. Restart: `./manage-bot.sh restart`

## 🐛 Troubleshooting

### Bot Won't Start

```bash
# Check status for errors
./manage-bot.sh status

# Check recent logs
./manage-bot.sh logs-tail

# Common issues:
# - Missing .env file
# - Invalid environment variables
# - Wrong WorkingDirectory in service file
# - Permission issues
```

### View Detailed Logs

```bash
# All logs since service started
sudo journalctl -u hyperbot --no-pager

# Logs from the last hour
sudo journalctl -u hyperbot --since "1 hour ago"

# Logs with specific priority (errors only)
sudo journalctl -u hyperbot -p err
```

### Service Keeps Restarting

```bash
# Check what's causing crashes
./manage-bot.sh logs-tail

# The service will automatically retry up to 5 times
# with 10 second delays between attempts
```

### Check if Service is Enabled

```bash
systemctl is-enabled hyperbot

# Output:
# - "enabled" = will start on boot
# - "disabled" = won't start on boot
```

## 🔐 Security Notes

The service includes security hardening:
- `NoNewPrivileges=true`: Prevents privilege escalation
- `PrivateTmp=true`: Isolated /tmp directory
- Runs as your user (not root)

## 📊 Monitoring

### Check if Bot is Running

```bash
# Quick check
systemctl is-active hyperbot

# Detailed status
./manage-bot.sh status
```

### View Resource Usage

```bash
# CPU and memory usage
systemctl status hyperbot

# More detailed stats
sudo systemd-cgtop
```

## 🔄 Updating the Bot

When you update the bot code:

```bash
# Pull latest changes
git pull

# Install dependencies if needed
uv sync

# Restart the service to use new code
./manage-bot.sh restart

# Check logs to ensure it started correctly
./manage-bot.sh logs-tail
```

## 🚫 Uninstalling

To completely remove the service:

```bash
./manage-bot.sh uninstall
```

This will:
- Stop the bot
- Disable auto-start
- Remove the service file
- Reload systemd

## 🆘 Alternative: tmux (Quick Alternative)

If you don't want to use systemd, you can use tmux:

```bash
# Install tmux
sudo pacman -S tmux

# Start a tmux session
tmux new -s hyperbot

# Run the bot
uv run python -m src.bot.main

# Detach: Press Ctrl+B, then D

# Reattach later
tmux attach -t hyperbot

# Kill session
tmux kill-session -t hyperbot
```

**Note**: tmux is simpler but doesn't provide auto-restart or guaranteed survival of sleep cycles.

## ❓ FAQ

**Q: Will the bot survive computer sleep?**
A: Yes! systemd services continue running after wake.

**Q: Will the bot start automatically on boot?**
A: Yes, if you ran `./manage-bot.sh enable` (or `./install-service.sh` does this automatically).

**Q: Can I still use VS Code tasks.json for development?**
A: Yes! Use tasks.json for development/testing, and systemd service for production running.

**Q: How do I see errors?**
A: `./manage-bot.sh logs-tail` or `./manage-bot.sh logs` for live output.

**Q: Can I run multiple bots?**
A: Yes, but you'll need to create separate service files with different names and WorkingDirectory settings.

## 📞 Support

For issues:
1. Check logs: `./manage-bot.sh logs-tail`
2. Check status: `./manage-bot.sh status`
3. Review CLAUDE.md for development guidance
4. Check docs/telegram/faq.md for bot-specific issues
