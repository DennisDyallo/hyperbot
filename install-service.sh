#!/bin/bash
# Script to install and start the Hyperbot systemd service

set -e  # Exit on error

echo "🤖 Installing Hyperbot systemd service..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script needs sudo access to install the systemd service."
    echo "   You'll be prompted for your password."
    echo ""
fi

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$PROJECT_DIR/hyperbot.service"

echo "📁 Project directory: $PROJECT_DIR"
echo "📄 Service file: $SERVICE_FILE"
echo ""

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Error: hyperbot.service file not found!"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Make sure to create .env with your configuration before starting the service."
    echo ""
fi

# Copy service file to systemd directory
echo "📋 Installing service file..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/hyperbot.service

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
echo "✅ Enabling service to start on boot..."
sudo systemctl enable hyperbot.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Available commands:"
echo "   Start:   sudo systemctl start hyperbot"
echo "   Stop:    sudo systemctl stop hyperbot"
echo "   Restart: sudo systemctl restart hyperbot"
echo "   Status:  sudo systemctl status hyperbot"
echo "   Logs:    sudo journalctl -u hyperbot -f"
echo ""
echo "🚀 To start the bot now, run:"
echo "   sudo systemctl start hyperbot"
echo ""
