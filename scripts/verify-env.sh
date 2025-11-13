#!/bin/bash
# Script to verify environment variables are loaded correctly

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() { echo -e "${BLUE}═══════════════════════════════════════${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

ENV_FILE="${1:-.env}"

echo ""
print_header
echo -e "${BLUE}🔍 Environment Variables Verification${NC}"
print_header
echo ""

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file not found: $ENV_FILE"
    echo ""
    echo "Available environment files:"
    ls -1 .env* 2>/dev/null || echo "  No .env files found"
    echo ""
    exit 1
fi

print_info "Reading from: $ENV_FILE"
echo ""

# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Function to check variable
check_var() {
    local var_name=$1
    local var_value=$2
    local is_secret=$3

    if [ -z "$var_value" ]; then
        print_error "$var_name is not set or empty"
        return 1
    else
        if [ "$is_secret" = "true" ]; then
            # Mask secret values
            local masked_value="${var_value:0:4}...${var_value: -4}"
            print_success "$var_name is set: $masked_value"
        else
            print_success "$var_name is set: $var_value"
        fi
        return 0
    fi
}

# Critical variables check
echo "📋 Critical Variables:"
echo ""

check_var "ENVIRONMENT" "$ENVIRONMENT" false
check_var "HYPERLIQUID_TESTNET" "$HYPERLIQUID_TESTNET" false
check_var "HYPERLIQUID_WALLET_ADDRESS" "$HYPERLIQUID_WALLET_ADDRESS" true
check_var "HYPERLIQUID_SECRET_KEY" "$HYPERLIQUID_SECRET_KEY" true
check_var "TELEGRAM_BOT_TOKEN" "$TELEGRAM_BOT_TOKEN" true
check_var "TELEGRAM_AUTHORIZED_USERS" "$TELEGRAM_AUTHORIZED_USERS" false

echo ""
echo "📊 Configuration Summary:"
echo ""

# Show configuration summary
if [ "$ENVIRONMENT" = "production" ]; then
    print_warning "Environment: PRODUCTION"
else
    print_info "Environment: $ENVIRONMENT"
fi

if [ "$HYPERLIQUID_TESTNET" = "true" ]; then
    print_success "Hyperliquid: TESTNET (safe)"
else
    print_warning "Hyperliquid: MAINNET (⚠️  REAL MONEY)"
fi

echo ""
echo "🔐 Security Checks:"
echo ""

# Check for default/weak values
if [ "$API_KEY" = "dev-key-change-in-production" ]; then
    print_warning "API_KEY is using default value (should be changed for production)"
elif [ ${#API_KEY} -lt 20 ]; then
    print_warning "API_KEY is short (consider using a longer, more secure key)"
else
    print_success "API_KEY appears secure (length: ${#API_KEY})"
fi

# Check Hyperliquid secret key length
if [ ${#HYPERLIQUID_SECRET_KEY} -lt 20 ]; then
    print_warning "HYPERLIQUID_SECRET_KEY seems short (expected 64+ chars)"
else
    print_success "HYPERLIQUID_SECRET_KEY appears valid (length: ${#HYPERLIQUID_SECRET_KEY})"
fi

# Check for authorized users
if [ -z "$TELEGRAM_AUTHORIZED_USERS" ]; then
    print_error "No authorized Telegram users configured!"
else
    user_count=$(echo "$TELEGRAM_AUTHORIZED_USERS" | tr ',' '\n' | wc -l)
    print_success "Authorized users: $user_count"
fi

echo ""
print_header

# Final recommendation
echo ""
if [ "$ENVIRONMENT" = "production" ] && [ "$HYPERLIQUID_TESTNET" = "true" ]; then
    echo "⚠️  WARNING: ENVIRONMENT=production but HYPERLIQUID_TESTNET=true"
    echo "   This is unusual. Verify your configuration."
    echo ""
elif [ "$ENVIRONMENT" = "production" ] && [ "$HYPERLIQUID_TESTNET" = "false" ]; then
    echo "🚨 PRODUCTION MODE DETECTED"
    echo ""
    echo "   You are running on MAINNET with REAL MONEY!"
    echo "   Double-check all settings before starting the bot."
    echo ""
elif [ "$HYPERLIQUID_TESTNET" = "false" ]; then
    echo "⚠️  TESTNET=false detected"
    echo "   You are configured for MAINNET (real money)"
    echo "   Set HYPERLIQUID_TESTNET=true for safe testing"
    echo ""
else
    print_success "Configuration looks good for development/testing"
    echo ""
fi

# Test with Python to ensure settings load correctly
echo "🐍 Testing Python settings loader..."
echo ""

python_test=$(cat <<'EOF'
import sys
sys.path.insert(0, '.')
try:
    from src.config.settings import settings
    print(f"✅ Settings loaded successfully")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Testnet: {settings.HYPERLIQUID_TESTNET}")
    print(f"   Wallet: {settings.HYPERLIQUID_WALLET_ADDRESS[:8]}...{settings.HYPERLIQUID_WALLET_ADDRESS[-6:]}")
except Exception as e:
    print(f"❌ Failed to load settings: {e}")
    sys.exit(1)
EOF
)

if uv run python -c "$python_test"; then
    echo ""
    print_success "Environment configuration is valid!"
else
    echo ""
    print_error "Failed to load settings in Python"
    exit 1
fi

echo ""
