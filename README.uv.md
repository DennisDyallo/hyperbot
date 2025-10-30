# Using uv with Hyperbot

Hyperbot uses [uv](https://github.com/astral-sh/uv) - a fast, modern Python package manager.

## Why uv?

- ⚡ **10-100x faster** than pip
- 🔒 **Lockfile** (uv.lock) ensures reproducible installs
- 🎯 **Better dependency resolution**
- 🔄 **Automatic virtual environment** management

## Quick Start

### Install Dependencies

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Install with dev dependencies
uv sync --extra dev
```

### Run the Server

```bash
# Using uv run (automatically uses .venv)
uv run python run.py

# Or activate the virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
python run.py
```

### Common Commands

```bash
# Add a new dependency
uv add requests

# Add a dev dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade

# Run a script
uv run python script.py

# Run tests
uv run pytest
```

## Files

- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Lockfile (like package-lock.json) - **commit this!**
- `.venv/` - Virtual environment (gitignored)

## Migrating from pip

If you have `requirements.txt`:

```bash
# uv can read requirements.txt
uv pip compile requirements.txt -o requirements.lock

# Or convert to pyproject.toml
# (we've already done this!)
```

## More Info

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv vs pip Comparison](https://docs.astral.sh/uv/pip/)
