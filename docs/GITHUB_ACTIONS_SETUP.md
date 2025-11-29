# GitHub Actions CI/CD Setup for GCP Cloud Run

This guide will help you set up automated deployments to GCP Cloud Run on every commit to the `main` branch.

## 📋 Prerequisites

- GCP project with billing enabled
- GitHub repository with admin access
- Secrets already uploaded to GCP Secret Manager (run `./scripts/setup-gcp-secrets.sh` if not done)

---

## 🔐 Step 1: Create GCP Service Account

### 1.1 Create Service Account

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --project=${PROJECT_ID} \
  --description="Service account for GitHub Actions CI/CD" \
  --display-name="GitHub Actions"
```

### 1.2 Grant Required Permissions

```bash
# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant Storage Admin role (for pushing to Container Registry)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Grant Service Account User role (to deploy as a service account)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Grant Secret Manager Secret Accessor (to use secrets in Cloud Run)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 1.3 Create Service Account Key

```bash
# Create and download JSON key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# ⚠️ IMPORTANT: This file contains sensitive credentials!
# Do not commit this to git!
```

---

## 🔧 Step 2: Configure GitHub Secrets

### 2.1 Add Secrets to GitHub Repository

Go to your GitHub repository:
1. Navigate to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

Add the following secrets:

#### Required Secret: GCP_SA_KEY
- **Name:** `GCP_SA_KEY`
- **Value:** Contents of `github-actions-key.json` file
  ```bash
  # Copy the entire contents of the file
  cat github-actions-key.json
  ```

#### Required Secret: GCP_PROJECT_ID
- **Name:** `GCP_PROJECT_ID`
- **Value:** Your GCP project ID (e.g., `my-hyperbot-project`)

### 2.2 Delete Local Service Account Key

```bash
# After adding to GitHub, delete the local key for security
rm github-actions-key.json
```

---

## 📦 Step 3: Enable Required GCP APIs

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com --project=${PROJECT_ID}

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com --project=${PROJECT_ID}

# Enable Cloud Build API (for building images)
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}

# Enable Secret Manager API (if not already enabled)
gcloud services enable secretmanager.googleapis.com --project=${PROJECT_ID}
```

---

## 🚀 Step 4: Upload Secrets to GCP Secret Manager

If you haven't already uploaded your secrets:

```bash
# Make sure you have a .env file configured
cp .env.example .env
# Edit .env with your actual credentials

# Upload secrets to GCP
./scripts/setup-gcp-secrets.sh
```

This creates the following secrets in GCP:
- `telegram-bot-token`
- `telegram-authorized-users`
- `hyperliquid-secret-key`
- `hyperliquid-wallet-address`
- `api-key`

---

## ✅ Step 5: Test the Workflow

### 5.1 Push to Main Branch

```bash
git add .
git commit -m "Add GitHub Actions deployment workflow"
git push origin main
```

### 5.2 Monitor Deployment

1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see a workflow run named "Deploy to GCP Cloud Run"
4. Click on it to view logs

### 5.3 Manual Trigger (Optional)

You can also trigger deployments manually:
1. Go to **Actions** tab
2. Click **Deploy to GCP Cloud Run** workflow
3. Click **Run workflow** button
4. Select branch and click **Run workflow**

---

## 🔍 Step 6: Verify Deployment

### Check Cloud Run Service

```bash
# List Cloud Run services
gcloud run services list --project=${PROJECT_ID} --region=us-central1

# Get service URL
gcloud run services describe hyperbot \
  --project=${PROJECT_ID} \
  --region=us-central1 \
  --format='value(status.url)'
```

### View Logs

```bash
# Tail logs in real-time
gcloud logs tail \
  --project=${PROJECT_ID} \
  --filter='resource.type=cloud_run_revision AND resource.labels.service_name=hyperbot'

# Or view in GCP Console
# https://console.cloud.google.com/logs
```

---

## 🎯 Workflow Triggers

The workflow runs automatically on:
- ✅ **Push to `main` branch** - Automatic deployment
- ✅ **Manual trigger** - Via GitHub Actions UI

### Customizing Triggers

Edit `.github/workflows/deploy-gcp.yml` to change when deployments happen:

```yaml
# Deploy on multiple branches
on:
  push:
    branches:
      - main
      - production
      - staging

# Deploy on pull request merge
on:
  pull_request:
    types: [closed]
    branches:
      - main

# Deploy on tags
on:
  push:
    tags:
      - 'v*'
```

---

## 🔧 Troubleshooting

### Error: "Permission denied"

**Solution:** Ensure service account has all required roles:
```bash
# Re-grant permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Error: "Secret not found"

**Solution:** Upload secrets to GCP Secret Manager:
```bash
./scripts/setup-gcp-secrets.sh
```

### Error: "Image not found"

**Solution:** Ensure Container Registry is enabled:
```bash
gcloud services enable containerregistry.googleapis.com --project=${PROJECT_ID}
```

### Deployment Slow or Hanging

**Cause:** Docker build can be slow on GitHub Actions runners

**Solutions:**
1. Use Docker layer caching (add to workflow)
2. Pre-build and push base images
3. Consider using Google Cloud Build instead

---

## 💰 Cost Estimate

### GitHub Actions
- **Free tier:** 2,000 minutes/month for public repos
- **Private repos:** 2,000 minutes/month (Free plan), 3,000 minutes/month (Pro)
- **This workflow:** ~3-5 minutes per deployment

### GCP Cloud Run
- **Always-on instance:** ~$10-15/month (min-instances=1)
- **Container Registry storage:** ~$0.26/GB/month
- **Total:** ~$10-16/month

---

## 🔒 Security Best Practices

✅ **DO:**
- Store credentials in GitHub Secrets
- Use service accounts with minimal permissions
- Delete local service account keys after uploading
- Rotate service account keys regularly
- Use `HYPERLIQUID_TESTNET=true` until fully tested

❌ **DON'T:**
- Commit service account keys to git
- Give service accounts Owner/Editor roles
- Share `GCP_SA_KEY` value publicly
- Deploy to production without testing

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Container Registry Pricing](https://cloud.google.com/container-registry/pricing)

---

## 🎉 Next Steps

1. ✅ Service account created
2. ✅ GitHub secrets configured
3. ✅ GCP APIs enabled
4. ✅ Secrets uploaded to GCP
5. ✅ First deployment successful
6. 🔄 Monitor deployments in GitHub Actions
7. 📊 Check Cloud Run logs for issues
8. 🚀 Iterate and improve!

---

**Need help?** Check the logs in:
- GitHub Actions tab (build logs)
- GCP Cloud Logging (runtime logs)
