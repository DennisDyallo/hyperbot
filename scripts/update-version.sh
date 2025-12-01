#!/usr/bin/env bash
#
# Update version in settings.py with git commit hash
# This script is called by pre-commit hook
#

set -e

# Get the short commit hash (7 characters)
COMMIT_HASH=$(git rev-parse --short=7 HEAD 2>/dev/null || echo "0000000")

# Base version
BASE_VERSION="0.1.0"

# Combined version
NEW_VERSION="${BASE_VERSION}+${COMMIT_HASH}"

# File to update
SETTINGS_FILE="src/config/settings.py"

# Check if the file exists
if [ ! -f "$SETTINGS_FILE" ]; then
    echo "Error: $SETTINGS_FILE not found"
    exit 1
fi

# Update the VERSION line using sed
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/VERSION: str = \".*\"/VERSION: str = \"$NEW_VERSION\"/" "$SETTINGS_FILE"
else
    # Linux
    sed -i "s/VERSION: str = \".*\"/VERSION: str = \"$NEW_VERSION\"/" "$SETTINGS_FILE"
fi

echo "✅ Updated version to: $NEW_VERSION"

# Add the updated file to the commit
git add "$SETTINGS_FILE"
