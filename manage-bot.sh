#!/bin/bash
# Hyperbot management script - Easy commands for controlling the bot

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check if service is installed
check_service_installed() {
    if ! systemctl list-unit-files | grep -q "hyperbot.service"; then
        print_error "Service not installed!"
        echo ""
        echo "Run './install-service.sh' first to install the systemd service."
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "🤖 Hyperbot Management Script"
    echo ""
    echo "Usage: ./manage-bot.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the bot"
    echo "  stop        - Stop the bot"
    echo "  restart     - Restart the bot"
    echo "  status      - Show bot status"
    echo "  logs        - Show live logs (Ctrl+C to exit)"
    echo "  logs-tail   - Show last 50 log lines"
    echo "  verify-env  - Check environment configuration"
    echo "  enable      - Enable auto-start on boot"
    echo "  disable     - Disable auto-start on boot"
    echo "  install     - Install systemd service"
    echo "  uninstall   - Remove systemd service"
    echo ""
}

# Command handling
case "$1" in
    start)
        check_service_installed
        print_info "Starting Hyperbot..."
        sudo systemctl start hyperbot
        sleep 2
        if systemctl is-active --quiet hyperbot; then
            print_status "Bot started successfully!"
            echo ""
            print_info "Check logs with: ./manage-bot.sh logs"
        else
            print_error "Failed to start bot"
            echo ""
            print_info "Check status with: ./manage-bot.sh status"
        fi
        ;;

    stop)
        check_service_installed
        print_info "Stopping Hyperbot..."
        sudo systemctl stop hyperbot
        sleep 1
        print_status "Bot stopped"
        ;;

    restart)
        check_service_installed
        print_info "Restarting Hyperbot..."
        sudo systemctl restart hyperbot
        sleep 2
        if systemctl is-active --quiet hyperbot; then
            print_status "Bot restarted successfully!"
            echo ""
            print_info "Check logs with: ./manage-bot.sh logs"
        else
            print_error "Failed to restart bot"
            echo ""
            print_info "Check status with: ./manage-bot.sh status"
        fi
        ;;

    status)
        check_service_installed
        sudo systemctl status hyperbot --no-pager
        ;;

    logs)
        check_service_installed
        print_info "Showing live logs (Ctrl+C to exit)..."
        echo ""
        sudo journalctl -u hyperbot -f
        ;;

    logs-tail)
        check_service_installed
        print_info "Last 50 log lines:"
        echo ""
        sudo journalctl -u hyperbot -n 50 --no-pager
        ;;

    verify-env)
        if [ -f "./scripts/verify-env.sh" ]; then
            ./scripts/verify-env.sh
        else
            print_error "verify-env.sh not found in scripts/"
            exit 1
        fi
        ;;

    enable)
        check_service_installed
        print_info "Enabling auto-start on boot..."
        sudo systemctl enable hyperbot
        print_status "Auto-start enabled"
        ;;

    disable)
        check_service_installed
        print_info "Disabling auto-start on boot..."
        sudo systemctl disable hyperbot
        print_status "Auto-start disabled"
        ;;

    install)
        if [ -f "./install-service.sh" ]; then
            ./install-service.sh
        else
            print_error "install-service.sh not found!"
            exit 1
        fi
        ;;

    uninstall)
        check_service_installed
        print_warning "Uninstalling Hyperbot service..."
        sudo systemctl stop hyperbot 2>/dev/null || true
        sudo systemctl disable hyperbot
        sudo rm /etc/systemd/system/hyperbot.service
        sudo systemctl daemon-reload
        print_status "Service uninstalled"
        ;;

    *)
        show_usage
        exit 1
        ;;
esac
