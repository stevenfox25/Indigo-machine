from __future__ import annotations

import logging

from flask import Flask, jsonify

from indigo.api.blueprints.devices import bp as devices_bp
from indigo.api.blueprints.health import bp as health_bp
from indigo.api.blueprints.lanes import bp as lanes_bp
from indigo.api.blueprints.recipes import bp as recipes_bp  # NEW
from indigo.config.settings import get_settings


def create_app() -> Flask:
    s = get_settings()
    app = Flask(__name__)

    app.register_blueprint(health_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(lanes_bp)
    app.register_blueprint(recipes_bp)  # NEW

    @app.get("/api/_meta")
    def meta():
        return jsonify(
            {
                "ok": True,
                "simulation_mode": s.SIMULATION_MODE,
                "poll_hz": s.POLL_HZ,
                "lane_addrs": list(s.LANE_ADDRS),
                "utility_addr": s.UTILITY_ADDR,
                "enable_api": s.ENABLE_API,
                "enable_ui": s.ENABLE_UI,
            }
        )

    return app


def run_dev() -> None:
    s = get_settings()
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app = create_app()
    app.run(host=s.API_HOST, port=s.API_PORT, debug=True)
