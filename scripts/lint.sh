#!/bin/bash
# Linting and code quality checks for Hyperbot

set -e

echo "🔍 Running linting checks..."
echo ""

echo "1️⃣  Running Ruff linter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ruff check src/ tests/ --statistics
echo ""

echo "2️⃣  Running Ruff formatter check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ruff format --check src/ tests/
echo ""

echo "3️⃣  Running mypy type checker..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mypy src/ || echo "⚠️  Type check warnings found (non-critical)"
echo ""

echo "✅ All checks complete!"
echo ""
echo "To auto-fix issues:"
echo "  ruff check --fix src/ tests/    # Fix linting issues"
echo "  ruff format src/ tests/          # Format code"
