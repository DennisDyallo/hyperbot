#!/bin/bash
# Quick setup script for GitHub Actions deployment
# Project: Hyperbot (hyperbot-479700)

set -e

PROJECT_ID="hyperbot-479700"
SERVICE_ACCOUNT_NAME="lightbringer-hyperbot-github-actions"
SERVICE_ACCOUNT_EMAIL="lightbringer-hyperbot-github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="lightbringer-hyperbot-github-actions-key.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GitHub Actions Setup for Hyperbot${NC}"
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Create service account
echo -e "${YELLOW}Step 1/6: Creating service account...${NC}"
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_EMAIL} --project=${PROJECT_ID} &> /dev/null; then
    echo -e "${GREEN}✓ Service account already exists${NC}"
else
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --project=${PROJECT_ID} \
        --description="Service account for GitHub Actions CI/CD" \
        --display-name="GitHub Actions"
    echo -e "${GREEN}✓ Service account created${NC}"
fi
echo ""

# Step 2: Grant permissions
echo -e "${YELLOW}Step 2/6: Granting IAM permissions...${NC}"

echo "  → Cloud Run Admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/run.admin" \
    --quiet

echo "  → Storage Admin"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin" \
    --quiet

echo "  → Service Account User"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

echo "  → Secret Manager Secret Accessor"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo -e "${GREEN}✓ Permissions granted${NC}"
echo ""

# Step 3: Enable required APIs
echo -e "${YELLOW}Step 3/6: Enabling required GCP APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --project=${PROJECT_ID} \
    --quiet

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 4: Create service account key
echo -e "${YELLOW}Step 4/6: Creating service account key...${NC}"
if [ -f "${KEY_FILE}" ]; then
    echo -e "${RED}⚠️  ${KEY_FILE} already exists. Skipping key creation.${NC}"
    echo -e "${YELLOW}   Delete it first if you want to create a new one.${NC}"
else
    gcloud iam service-accounts keys create ${KEY_FILE} \
        --iam-account=${SERVICE_ACCOUNT_EMAIL} \
        --project=${PROJECT_ID}
    echo -e "${GREEN}✓ Service account key created: ${KEY_FILE}${NC}"
fi
echo ""

# Step 5: Instructions for GitHub secrets
echo -e "${YELLOW}Step 5/6: Configure GitHub Secrets${NC}"
echo ""
echo -e "${BLUE}Go to your GitHub repository:${NC}"
echo "  https://github.com/DennisDyallo/hyperbot/settings/secrets/actions"
echo ""
echo -e "${BLUE}Add these two secrets:${NC}"
echo ""
echo -e "${GREEN}1. LIGHTBRINGER_HYPERBOT_GCP_SA_KEY${NC}"
echo "   Value: Copy the ENTIRE contents of ${KEY_FILE}"
echo "   Command to view:"
echo -e "   ${YELLOW}cat ${KEY_FILE}${NC}"
echo ""
echo -e "${GREEN}2. LIGHTBRINGER_HYPERBOT_GCP_PROJECT_ID${NC}"
echo "   Value: ${PROJECT_ID}"
echo ""

# Step 6: Upload secrets to GCP (if .env exists)
echo -e "${YELLOW}Step 6/6: Upload secrets to GCP Secret Manager${NC}"
if [ -f ".env" ]; then
    echo "Found .env file. Uploading secrets..."
    ./scripts/setup-gcp-secrets.sh
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Create .env from .env.example and run:"
    echo -e "  ${YELLOW}./scripts/setup-gcp-secrets.sh${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Add GitHub secrets (see above)"
echo "2. Delete service account key: ${YELLOW}rm ${KEY_FILE}${NC}"
echo "3. Push to main branch to trigger deployment"
echo ""
echo -e "${BLUE}Test deployment:${NC}"
echo "  git add ."
echo "  git commit -m \"Add GitHub Actions deployment\""
echo "  git push origin main"
echo ""
echo -e "${BLUE}Monitor deployment:${NC}"
echo "  https://github.com/DennisDyallo/hyperbot/actions"
echo ""
