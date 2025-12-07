# GCP Bot Management

## Quick Start

### Local Usage

```bash
# No setup needed! Project ID is embedded (hyperbot-479700)

# Check bot status
./scripts/manage-gcp-bot.sh status

# Start the bot (redeploys from latest image)
./scripts/manage-gcp-bot.sh start

# Stop the bot (deletes service, no cost)
./scripts/manage-gcp-bot.sh stop

# Override project ID if needed
export GCP_PROJECT_ID="different-project"
./scripts/manage-gcp-bot.sh status
```

### GitHub Actions Workflow Dispatch

1. Go to **Actions** tab in GitHub
2. Select **"Manage GCP Bot"** workflow
3. Click **"Run workflow"** button
4. Select action from dropdown:
   - **status** - Check current bot status and recent logs
   - **start** - Redeploy bot from latest image (will run with min-instances=1)
   - **stop** - Delete the service (stops bot, $0 cost)

## Commands

### `start`
- Redeploys the service from the latest image in Artifact Registry
- Sets min-instances=1, max-instances=1
- Bot will start running and actively polling Telegram
- **Note**: Requires that an image exists (push to main or run deploy-gcp.yml first)

### `stop`
- **Deletes the Cloud Run service entirely**
- Bot stops running immediately
- **No cost incurred** while stopped
- Use `start` to redeploy (takes ~30-60 seconds)

### `status`
- Shows current running state (RUNNING/STOPPED/NOT DEPLOYED)
- Displays service configuration (memory, CPU, scaling)
- Shows last 10 log entries
- No changes made to the service

## Cost Management

**Key Insight**: Use `stop` to completely remove the service when not trading.

| Action | Cost | Recovery Time | Use When |
|--------|------|---------------|----------|
| `stop` | $0/month | ~30-60 seconds | Not trading, overnight, testing |
| Keep running | ~$5-10/month* | N/A | Active trading hours |

*Estimated cost with min-instances=1, 512Mi memory, 1 CPU

**How it works:**
- `stop` deletes the service → $0 cost
- `start` redeploys from latest image → bot resumes in ~30-60 seconds
- Telegram bot requires min-instances=1 (needs to actively poll for messages)

## Prerequisites

### Local Usage
1. Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)
2. Authenticate: `gcloud auth login`
3. Run the script - project ID is already embedded!

### GitHub Actions
- No setup required! Uses existing secrets:
  - `LB_HYPERBOT_GCP_PROJECT_ID`
  - `LB_HYPERBOT_GCP_SA_KEY`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | `hyperbot-479700` | Your GCP project ID |
| `GCP_REGION` | `us-central1` | Cloud Run region |
| `GCP_SERVICE_NAME` | `hyperbot` | Service name |

**Note**: Project ID is hardcoded - it's not sensitive information.

## Examples

### Daily Development Workflow
```bash
# Morning: Start bot (redeploys from latest image)
./scripts/manage-gcp-bot.sh start

# Evening: Stop bot (delete service, save costs)
./scripts/manage-gcp-bot.sh stop
```

### After Code Changes
```bash
# 1. Push to main branch (triggers auto-deploy via GitHub Actions)
git push origin main

# 2. Wait for deployment (~2-3 minutes)

# 3. Bot is now running with new code
./scripts/manage-gcp-bot.sh status
```

### Check Logs Without Changing State
```bash
./scripts/manage-gcp-bot.sh status
```

### Emergency Stop
```bash
./scripts/manage-gcp-bot.sh stop
```

## Troubleshooting

### "Not authenticated to gcloud"
```bash
gcloud auth login
```

### "Service not found"
The bot is currently stopped. Start it with:
```bash
./scripts/manage-gcp-bot.sh start
```

This will redeploy from the latest image in Artifact Registry.

### Service won't start
Check logs in the `status` output or use:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hyperbot" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

## Related Workflows

- **Deploy to GCP Cloud Run** (`.github/workflows/deploy-gcp.yml`) - Initial deployment and updates
- **Manage GCP Bot** (`.github/workflows/manage-gcp-bot.yml`) - Start/stop/delete via GitHub UI

## Best Practices

1. **Use `stop` when not trading** - Completely free, fast restart
2. **Use `status` frequently** - Check health without side effects
3. **Push to main for code updates** - Auto-deploys via GitHub Actions
4. **GitHub Actions for remote management** - Control from anywhere without local gcloud setup
5. **Always keep min-instances=1 when running** - Bot needs to actively poll Telegram
