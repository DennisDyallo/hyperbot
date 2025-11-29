#!/bin/bash
# Setup GCP Secret Manager secrets for Hyperbot
# Usage: ./scripts/setup-gcp-secrets.sh

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT:-hyperbot-479700}"  # Your GCP project ID or set GCP_PROJECT env var
REGION="${GCP_REGION:-us-central1}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Setting up GCP Secret Manager for Hyperbot${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env from .env.example first"
    exit 1
fi

# Validate gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable Secret Manager API
echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com

echo ""
echo -e "${BLUE}Creating secrets from .env file...${NC}"
echo ""

# Function to create or update secret
create_or_update_secret() {
    local SECRET_NAME=$1
    local ENV_VAR_NAME=$2

    # Get value from .env
    local SECRET_VALUE=$(grep "^${ENV_VAR_NAME}=" .env | cut -d '=' -f2-)

    # Skip if not set or is placeholder
    if [ -z "$SECRET_VALUE" ] || [[ "$SECRET_VALUE" == "your_"* ]]; then
        echo -e "${YELLOW}⏭️  Skipping ${SECRET_NAME} (not configured in .env)${NC}"
        return
    fi

    # Check if secret exists
    if gcloud secrets describe ${SECRET_NAME} --project=${PROJECT_ID} &> /dev/null; then
        echo -e "${YELLOW}📝 Updating existing secret: ${SECRET_NAME}${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets versions add ${SECRET_NAME} --data-file=-
    else
        echo -e "${GREEN}✨ Creating new secret: ${SECRET_NAME}${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets create ${SECRET_NAME} \
            --data-file=- \
            --replication-policy="automatic"
    fi
}

# Create/update secrets
create_or_update_secret "lb-hyperbot-telegram-bot-token" "TELEGRAM_BOT_TOKEN"
create_or_update_secret "lb-hyperbot-telegram-authorized-users" "TELEGRAM_AUTHORIZED_USERS"
create_or_update_secret "lb-hyperbot-hyperliquid-secret-key" "HYPERLIQUID_SECRET_KEY"
create_or_update_secret "lb-hyperbot-hyperliquid-wallet-address" "HYPERLIQUID_WALLET_ADDRESS"
create_or_update_secret "lb-hyperbot-api-key" "API_KEY"echo ""
echo -e "${GREEN}✅ Secrets created/updated successfully!${NC}"
echo ""

# Grant Cloud Run service account access to secrets
echo -e "${YELLOW}Setting up IAM permissions...${NC}"
echo ""

# Get the default compute service account
COMPUTE_SA="${PROJECT_ID}@appspot.gserviceaccount.com"

echo -e "${BLUE}Granting Secret Manager access to: ${COMPUTE_SA}${NC}"

for SECRET_NAME in lb-hyperbot-telegram-bot-token lb-hyperbot-telegram-authorized-users lb-hyperbot-hyperliquid-secret-key lb-hyperbot-hyperliquid-wallet-address lb-hyperbot-api-key; do
    if gcloud secrets describe ${SECRET_NAME} --project=${PROJECT_ID} &> /dev/null; then
        gcloud secrets add-iam-policy-binding ${SECRET_NAME} \
            --member="serviceAccount:${COMPUTE_SA}" \
            --role="roles/secretmanager.secretAccessor" \
            --project=${PROJECT_ID} &> /dev/null || true
        echo -e "${GREEN}✅ ${SECRET_NAME}${NC}"
    fi
done

echo ""
echo -e "${GREEN}🎉 Secret Manager setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Deploy with: ./scripts/deploy-gcp-cloudrun.sh"
echo "2. Secrets will be automatically loaded in Cloud Run"
echo ""
echo -e "${YELLOW}To verify secrets:${NC}"
echo "gcloud secrets list --project=${PROJECT_ID}"
echo ""
echo -e "${YELLOW}To view a secret value:${NC}"
echo "gcloud secrets versions access latest --secret=\"lb-hyperbot-telegram-bot-token\" --project=${PROJECT_ID}"
