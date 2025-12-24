from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/api/health")
def health() -> tuple[dict, int]:
    return jsonify({"ok": True}), 200
