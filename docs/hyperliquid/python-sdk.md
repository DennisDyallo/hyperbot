# Hyperliquid Python SDK Documentation

## Overview

The Hyperliquid Python SDK is a Python library designed to facilitate trading on the Hyperliquid API. It offers straightforward installation and configuration for users seeking to integrate Hyperliquid trading capabilities into their Python applications.

## Installation

Install the SDK using pip:

```bash
pip install hyperliquid-python-sdk
```

## Configuration

### Basic Setup

To configure the SDK for use:

1. Set your wallet's public key as the `account_address` parameter in `examples/config.json`
2. Set your wallet's private key as the `secret_key` parameter in `examples/config.json`
3. Reference `examples/example_utils.py` for configuration loading examples

### API Wallet Setup (Optional)

For enhanced security, you can create a dedicated API wallet:

1. Generate a new API private key at https://app.hyperliquid.xyz/API
2. Set the API wallet's private key as `secret_key` in your configuration
3. **Important:** Still use your main wallet's public key as `account_address`

## Usage Examples

### Basic Query Example

```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
user_state = info.user_state("0xcd5051944f780a621ee62e39e493c489668acf4d")
print(user_state)
```

### Running Examples

After configuring your credentials:

```bash
cp examples/config.json.example examples/config.json
vim examples/config.json
python examples/basic_order.py
```

For additional examples, explore the `examples` directory in the repository.

## Development Setup

### Prerequisites

- **Poetry** (version 1.x only; v2 is unsupported)
- **Python 3.10** (exact version required for development)

### Installation Steps

1. Install Poetry from https://python-poetry.org/
2. Configure Poetry to use Python 3.10
3. Install dependencies:

```bash
make install
```

### Development Tools

The project includes a Makefile with useful commands:

- `make install` — Install dependencies from poetry.lock
- `make test` — Run tests with pytest
- `make pre-commit` — Run linters and formatters
- `make lint` — Execute pre-commit checks
- `make help` — Display all available commands

## Project Quality Standards

The repository maintains high code quality through:

- **Code style:** Black formatter for consistent formatting
- **Security scanning:** Bandit for vulnerability detection
- **Pre-commit hooks:** Automated checks before commits
- **Semantic versioning:** Following standard version numbering
- **MIT License:** Open source with permissive licensing

## Release Management

### Versioning

The project adheres to semantic versioning. Bump versions using:

```bash
poetry version <version|major|minor|patch>
```

### Publishing Releases

1. Bump the version number with Poetry
2. Commit changes to GitHub
3. Create a GitHub release
4. Publish to PyPI: `poetry publish --build`

### Release Categories

Pull requests are automatically categorized in releases using labels:

- "enhancement," "feature" → Features section
- "bug," "fix," "refactoring" → Fixes & Refactoring section
- "build," "ci," "testing" → Build System & CI/CD section
- "breaking" → Breaking Changes section
- "documentation" → Documentation section
- "dependencies" → Dependencies updates section

## Repository Information

**Stats:**
- 1.2k stars
- 429 forks
- 41 contributors
- 40 releases

**Current Version:** 0.20.0 (as of October 2025)

**Dependencies:** 195 projects depend on this SDK

## License

Licensed under the MIT License. See LICENSE.md for complete terms and conditions.

---

*This SDK was generated using the python-package-template project.*
