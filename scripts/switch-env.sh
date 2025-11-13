#!/bin/bash
# Script to switch between development and production environments

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Get project directory (parent of scripts/)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

show_usage() {
    echo "🔄 Environment Switcher"
    echo ""
    echo "Usage: ./scripts/switch-env.sh [environment]"
    echo ""
    echo "Environments:"
    echo "  dev         - Switch to development (.env)"
    echo "  prod        - Switch to production (.env.production)"
    echo "  test        - Switch to testing (.env.test)"
    echo "  status      - Show current environment"
    echo ""
    echo "Examples:"
    echo "  ./scripts/switch-env.sh dev"
    echo "  ./scripts/switch-env.sh prod"
    echo "  ./scripts/switch-env.sh status"
    echo ""
}

show_current_env() {
    if [ -f ".env" ]; then
        echo "📍 Current environment configuration:"
        echo ""

        # Extract key values
        ENV_TYPE=$(grep "^ENVIRONMENT=" .env | cut -d'=' -f2)
        TESTNET=$(grep "^HYPERLIQUID_TESTNET=" .env | cut -d'=' -f2)

        echo "   ENVIRONMENT: $ENV_TYPE"
        echo "   HYPERLIQUID_TESTNET: $TESTNET"

        if [ "$TESTNET" = "false" ]; then
            echo ""
            print_warning "Running on MAINNET (real money)"
        else
            echo ""
            print_info "Running on TESTNET (safe)"
        fi
    else
        print_error "No .env file found"
    fi
}

switch_to_env() {
    local target_env=$1
    local env_file=""

    case "$target_env" in
        dev|development)
            # For dev, we might keep current .env or restore from backup
            if [ -f ".env.development" ]; then
                env_file=".env.development"
            else
                print_error "No .env.development file found"
                echo ""
                echo "Create one or use .env.example as template"
                exit 1
            fi
            ;;
        prod|production)
            env_file=".env.production"
            ;;
        test|testing)
            env_file=".env.test"
            ;;
        *)
            print_error "Unknown environment: $target_env"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    # Check if target env file exists
    if [ ! -f "$env_file" ]; then
        print_error "Environment file not found: $env_file"
        echo ""
        echo "Available environment files:"
        ls -1 .env* 2>/dev/null | grep -v ".example" | grep -v ".gitignore" || echo "  None found"
        echo ""
        exit 1
    fi

    # Backup current .env
    if [ -f ".env" ]; then
        cp .env .env.backup
        print_info "Backed up current .env to .env.backup"
    fi

    # Copy target env to .env
    cp "$env_file" .env
    print_success "Switched to $target_env environment"

    echo ""
    show_current_env

    echo ""
    print_info "Verifying configuration..."
    echo ""

    # Run verification
    ./scripts/verify-env.sh .env

    # Check if bot is running as service
    if systemctl is-active --quiet hyperbot 2>/dev/null; then
        echo ""
        print_warning "Bot is currently running as a service"
        echo ""
        echo "To apply changes, restart the bot:"
        echo "  ./manage-bot.sh restart"
        echo ""
    fi
}

# Main script
case "${1:-status}" in
    dev|development|prod|production|test|testing)
        switch_to_env "$1"
        ;;
    status|current)
        show_current_env
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Invalid command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
