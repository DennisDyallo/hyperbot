# Docker & Cloud Deployment Guide

## 🐳 Docker Setup Overview

Your Hyperbot is now containerized and ready for cloud deployment. Here's what was configured:

### Files Created
- `Dockerfile` - Multi-stage production build
- `.dockerignore` - Excludes unnecessary files from build
- `docker-compose.yml` - Local development environment
- `scripts/deploy-gcp-cloudrun.sh` - GCP deployment script
- `scripts/test-docker-local.sh` - Local testing script

---

## 📋 Pre-Deployment Checklist

### 1. Configure Environment Variables

```bash
# Copy example and edit
cp .env.example .env

# Required variables:
TELEGRAM_BOT_TOKEN=         # Get from @BotFather
TELEGRAM_AUTHORIZED_USERS=  # Your Telegram user IDs (comma-separated)
HYPERLIQUID_SECRET_KEY=     # Your Hyperliquid private key
HYPERLIQUID_WALLET_ADDRESS= # Your wallet address
HYPERLIQUID_TESTNET=true    # ALWAYS true for safety
```

### 2. Test Locally First

```bash
# Test with Docker Compose
docker-compose up hyperbot

# Or test with script
./scripts/test-docker-local.sh
```

### 3. Verify Bot Functionality
- Send `/start` to your bot
- Test basic commands
- Check logs in `./logs/`

---

## ☁️ Cloud Deployment Options

### Option 1: GCP Cloud Run (Recommended) - $10-15/month

**Why Cloud Run?**
- ✅ Serverless - no server management
- ✅ Automatic scaling and health checks
- ✅ Built-in logging and monitoring
- ✅ Cheapest for Telegram bots
- ✅ Free tier: 2M requests/month

**Setup Steps:**

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Initialize GCP**
   ```bash
   gcloud init
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable Required APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

4. **Configure Authentication**
   ```bash
   gcloud auth configure-docker
   ```

5. **Deploy**
   ```bash
   # Edit the script first to set your PROJECT_ID
   nano scripts/deploy-gcp-cloudrun.sh

   # Deploy
   ./scripts/deploy-gcp-cloudrun.sh
   ```

**Cost Estimate:**
- CPU: 1 vCPU × 730 hours = ~$6/month
- Memory: 512MB × 730 hours = ~$3/month
- Requests: Free tier covers bot polling
- **Total: ~$9/month**

---

### Option 2: GCP Compute Engine (Free Tier) - $0-7/month

**Best for:** More control, potential free tier

**Setup Steps:**

1. **Create VM Instance**
   ```bash
   gcloud compute instances create hyperbot-vm \
     --machine-type=e2-micro \
     --zone=us-west1-b \
     --image-family=cos-stable \
     --image-project=cos-cloud \
     --boot-disk-size=30GB
   ```

2. **SSH and Install Docker**
   ```bash
   gcloud compute ssh hyperbot-vm

   # Install Docker
   sudo yum install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Copy .env to VM**
   ```bash
   # On your local machine
   gcloud compute scp .env hyperbot-vm:~/
   ```

4. **Build and Run**
   ```bash
   # On the VM
   git clone YOUR_REPO_URL
   cd hyperbot

   # Copy .env
   mv ~/.env .

   # Run with Docker Compose
   docker-compose up -d hyperbot
   ```

**Cost:** Free tier eligible (e2-micro in certain regions)

---

## 🔧 Docker Commands Reference

### Local Development

```bash
# Build image
docker build -t hyperbot .

# Run bot
docker run --rm --env-file .env hyperbot

# Run API server
docker run --rm --env-file .env -p 8000:8000 hyperbot python run.py

# Use Docker Compose
docker-compose up          # Start all services
docker-compose up -d       # Start in background
docker-compose logs -f     # View logs
docker-compose down        # Stop all services
```

### Production

```bash
# Build production image
docker build -t hyperbot:prod .

# Run with production settings
docker run -d \
  --name hyperbot \
  --restart unless-stopped \
  --env-file .env \
  -e ENVIRONMENT=production \
  -v $(pwd)/logs:/app/logs \
  hyperbot:prod
```

---

## 🚀 Multi-App Deployment (Bot + Open WebUI)

### Using Docker Compose

Edit `docker-compose.yml` to uncomment Open WebUI service, then:

```bash
docker-compose up -d
```

Access:
- **Hyperbot**: Running in background
- **Open WebUI**: http://localhost:8080

### Using GCP Cloud Run (Both Services)

```bash
# Deploy Hyperbot
gcloud run deploy hyperbot \
  --image gcr.io/PROJECT/hyperbot \
  --min-instances 1

# Deploy Open WebUI
gcloud run deploy openwebui \
  --image ghcr.io/open-webui/open-webui:main \
  --min-instances 0 \
  --memory 1Gi \
  --allow-unauthenticated
```

**Total Cost:** ~$10-20/month (Hyperbot always-on, Open WebUI scales to zero)

---

## 🐛 Troubleshooting

### Bot Not Starting

```bash
# Check logs
docker logs hyperbot

# Common issues:
# 1. Missing TELEGRAM_BOT_TOKEN
# 2. Invalid bot token
# 3. Network issues
```

### High Memory Usage

```bash
# Check container stats
docker stats hyperbot

# Restart if needed
docker restart hyperbot
```

---

## 💰 Cost Comparison Summary

| Provider | Service | Monthly Cost | Best For |
|----------|---------|--------------|----------|
| **GCP** | Cloud Run | **$9-15** | Simplest, serverless |
| **GCP** | Compute Engine | **$0-7** | Free tier, more control |
| **AWS** | Fargate | **$15-25** | AWS ecosystem |
| **Azure** | Container Instances | **$15-30** | Azure users |

**Recommendation:** Start with GCP Cloud Run

---

## 🎯 Next Steps

1. ✅ Test locally: `./scripts/test-docker-local.sh`
2. ✅ Choose cloud provider (GCP Cloud Run recommended)
3. ✅ Deploy: `./scripts/deploy-gcp-cloudrun.sh`
4. ✅ Monitor for 24 hours
5. ✅ (Optional) Add Open WebUI as second service

---

See also: [DEPLOYMENT.md](./DEPLOYMENT.md) for systemd local deployment.
