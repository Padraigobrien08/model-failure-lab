SHELL := /bin/bash
PYTHON ?= python3

.PHONY: help install install-dev install-ci lint test test-fast check demo datasets-list run report compare smoke build verify-dist publish clean

help: ## Show available developer commands
	@echo "Model Failure Lab Make targets"
	@echo ""
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install package (local checkout)
	$(PYTHON) -m pip install .

install-dev: ## Install editable dev environment
	$(PYTHON) -m pip install -e '.[dev]'

install-ci: ## Install dependencies used in CI
	$(PYTHON) -m pip install .
	$(PYTHON) -m pip install -e '.[dev,legacy]'

lint: ## Run Ruff lint checks
	$(PYTHON) -m ruff check src tests

test: ## Run full test suite
	$(PYTHON) -m pytest -q

test-fast: ## Run smoke + governance-focused tests
	$(PYTHON) -m pytest -q tests/unit/test_cli_production_smoke.py tests/unit/test_cli_governance.py

check: lint test ## Run lint + tests

demo: ## Run deterministic demo flow
	$(PYTHON) -m model_failure_lab demo

datasets-list: ## List bundled/local datasets
	$(PYTHON) -m model_failure_lab datasets list

run: ## Run bundled reasoning dataset with demo model
	$(PYTHON) -m model_failure_lab run --dataset reasoning-failures-v1 --model demo

report: ## Build report for latest run in ./runs
	@run_id=$$(ls runs | sort | tail -n 1); \
	if [ -z "$$run_id" ]; then \
		echo "No runs found. Execute 'make run' first."; \
		exit 1; \
	fi; \
	$(PYTHON) -m model_failure_lab report --run "$$run_id"

compare: ## Compare latest two runs in ./runs
	@baseline=$$(ls runs | sort | tail -n 2 | head -n 1); \
	candidate=$$(ls runs | sort | tail -n 1); \
	if [ -z "$$baseline" ] || [ -z "$$candidate" ] || [ "$$baseline" = "$$candidate" ]; then \
		echo "Need at least two runs in ./runs. Execute 'make run' twice first."; \
		exit 1; \
	fi; \
	$(PYTHON) -m model_failure_lab compare "$$baseline" "$$candidate"

smoke: install demo datasets-list run report ## Clean-clone smoke flow

build: ## Build source and wheel distributions
	$(PYTHON) -m pip install build
	$(PYTHON) -m build

verify-dist: build ## Verify built distributions with twine check
	$(PYTHON) -m pip install twine
	$(PYTHON) -m twine check dist/*

publish: verify-dist ## Publish distributions to PyPI using TWINE_* env vars
	@if [ -z "$$TWINE_USERNAME" ] || [ -z "$$TWINE_PASSWORD" ]; then \
		echo "TWINE_USERNAME and TWINE_PASSWORD must be set (use __token__ + PyPI token)."; \
		exit 1; \
	fi
	$(PYTHON) -m twine upload dist/*

clean: ## Remove local artifact dirs generated in workspace root
	rm -rf runs reports .failure_lab dist build *.egg-info
