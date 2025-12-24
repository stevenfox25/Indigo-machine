UV=uv
DATE := $(shell powershell -Command "Get-Date -Format yyyyMMdd-HHmmss")
SNAPSHOT_FILE := snapshot-$(DATE).txt

.PHONY: install dev services lint test clean sync

install:
	$(UV) venv
	$(UV) pip install -e ".[dev]"

sync:
	$(UV) pip sync uv.lock

dev:
	$(UV) run python -c "from indigo.api.app import run_dev; run_dev()"

services:
	$(UV) run python -c "from indigo.services.runner import run_services; run_services()"

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest

clean:
	rm -rf .venv .pytest_cache .ruff_cache .indigo_data uv.lock

snapshot:
	@echo "================ Indigo Snapshot ================"
	@echo
	@echo "GIT STATUS:"
	@git status --short
	@echo
	@echo "GIT BRANCH / COMMIT:"
	@git branch --show-current
	@git rev-parse --short HEAD
	@echo
	@echo "TRACKED CORE FILES:"
	@git ls-files | rg "src/indigo/(api|services|hw|db)"
	@echo
	@echo "================================================="
	@echo "GIT DIFF (Status):"
	@git diff --stat
	@echo "================================================="


snapshot-file:
	@make snapshot > docs\checkpoints\$(SNAPSHOT_FILE)
	@$(UV) run python tools\snapshot_settings.py >> docs\checkpoints\$(SNAPSHOT_FILE)
	@$(UV) run python tools\snapshot_core_imports.py >> docs\checkpoints\$(SNAPSHOT_FILE)
	@echo "Snapshot written to docs\checkpoints\$(SNAPSHOT_FILE)

