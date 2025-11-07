#!/bin/bash
# Auto-fix linting issues in Hyperbot

set -e

echo "🔧 Auto-fixing linting issues..."
echo ""

echo "1️⃣  Running Ruff auto-fix..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ruff check --fix src/ tests/
echo ""

echo "2️⃣  Running Ruff formatter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ruff format src/ tests/
echo ""

echo "✅ Auto-fix complete!"
echo ""
echo "Review changes with: git diff"
echo "Run tests with: uv run pytest tests/"
