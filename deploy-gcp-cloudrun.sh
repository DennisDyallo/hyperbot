#!/bin/bash
# deploy-gcp-cloudrun.sh
# Deploy Hyperbot to Google Cloud Platform Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-hyperbot-telegram}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MIN_INSTANCES="${MIN_INSTANCES:-1}"  # Keep at least 1 instance for bot polling
MAX_INSTANCES="${MAX_INSTANCES:-3}"
MEMORY="${MEMORY:-512Mi}"
CPU="${CPU:-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable not set${NC}"
    echo "Usage: GCP_PROJECT_ID=your-project-id ./deploy-gcp-cloudrun.sh"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Create a .env file with your configuration before deploying"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Hyperbot to GCP Cloud Run${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Step 1: Build and push Docker image
echo -e "${YELLOW}Step 1/3: Building and pushing Docker image...${NC}"
gcloud builds submit \
    --project="$PROJECT_ID" \
    --tag="$IMAGE_NAME" \
    .

echo -e "${GREEN}✓ Image built and pushed successfully${NC}"
echo ""

# Step 2: Prepare environment variables from .env file
echo -e "${YELLOW}Step 2/3: Preparing environment variables...${NC}"

# Convert .env to Cloud Run format (KEY=value becomes --set-env-vars KEY=value)
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | tr '\n' ',' | sed 's/,$//')

echo -e "${GREEN}✓ Environment variables prepared${NC}"
echo ""

# Step 3: Deploy to Cloud Run
echo -e "${YELLOW}Step 3/3: Deploying to Cloud Run...${NC}"

gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --image="$IMAGE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --min-instances="$MIN_INSTANCES" \
    --max-instances="$MAX_INSTANCES" \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --no-allow-unauthenticated \
    --set-env-vars="$ENV_VARS,HYPERLIQUID_TESTNET=true" \
    --timeout=3600 \
    --concurrency=1

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service URL:"
gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)'
echo ""
echo "To view logs:"
echo "  gcloud logs tail --project=$PROJECT_ID --service=$SERVICE_NAME"
echo ""
echo "To update environment variables:"
echo "  gcloud run services update $SERVICE_NAME --project=$PROJECT_ID --region=$REGION --update-env-vars KEY=VALUE"
echo ""
