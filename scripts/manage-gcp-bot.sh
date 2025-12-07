#!/usr/bin/env bash
#
# GCP Cloud Run Bot Management Script
# Usage: ./scripts/manage-gcp-bot.sh [start|stop|status]
#

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-hyperbot-479700}"  # Default to your project, can override with env var
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${GCP_SERVICE_NAME:-hyperbot}"
IMAGE_NAME="us-docker.pkg.dev/${PROJECT_ID}/hyperbot/hyperbot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_gcloud_auth() {
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
        error "Not authenticated to gcloud. Run 'gcloud auth login' first."
    fi
}

check_project() {
    info "Using GCP project: $PROJECT_ID"

    gcloud config set project "$PROJECT_ID" 2>/dev/null || \
        error "Failed to set project to $PROJECT_ID"
}

get_service_status() {
    gcloud run services describe "$SERVICE_NAME" \
        --region "$REGION" \
        --format="value(status.conditions[0].status)" 2>/dev/null || echo "NOT_FOUND"
}

get_service_url() {
    gcloud run services describe "$SERVICE_NAME" \
        --region "$REGION" \
        --format="value(status.url)" 2>/dev/null || echo ""
}

start_bot() {
    info "Starting GCP Cloud Run bot..."

    local status
    status=$(get_service_status)

    if [ "$status" = "True" ]; then
        success "Bot is already running"
        local url
        url=$(get_service_url)
        info "Service URL: $url"
        return 0
    fi

    # Check if image exists
    info "Deploying bot from latest image..."

    # Deploy service with latest image
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME:latest" \
        --platform managed \
        --region "$REGION" \
        --min-instances 1 \
        --max-instances 1 \
        --memory 512Mi \
        --cpu 1 \
        --timeout 300 \
        --no-cpu-throttling \
        --no-allow-unauthenticated \
        --set-env-vars ENVIRONMENT=production \
        --set-env-vars HYPERLIQUID_TESTNET=false \
        --set-env-vars GCP_PROJECT="$PROJECT_ID" \
        --set-secrets=TELEGRAM_BOT_TOKEN=lb-hyperbot-telegram-bot-token:latest \
        --set-secrets=TELEGRAM_AUTHORIZED_USERS=lb-hyperbot-telegram-authorized-users:latest \
        --set-secrets=HYPERLIQUID_SECRET_KEY=lb-hyperbot-hyperliquid-secret-key:latest \
        --set-secrets=HYPERLIQUID_WALLET_ADDRESS=lb-hyperbot-hyperliquid-wallet-address:latest \
        --quiet

    success "Bot deployed and started successfully"

    local url
    url=$(get_service_url)
    info "Service URL: $url"
}

stop_bot() {
    info "Stopping GCP Cloud Run bot..."

    local status
    status=$(get_service_status)

    if [ "$status" = "NOT_FOUND" ]; then
        success "Bot is already stopped"
        return 0
    fi

    # Delete the service to stop it completely
    gcloud run services delete "$SERVICE_NAME" \
        --region "$REGION" \
        --quiet

    success "Bot stopped (service deleted)"
    info "Service will not consume any resources"
    info "Use 'start' to redeploy and restart the bot"
}

delete_bot() {
    # Alias for stop_bot since they do the same thing now
    stop_bot
}

show_status() {
    info "Checking bot status..."

    local status
    status=$(get_service_status)

    if [ "$status" = "NOT_FOUND" ]; then
        echo "Status: NOT DEPLOYED"
        echo "Region: $REGION"
        info "Deploy the service using the deploy-gcp.yml workflow first"
        return 1
    fi

    echo "Status: $([ "$status" = "True" ] && echo "RUNNING" || echo "STOPPED")"
    echo "Service: $SERVICE_NAME"
    echo "Region: $REGION"
    echo "Project: $PROJECT_ID"

    # Get detailed info
    gcloud run services describe "$SERVICE_NAME" \
        --region "$REGION" \
        --format="table(
            status.url,
            spec.template.spec.containers[0].image.split('/').slice(-1:),
            metadata.annotations['run.googleapis.com/launched'],
            spec.template.spec.containers[0].resources.limits.memory,
            spec.template.spec.containers[0].resources.limits.cpu,
            spec.template.metadata.annotations['autoscaling.knative.dev/minScale'],
            spec.template.metadata.annotations['autoscaling.knative.dev/maxScale']
        )"

    # Show recent logs (last 10 lines)
    echo ""
    info "Recent logs (last 10 lines):"
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
        --limit=10 \
        --format="table(timestamp,severity,textPayload)" \
        --project "$PROJECT_ID" 2>/dev/null || echo "No logs available"
}

# Main script
main() {
    local command="${1:-}"

    if [ -z "$command" ]; then
        echo "Usage: $0 [start|stop|status]"
        echo ""
        echo "Commands:"
        echo "  start   - Deploy and start the bot from latest image"
        echo "  stop    - Stop the bot (deletes service, no cost)"
        echo "  status  - Show current bot status and logs"
        echo ""
        echo "Environment variables (optional):"
        echo "  GCP_PROJECT_ID    - GCP project ID (default: hyperbot-479700)"
        echo "  GCP_REGION        - GCP region (default: us-central1)"
        echo "  GCP_SERVICE_NAME  - Service name (default: hyperbot)"
        echo ""
        echo "Note: 'start' requires that an image exists in Artifact Registry."
        echo "      Use the deploy-gcp.yml workflow to build and push a new image."
        exit 1
    fi

    check_gcloud_auth
    check_project

    case "$command" in
        start)
            start_bot
            ;;
        stop)
            stop_bot
            ;;
        delete)
            delete_bot
            ;;
        status)
            show_status
            ;;
        *)
            error "Unknown command: $command. Use start, stop, or status."
            ;;
    esac
}

main "$@"
