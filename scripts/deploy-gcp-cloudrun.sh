#!/bin/bash
# Deploy Hyperbot to GCP Cloud Run
# Usage: ./scripts/deploy-gcp-cloudrun.sh

set -e

# Configuration
PROJECT_ID="hyperbot-479700"  # Your GCP project ID
REGION="us-central1"  # Change to your preferred region
SERVICE_NAME="hyperbot"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Deploying Hyperbot to GCP Cloud Run...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env file from .env.example and configure it"
    exit 1
fi

# Validate required environment variables
required_vars=(
    "TELEGRAM_BOT_TOKEN"
    "TELEGRAM_AUTHORIZED_USERS"
    "HYPERLIQUID_SECRET_KEY"
    "HYPERLIQUID_WALLET_ADDRESS"
)

echo -e "${YELLOW}Validating environment variables...${NC}"
for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=$" .env || grep -q "^${var}=your_" .env; then
        echo -e "${RED}❌ Error: ${var} not configured in .env${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Environment variables validated${NC}"

# Check if secrets are set up in GCP
echo -e "${YELLOW}Checking GCP Secret Manager...${NC}"
if gcloud secrets describe lb-hyperbot-telegram-bot-token --project=${PROJECT_ID} &> /dev/null; then
    echo -e "${GREEN}✅ Secrets found in GCP Secret Manager${NC}"
    USE_SECRETS=true
else
    echo -e "${YELLOW}⚠️  Secrets not found in GCP Secret Manager${NC}"
    echo -e "${YELLOW}Run: ./scripts/setup-gcp-secrets.sh${NC}"
    echo -e "${YELLOW}Deploying with environment variables from .env...${NC}"
    USE_SECRETS=false
fi

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest .

echo -e "${YELLOW}Pushing image to Google Container Registry...${NC}"
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"

if [ "$USE_SECRETS" = true ]; then
    # Deploy using GCP Secret Manager
    echo -e "${BLUE}Using GCP Secret Manager for secrets${NC}"

    gcloud run deploy ${SERVICE_NAME} \
      --image ${IMAGE_NAME}:latest \
      --platform managed \
      --region ${REGION} \
      --project ${PROJECT_ID} \
      --min-instances 1 \
      --max-instances 1 \
      --memory 512Mi \
      --cpu 1 \
      --timeout 300 \
      --no-allow-unauthenticated \
      --set-env-vars ENVIRONMENT=production \
      --set-env-vars HYPERLIQUID_TESTNET=true \
      --set-env-vars GCP_PROJECT=${PROJECT_ID} \
      --set-secrets=TELEGRAM_BOT_TOKEN=lb-hyperbot-telegram-bot-token:latest \
      --set-secrets=TELEGRAM_AUTHORIZED_USERS=lb-hyperbot-telegram-authorized-users:latest \
      --set-secrets=HYPERLIQUID_SECRET_KEY=lb-hyperbot-hyperliquid-secret-key:latest \
      --set-secrets=HYPERLIQUID_WALLET_ADDRESS=lb-hyperbot-hyperliquid-wallet-address:latest \
      --set-secrets=API_KEY=lb-hyperbot-api-key:latest
else
    # Deploy using environment variables (fallback)
    echo -e "${BLUE}Using environment variables from .env${NC}"

    # Read environment variables from .env and format for Cloud Run
    ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | sed 's/^/--set-env-vars /' | tr '\n' ' ')

    gcloud run deploy ${SERVICE_NAME} \
      --image ${IMAGE_NAME}:latest \
      --platform managed \
      --region ${REGION} \
      --project ${PROJECT_ID} \
      --min-instances 1 \
      --max-instances 1 \
      --memory 512Mi \
      --cpu 1 \
      --timeout 300 \
      --no-allow-unauthenticated \
      --set-env-vars ENVIRONMENT=production \
      --set-env-vars HYPERLIQUID_TESTNET=true \
      $(echo $ENV_VARS)
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📊 Service Info:${NC}"
gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID}

echo ""
echo -e "${YELLOW}📝 To view logs:${NC}"
echo "gcloud logs tail --project ${PROJECT_ID} --filter=\"resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}\""
