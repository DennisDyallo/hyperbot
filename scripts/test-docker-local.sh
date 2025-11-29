#!/bin/bash
# Test Docker build locally before cloud deployment
# Usage: ./scripts/test-docker-local.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧪 Testing Docker build locally...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your credentials${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t hyperbot:test .

echo -e "${GREEN}✅ Build successful!${NC}"
echo ""

# Test the bot
echo -e "${YELLOW}Starting Telegram bot in test mode...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

docker run --rm \
    --name hyperbot-test \
    --env-file .env \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/data:/app/data \
    hyperbot:test

echo ""
echo -e "${GREEN}✅ Test complete!${NC}"
