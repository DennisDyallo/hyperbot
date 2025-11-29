# 🚀 Quick Start: GitHub Actions Deployment

**Project:** Hyperbot
**Project ID:** `hyperbot-479700`
**Region:** `us-central1`

---

## ⚡ One-Command Setup

```bash
./setup-github-actions.sh
```

This automated script will:
1. ✅ Create service account `github-actions@hyperbot-479700.iam.gserviceaccount.com`
2. ✅ Grant all required IAM permissions
3. ✅ Enable GCP APIs (Cloud Run, Container Registry, etc.)
4. ✅ Create service account key file
5. ✅ Upload secrets to GCP Secret Manager (if .env exists)
6. ✅ Show instructions for GitHub secrets

---

## 🔐 Add GitHub Secrets

After running the setup script, add these to GitHub:

**Go to:** https://github.com/DennisDyallo/hyperbot/settings/secrets/actions

### Secret 1: LIGHTBRINGER_HYPERBOT_GCP_SA_KEY
```bash
# Copy entire file contents
cat lb-hyperbot-github-actions-key.json
```

### Secret 2: LIGHTBRINGER_HYPERBOT_GCP_PROJECT_ID
```
hyperbot-479700
```

---

## 🧹 Clean Up

```bash
# After adding secrets to GitHub, delete the local key
rm lb-hyperbot-github-actions-key.json
```

---

## 🚀 Deploy

```bash
git add .
git commit -m "Setup GitHub Actions deployment"
git push origin main
```

**Monitor:** https://github.com/DennisDyallo/hyperbot/actions

---

## 📋 Manual Commands (if needed)

### Create Service Account
```bash
gcloud iam service-accounts create lb-hyperbot-github-actions \
  --project=hyperbot-479700 \
  --description="Service account for GitHub Actions CI/CD" \
  --display-name="Lightbringer Hyperbot GitHub Actions"
```

### Grant Permissions
```bash
PROJECT_ID="hyperbot-479700"
SA_EMAIL="lb-hyperbot-github-actions@hyperbot-479700.iam.gserviceaccount.com"

# Cloud Run Admin
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Storage Admin
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

# Service Account User
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Secret Manager Accessor
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

### Enable APIs
```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project=hyperbot-479700
```

### Create Service Account Key
```bash
gcloud iam service-accounts keys create lb-hyperbot-github-actions-key.json \
  --iam-account=lb-hyperbot-github-actions@hyperbot-479700.iam.gserviceaccount.com \
  --project=hyperbot-479700
```

---

## 🔍 Verify Deployment

### Check Cloud Run Service
```bash
gcloud run services list --project=hyperbot-479700 --region=us-central1
```

### View Logs
```bash
gcloud logs tail \
  --project=hyperbot-479700 \
  --filter='resource.type=cloud_run_revision AND resource.labels.service_name=hyperbot'
```

### Get Service URL
```bash
gcloud run services describe hyperbot \
  --project=hyperbot-479700 \
  --region=us-central1 \
  --format='value(status.url)'
```

---

## 💰 Cost

- **GitHub Actions:** Free (under 2,000 min/month)
- **Cloud Run:** ~$10-15/month (always-on instance)
- **Container Registry:** ~$0.26/GB/month
- **Secret Manager:** ~$0.30/month

**Total:** ~$10-16/month

---

## 🎯 Workflow Behavior

**Automatic deployment on:**
- Push to `main` branch

**Manual deployment:**
- GitHub Actions → Deploy to GCP Cloud Run → Run workflow

**Each deployment:**
1. Builds Docker image
2. Pushes to `gcr.io/hyperbot-479700/hyperbot`
3. Deploys to Cloud Run in `us-central1`
4. Uses secrets from GCP Secret Manager

---

## 📚 Documentation

- Full guide: `docs/GITHUB_ACTIONS_SETUP.md`
- Workflow file: `.github/workflows/deploy-gcp.yml`
- Deploy script: `scripts/deploy-gcp-cloudrun.sh`
- Secrets setup: `scripts/setup-gcp-secrets.sh`

---

**Questions?** Check the troubleshooting section in `docs/GITHUB_ACTIONS_SETUP.md`
