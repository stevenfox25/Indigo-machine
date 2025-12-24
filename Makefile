APP=indigo
UV=uv

.PHONY: install dev lint test clean sync

install:
	$(UV) venv
	$(UV) pip install -e ".[dev]"

sync:
	$(UV) pip sync uv.lock

dev:
	$(UV) run python -c "from indigo.api.app import run_dev; run_dev()"

lint:
	$(UV) run ruff check .

test:
	$(UV) run pytest

clean:
	rm -rf .venv .pytest_cache .ruff_cache .indigo_data uv.lock
