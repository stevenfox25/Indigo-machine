from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("lanes", __name__)


@bp.get("/api/lanes")
def lanes() -> tuple[dict, int]:
    # Stub for Phase 2.x: later we’ll pull from DeviceRegistry snapshots
    return jsonify({"lanes": []}), 200
