# GCP Bot Management

## Quick Start

### Local Usage

```bash
# No setup needed! Project ID is embedded (hyperbot-479700)

# Check bot status
./scripts/manage-gcp-bot.sh status

# Start the bot (scale to 1 instance)
./scripts/manage-gcp-bot.sh start

# Stop the bot (scale to 0, no cost)
./scripts/manage-gcp-bot.sh stop

# Delete the service entirely
./scripts/manage-gcp-bot.sh delete

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
   - **start** - Scale bot to 1 instance (will start consuming resources)
   - **stop** - Scale bot to 0 instances (stops resource consumption but keeps service)
   - **delete** - Delete the service entirely (requires redeployment to restore)

## Commands

### `start`
- Scales the service to min=1, max=1 instances
- Bot will start running and consuming resources
- Waits for service to be ready (up to 60 seconds)
- Shows service URL when ready

### `stop`
- Scales the service to min=0, max=1 instances
- Bot stops running immediately
- **No cost incurred** while stopped
- Service configuration is preserved
- Use `start` to quickly resume

### `delete`
- **Permanently deletes** the Cloud Run service
- All configuration is lost
- Must redeploy using `deploy-gcp.yml` workflow to restore
- Use this when you're done with the bot entirely

### `status`
- Shows current running state (RUNNING/STOPPED/NOT DEPLOYED)
- Displays service configuration (memory, CPU, scaling)
- Shows last 10 log entries
- No changes made to the service

## Cost Management

**Key Insight**: Use `stop` instead of `delete` to save costs while preserving the service.

| Action | Cost | Recovery Time | Use When |
|--------|------|---------------|----------|
| `stop` | $0/month | ~5 seconds | Taking a break, testing, overnight |
| `delete` | $0/month | ~2-3 minutes | Done with bot permanently |
| Keep running | ~$5-10/month* | N/A | Active trading |

*Estimated cost with min-instances=1, 512Mi memory, 1 CPU, minimal traffic

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
# Morning: Start bot
./scripts/manage-gcp-bot.sh start

# Evening: Stop bot (save costs overnight)
./scripts/manage-gcp-bot.sh stop
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
Deploy the service first:
```bash
# Via GitHub Actions: Trigger "Deploy to GCP Cloud Run" workflow
# Or push to main branch to auto-deploy
```

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

1. **Use `stop` for short breaks** - Preserves configuration, instant restart
2. **Use `status` frequently** - Check health without side effects
3. **Use `delete` sparingly** - Only when completely done with the bot
4. **GitHub Actions for remote management** - Control from anywhere without local gcloud setup
5. **Set min-instances=0 for development** - Only pay when actively using
