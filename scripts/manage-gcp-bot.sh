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

    if [ "$status" = "NOT_FOUND" ]; then
        error "Service '$SERVICE_NAME' not found. Deploy it first using the deploy-gcp.yml workflow."
    fi

    if [ "$status" = "True" ]; then
        success "Bot is already running"
        local url
        url=$(get_service_url)
        info "Service URL: $url"
        return 0
    fi

    # Update service to ensure it's running with min instances = 1
    gcloud run services update "$SERVICE_NAME" \
        --region "$REGION" \
        --min-instances 1 \
        --max-instances 1 \
        --quiet

    success "Bot started successfully"

    # Wait for service to be ready
    info "Waiting for service to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        status=$(get_service_status)
        if [ "$status" = "True" ]; then
            success "Service is ready"
            local url
            url=$(get_service_url)
            info "Service URL: $url"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    error "Service did not become ready within 60 seconds"
}

stop_bot() {
    info "Stopping GCP Cloud Run bot..."

    local status
    status=$(get_service_status)

    if [ "$status" = "NOT_FOUND" ]; then
        error "Service '$SERVICE_NAME' not found in region $REGION"
    fi

    # Update service to scale to zero
    gcloud run services update "$SERVICE_NAME" \
        --region "$REGION" \
        --min-instances 0 \
        --max-instances 1 \
        --no-cpu-throttling \
        --quiet

    success "Bot stopped (scaled to zero)"
    info "Service still exists but will not consume resources"
    info "Use 'start' to scale back up, or delete the service entirely if no longer needed"
}

delete_bot() {
    info "Deleting GCP Cloud Run service..."

    local status
    status=$(get_service_status)

    if [ "$status" = "NOT_FOUND" ]; then
        success "Service already deleted"
        return 0
    fi

    gcloud run services delete "$SERVICE_NAME" \
        --region "$REGION" \
        --quiet

    success "Service deleted successfully"
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
        echo "Usage: $0 [start|stop|delete|status]"
        echo ""
        echo "Commands:"
        echo "  start   - Start the bot (scale to min 1 instance)"
        echo "  stop    - Stop the bot (scale to 0 instances)"
        echo "  delete  - Delete the service entirely"
        echo "  status  - Show current bot status and logs"
        echo ""
        echo "Environment variables (optional):"
        echo "  GCP_PROJECT_ID    - GCP project ID (default: hyperbot-479700)"
        echo "  GCP_REGION        - GCP region (default: us-central1)"
        echo "  GCP_SERVICE_NAME  - Service name (default: hyperbot)"
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
            error "Unknown command: $command. Use start, stop, delete, or status."
            ;;
    esac
}

main "$@"
