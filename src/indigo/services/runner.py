from __future__ import annotations

import logging
import sys
from pathlib import Path

from indigo.config.settings import get_settings


def _ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _configure_logging(log_dir: Path, level: str) -> None:
    _ensure_dirs(log_dir)

    log_file = log_dir / "indigo.log"

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=handlers,
    )


def run_services() -> None:
    """
    Used by: `make services` and systemd.
    Keep stable—this is the “machine runner” entry point.
    """
    s = get_settings()
    _ensure_dirs(s.INDIGO_DATA_DIR, s.LOG_DIR)
    _configure_logging(s.LOG_DIR, s.LOG_LEVEL)

    log = logging.getLogger("indigo.runner")
    log.info("Starting Indigo services...")
    log.info("SIMULATION_MODE=%s POLL_HZ=%s", s.SIMULATION_MODE, s.POLL_HZ)

    # Import here to avoid side-effects during lint/test collection
    from indigo.services.bus_poll_service import BusPollService

    svc = BusPollService(simulation_mode=s.SIMULATION_MODE, poll_hz=s.POLL_HZ)
    svc.run_forever()
