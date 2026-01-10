# -------------------------
# Configuration
# -------------------------

PYTHON_VERSION ?= 3.12
VENV_DIR ?= .venv
UV ?= uv

# -------------------------
# Environment
# -------------------------

.PHONY: venv
venv:
	$(UV) venv --python $(PYTHON_VERSION)

.PHONY: activate
activate:
	@echo "Run: source $(VENV_DIR)/bin/activate"

# -------------------------
# Dependency management
# -------------------------

.PHONY: lock
lock:
	$(UV) pip compile pyproject.toml -o uv.lock

.PHONY: sync
sync:
	$(UV) pip sync uv.lock

.PHONY: install
install:
	$(UV) pip install -e .

.PHONY: install-dev
install-dev:
	$(UV) pip install -e '.[dev]'

.PHONY: dev
dev: sync install-dev
	@echo "Development environment ready."

# -------------------------
#  tests
# -------------------------

.PHONY: test
test:
	pytest

# -------------------------
#  quality gates
# -------------------------

.PHONY: format
format:
	ruff format .

.PHONY: lint
lint:
	ruff check .
	mypy src

pre-commit:
	pre-commit run --all-files

check: lint test

ci: lint test
	coverage run -m pytest
	coverage report


# -------------------------
# Clean
# -------------------------

.PHONY: clean
clean:
	rm -rf $(VENV_DIR)
	rm -rf .ruff_cache .mypy_cache .pytest_cache __pycache__
	find . -name "__pycache__" -type d -exec rm -rf {} +

# -------------------------
# Docs
# -------------------------

.PHONY: docs docs-live

docs:
	sphinx-build docs docs/_build

docs-live:
	sphinx-autobuild docs docs/_build
