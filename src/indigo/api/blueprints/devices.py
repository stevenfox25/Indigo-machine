from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("devices", __name__)


@bp.get("/api/devices")
def devices() -> tuple[dict, int]:
    # Stub for Phase 2.x: API returns something sane even before DB integration.
    return jsonify({"devices": []}), 200
