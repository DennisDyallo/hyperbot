# GCP Secrets & Cloud Logging Guide

This guide explains how Hyperbot uses GCP Secret Manager and cloud-native logging for production deployments.

---

## 🔐 GCP Secret Manager

### Why Use Secret Manager?

Instead of storing sensitive credentials in environment variables or `.env` files, GCP Secret Manager provides:

- ✅ **Encryption at rest** - Secrets are encrypted
- ✅ **Access control** - IAM-based permissions
- ✅ **Audit logging** - Track secret access
- ✅ **Versioning** - Rotate secrets safely
- ✅ **No plaintext files** - Never commit secrets to git

---

## 📝 Current Logging Setup

### Local Development (Your Machine)
```
✅ Logs to: stdout (terminal) + file (logs/hyperbot.log)
✅ Format: Colorized, human-readable
✅ Rotation: 100MB, 30 days retention
```

### Cloud Production (GCP Cloud Run)
```
✅ Logs to: stdout ONLY
✅ Format: Plain text (no colors, better for log aggregation)
✅ Captured by: GCP Cloud Logging automatically
✅ Queryable in: GCP Console Logs Explorer
```

**Key Difference:** In cloud, file logging is disabled because:
1. Containers are ephemeral (logs would be lost on restart)
2. Cloud platforms capture stdout automatically
3. No need for log rotation (handled by cloud)

---

## 🚀 Setup Instructions

### Step 1: Configure Secrets Locally

```bash
# Create .env from example
cp .env.example .env

# Edit .env and add your real credentials
nano .env
```

Required secrets:
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `TELEGRAM_AUTHORIZED_USERS` - Your Telegram user IDs
- `HYPERLIQUID_SECRET_KEY` - Your private key
- `HYPERLIQUID_WALLET_ADDRESS` - Your wallet address

---

### Step 2: Upload Secrets to GCP

```bash
# Run the setup script
./scripts/setup-gcp-secrets.sh
```

This script will:
1. ✅ Enable Secret Manager API
2. ✅ Create secrets from your `.env` file
3. ✅ Set IAM permissions for Cloud Run service account
4. ✅ Skip any unset or placeholder values

**Output:**
```
🔐 Setting up GCP Secret Manager for Hyperbot

Creating secrets from .env file...

✨ Creating new secret: telegram-bot-token
✨ Creating new secret: hyperliquid-secret-key
✅ Secrets created successfully!
```

---

### Step 3: Deploy to Cloud Run

```bash
# Deploy (will automatically use secrets if available)
./scripts/deploy-gcp-cloudrun.sh
```

The deployment script automatically:
- ✅ Checks if secrets exist in GCP
- ✅ Uses Secret Manager if available
- ✅ Falls back to .env variables if not

---

## 🔍 How It Works

### Code Flow

1. **Settings Module** (`src/config/settings.py`)
   ```python
   # Automatically tries Secret Manager in cloud
   TELEGRAM_BOT_TOKEN = _get_config_value("TELEGRAM_BOT_TOKEN")
   ```

2. **Secret Loader** (`src/config/secrets.py`)
   ```python
   # Detects cloud environment
   if os.getenv("K_SERVICE"):  # Cloud Run
       value = get_secret("telegram-bot-token")
   else:  # Local
       value = os.getenv("TELEGRAM_BOT_TOKEN")
   ```

3. **Logger** (`src/config/logger.py`)
   ```python
   # Cloud: stdout only, no colors
   # Local: stdout + file, with colors
   if settings.is_cloud_run():
       logger.add(sys.stdout, colorize=False)
   ```

---

## 📊 Viewing Logs in GCP

### Option 1: Cloud Console

1. Go to: https://console.cloud.google.com/logs
2. Select your project
3. Filter by:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="hyperbot"
   ```

### Option 2: gcloud CLI

```bash
# Tail logs in real-time
gcloud logs tail \
  --project=YOUR_PROJECT_ID \
  --filter='resource.type=cloud_run_revision AND resource.labels.service_name=hyperbot'

# Search for errors
gcloud logs read \
  --project=YOUR_PROJECT_ID \
  --filter='resource.type=cloud_run_revision AND severity>=ERROR' \
  --limit=50

# Export logs to file
gcloud logs read \
  --project=YOUR_PROJECT_ID \
  --filter='resource.labels.service_name=hyperbot' \
  --format=json > hyperbot-logs.json
```

---

## 🔧 Managing Secrets

### List Secrets

```bash
gcloud secrets list --project=YOUR_PROJECT_ID
```

### View Secret Value

```bash
# View latest version
gcloud secrets versions access latest \
  --secret="telegram-bot-token" \
  --project=YOUR_PROJECT_ID

# View specific version
gcloud secrets versions access 2 \
  --secret="telegram-bot-token"
```

### Update Secret

```bash
# Update with new value
echo -n "new_secret_value" | gcloud secrets versions add telegram-bot-token --data-file=-

# Or update from .env
./scripts/setup-gcp-secrets.sh  # Re-run to update all
```

### Rotate Secrets

```bash
# 1. Add new version
echo -n "new_token" | gcloud secrets versions add telegram-bot-token --data-file=-

# 2. Redeploy (will use latest version)
./scripts/deploy-gcp-cloudrun.sh

# 3. Disable old version (after confirming new one works)
gcloud secrets versions disable 1 --secret="telegram-bot-token"
```

---

## 🐛 Troubleshooting

### Secret Not Found Error

```
Failed to load secret telegram-bot-token from GCP
```

**Solution:**
```bash
# Check if secret exists
gcloud secrets describe telegram-bot-token --project=YOUR_PROJECT_ID

# If not, create it
./scripts/setup-gcp-secrets.sh
```

### Permission Denied Error

```
ERROR: (gcloud.secrets.versions.access) PERMISSION_DENIED
```

**Solution:**
```bash
# Grant access to service account
gcloud secrets add-iam-policy-binding telegram-bot-token \
  --member="serviceAccount:YOUR_PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Logs Not Appearing

```
No logs in GCP Console
```

**Solution:**
1. Check service is running: `gcloud run services describe hyperbot`
2. Verify stdout logging is enabled (check `src/config/logger.py`)
3. Wait 1-2 minutes for logs to propagate
4. Check log filters in Console

---

## 💡 Best Practices

### Local Development

```bash
# Use .env file (never commit!)
cp .env.example .env
# Edit .env with real values

# Logs appear in:
# - Terminal (stdout, colorized)
# - logs/hyperbot.log (plain text, rotated)
```

### Production (Cloud Run)

```bash
# Use Secret Manager
./scripts/setup-gcp-secrets.sh

# Logs appear in:
# - GCP Cloud Logging (stdout captured automatically)
# - Queryable via gcloud or Console
# - No local files (ephemeral containers)
```

### Security Checklist

- [ ] Never commit `.env` to git (already in `.gitignore`)
- [ ] Use Secret Manager for production
- [ ] Rotate secrets regularly (monthly recommended)
- [ ] Grant minimal IAM permissions
- [ ] Enable audit logging for secret access
- [ ] Use `HYPERLIQUID_TESTNET=true` until fully tested

---

## 📈 Cost Estimate

### Secret Manager

- **Storage:** $0.06 per secret per month
- **Access:** $0.03 per 10,000 accesses
- **Total for Hyperbot:** ~$0.30/month (5 secrets)

### Cloud Logging

- **First 50 GB/month:** Free
- **Additional:** $0.50 per GB
- **Hyperbot estimate:** < 1 GB/month = **Free**

**Combined:** ~$0.30/month for secrets + logging

---

## 🔗 Additional Resources

- [GCP Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Cloud Logging Docs](https://cloud.google.com/logging/docs)
- [Best Practices for Secrets](https://cloud.google.com/secret-manager/docs/best-practices)

---

**Next Steps:**
1. ✅ Setup secrets: `./scripts/setup-gcp-secrets.sh`
2. ✅ Deploy: `./scripts/deploy-gcp-cloudrun.sh`
3. ✅ Monitor logs in GCP Console
4. ✅ Rotate secrets monthly
