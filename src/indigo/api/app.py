from __future__ import annotations

import logging

from flask import Flask, jsonify

from indigo.api.blueprints.devices import bp as devices_bp
from indigo.api.blueprints.health import bp as health_bp
from indigo.api.blueprints.lanes import bp as lanes_bp
from indigo.config.settings import get_settings


def create_app() -> Flask:
    app = Flask(__name__)

    # Register API blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(lanes_bp)

    @app.get("/api/_meta")
    def meta() -> tuple[dict, int]:
        s = get_settings()
        return jsonify(
            {
                "simulation_mode": s.SIMULATION_MODE,
                "poll_hz": s.POLL_HZ,
                "enable_api": s.ENABLE_API,
                "enable_ui": s.ENABLE_UI,
            }
        ), 200

    return app


def run_dev() -> None:
    s = get_settings()
    if not s.ENABLE_API:
        raise RuntimeError("ENABLE_API is false; dev server disabled by settings")

    app = create_app()
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app.run(host=s.API_HOST, port=s.API_PORT, debug=True)
