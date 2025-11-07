# Linting and Code Quality Tools

This project uses modern Python linting tools to maintain code quality.

## Quick Start

### Check code quality
```bash
./scripts/lint.sh
```

### Auto-fix issues
```bash
./scripts/lint-fix.sh
```

## Tools Installed

### 1. Ruff (Linter + Formatter)
- **Fast Python linter** written in Rust
- Replaces Flake8, isort, pydocstyle, and more
- **Auto-fixes** most issues

**Manual commands:**
```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code (replaces Black)
ruff format src/ tests/

# Check formatting without changing files
ruff format --check src/ tests/
```

### 2. Mypy (Type Checker)
- **Static type checker** for Python
- Catches type-related bugs before runtime

**Manual commands:**
```bash
# Check types in src/
mypy src/

# Check specific file
mypy src/services/position_service.py

# More strict checking
mypy --strict src/
```

### 3. Pre-commit Hooks
- **Automatic checks** before each commit
- Runs ruff, mypy, and other checks
- Prevents committing code with issues

**Manual commands:**
```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Skip hooks for a commit (use sparingly!)
git commit --no-verify -m "message"
```

### 4. Vulture (Dead Code Detector)
- **Finds unused code** across the entire project
- Detects unused functions, classes, variables, and files
- Uses static analysis to find code that's never called/imported

**Manual commands:**
```bash
# Check for dead code (recommended)
./scripts/check-dead-code.sh

# Check with custom confidence level
vulture src/ .vulture_whitelist.py --min-confidence 60

# Sort by file size (find biggest issues first)
vulture src/ .vulture_whitelist.py --sort-by-size

# Check specific directory
vulture src/services/ --min-confidence 80
```

**Understanding confidence levels:**
- `90-100%`: Very likely unused (high priority)
- `70-89%`: Probably unused (investigate)
- `60-69%`: May be unused (many false positives)

**False positives:**
Vulture may flag code that IS actually used:
- FastAPI route functions (used via decorators)
- Pydantic model fields (used for serialization)
- pytest fixtures (used by the framework)

Add false positives to `.vulture_whitelist.py` to filter them out.

## Configuration

All configuration is in `pyproject.toml`:

### Ruff Configuration
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
    "N",   # pep8-naming
]
```

### Mypy Configuration
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
check_untyped_defs = true
strict_equality = true
```

## Common Issues and Fixes

### Import Sorting (I001)
```python
# ❌ Wrong order
from typing import Dict
import os
from src.config import logger

# ✅ Correct (auto-fixed by ruff)
import os
from typing import Dict

from src.config import logger
```

### Unused Imports (F401)
```python
# ❌ Imported but not used
from typing import Dict, List  # List is unused

# ✅ Auto-fixed
from typing import Dict
```

### Type Hints (UP006, UP035)
```python
# ❌ Old-style type hints
from typing import Dict, List
def func() -> Dict[str, List[int]]:
    pass

# ✅ Modern Python 3.11+ style
def func() -> dict[str, list[int]]:
    pass
```

### Optional Type Hints (UP045)
```python
# ❌ Old style
from typing import Optional
def func(x: Optional[str]) -> None:
    pass

# ✅ New style (Python 3.10+)
def func(x: str | None) -> None:
    pass
```

### Raise Without From (B904)
```python
# ❌ Loses original exception context
try:
    something()
except Exception:
    raise ValueError("Failed")

# ✅ Preserves exception chain
try:
    something()
except Exception as e:
    raise ValueError("Failed") from e
```

## Workflow Integration

### Before Committing
1. **Auto-fix issues**: `./scripts/lint-fix.sh`
2. **Check remaining issues**: `./scripts/lint.sh`
3. **Run tests**: `uv run pytest tests/`
4. **Commit**: Pre-commit hooks run automatically

### In CI/CD (Future)
```yaml
- name: Lint
  run: |
    ruff check src/ tests/
    ruff format --check src/ tests/
    mypy src/
```

## Ignoring Specific Issues

### Inline Comments
```python
# Ignore specific rule for one line
result = eval(user_input)  # noqa: S307

# Ignore all rules for one line (use sparingly!)
complex_legacy_code()  # noqa

# Ignore mypy type check
x = func()  # type: ignore[no-any-return]
```

### File-Level Ignores
In `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ARG001"]  # Unused args OK in tests (fixtures)
"scripts/*" = ["T201"]  # Print statements OK in scripts
```

## Statistics

Current codebase status (as of setup):
- **435 total issues found**
- **273 auto-fixable** with `ruff check --fix`
- **162 require manual review**

Common issues:
- `UP006`: Old-style type annotations (114 instances)
- `B904`: Missing `from` in raise statements (74 instances)
- `UP045`: Optional type hints (64 instances)
- `I001`: Unsorted imports (49 instances)

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)

## Tips

1. **Run linting frequently** - Catch issues early
2. **Use auto-fix liberally** - Let ruff handle formatting
3. **Review type hints** - mypy catches subtle bugs
4. **Don't ignore warnings blindly** - Understand what they mean
5. **Keep configuration updated** - Review rules periodically
