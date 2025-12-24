from __future__ import annotations

from flask import Blueprint, current_app, jsonify

bp = Blueprint("health", __name__)


@bp.get("/api/health")
def health():
    settings = current_app.config["INDIGO_SETTINGS"]
    return jsonify(
        status="ok",
        simulation=bool(settings.simulation),
        enable_ui=bool(settings.enable_ui),
    )
