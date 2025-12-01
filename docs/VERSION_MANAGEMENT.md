# Version Management

## Overview

The bot's version is automatically updated with the git commit hash via a pre-commit hook, providing traceability for deployed versions.

## Format

```
{BASE_VERSION}+{COMMIT_HASH}
```

Example: `0.1.0+af20b04`

## How It Works

A pre-commit hook automatically updates the version before each commit:

1. **Pre-commit Hook**: `scripts/update-version.sh` runs before every commit
2. **Version Update**: The script updates `VERSION` in `src/config/settings.py`
3. **Auto-commit**: The updated file is automatically added to the commit
4. **Result**: Every commit contains the version with its own commit hash

## Setup

The pre-commit hook is already configured in `.pre-commit-config.yaml`:

```yaml
- id: update-version
  name: Update version with commit hash
  entry: ./scripts/update-version.sh
  language: system
  stages: [commit]
  pass_filenames: false
  always_run: true
```

To ensure pre-commit hooks are installed:

```bash
uv run pre-commit install
```

## Benefits

- ✅ **Automatic**: Runs on every commit, no manual updates needed
- ✅ **Traceable**: Each deployment shows exactly which commit it's running
- ✅ **Simple**: Static string in settings.py, no runtime git commands
- ✅ **Server-friendly**: Works in Docker, no .git directory needed at runtime
- ✅ **No Performance Impact**: Version is a simple string constant

## Viewing the Version

The version is displayed in multiple places:

1. **Telegram Bot Main Menu**: Shows next to environment (e.g., `Environment: 🚀 Mainnet | Version: 0.1.0+af20b04`)
2. **Telegram /start Command**: Displays in the welcome message
3. **Telegram /status Command**: Shows in bot status information
4. **Code**: Available as `settings.VERSION`

## Updating the Base Version

To update the base version (e.g., when releasing a new version):

1. Edit `scripts/update-version.sh`
2. Update the `BASE_VERSION` variable:
   ```bash
   BASE_VERSION="0.2.0"  # Change this
   ```
3. Commit your changes - the hook will update it with the commit hash automatically

## Manual Update

To manually update the version without committing:

```bash
./scripts/update-version.sh
```

## Docker Deployments

The version is baked into the code at commit time:

1. ✅ Commit your code → pre-commit hook updates version
2. ✅ Build Docker image → version is in the code
3. ✅ Deploy → no .git directory needed
4. ✅ Bot shows exact commit version

## Implementation Details

### Files

- **Hook Script**: `scripts/update-version.sh` - Updates version string
- **Pre-commit Config**: `.pre-commit-config.yaml` - Runs the hook
- **Settings**: `src/config/settings.py` - Contains the VERSION constant
- **Display**: Used in `src/bot/handlers/menus.py` and `src/bot/handlers/commands.py`

### How the Hook Works

```bash
# Get current commit hash
COMMIT_HASH=$(git rev-parse --short=7 HEAD)

# Update settings.py
sed -i "s/VERSION: str = \".*\"/VERSION: str = \"$NEW_VERSION\"/" src/config/settings.py

# Add to commit
git add src/config/settings.py
```
