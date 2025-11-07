#!/bin/bash
# Check for unused code (dead code) in the project

echo "🔍 Detecting unused code with Vulture..."
echo ""
echo "Note: Some findings may be false positives:"
echo "  - API route functions (used by FastAPI routers)"
echo "  - Pydantic model fields (used for serialization)"
echo "  - Test fixtures (used by pytest)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run with 70% confidence (good balance), using whitelist
vulture src/ .vulture_whitelist.py --min-confidence 70 --sort-by-size

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To exclude false positives, add them to .vulture_whitelist.py"
echo "To see more potential issues: vulture src/ --min-confidence 60"
echo "To see high-confidence only: vulture src/ --min-confidence 90"
