# Indigo Machine - Architecture (Source of Truth)

## Goals
- Keep deployment repeatable (multiple machines).
- Keep codebase modular (API, services, HW, protocol, simulation).
- Prevent regressions using phase checkpoints.

## Entry points (public contract)
- `make dev` -> runs Flask dev API server via `indigo.api.app.run_dev()`
- `make services` -> runs machine services via `indigo.services.runner.run_services()`

## Feature gates (settings)
- `ENABLE_API` (default True): registers API blueprints.
- `ENABLE_UI` (default False): purchased UI is not mounted by default.
- `SIMULATION_MODE` (default True): allows Windows dev and local runs without hardware.

Environment variables:
- `ENABLE_API`, `ENABLE_UI`, `SIMULATION_MODE`
- `API_HOST`, `API_PORT`, `API_DEBUG`
- `INDIGO_DATA_DIR`, `INDIGO_LOG_DIR`, `LOG_LEVEL`
- `UART_PORT`, `UART_BAUD`
- `POLL_HZ`

## Modules
- `indigo/api/` Flask app + blueprints
- `indigo/services/` long-running services (poller, registry)
- `indigo/hw/` bus and device abstractions
- `indigo/hw/protocol/` framing + codec
- `indigo/hw/devices/` lane + utility board models

## Current phase behavior (2.6)
- Polling service runs under `make services`.
- API reads device state from registry (no DB persistence yet).
- Simulation mode is the default for dev portability.

## Next planned (later phase)
- Persist latest snapshot + event log (SQLite).
- Add log rotation and “capture raw frames on failure”.
