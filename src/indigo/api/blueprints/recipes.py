from __future__ import annotations

from flask import Blueprint, jsonify, request

from indigo.db.engine import get_session_factory
from indigo.services.recipe_service import RecipeService

bp = Blueprint("recipes", __name__, url_prefix="/api")


@bp.post("/lanes/<int:lane_addr>/recipe")
def upsert_lane_recipe(lane_addr: int):
    payload = request.get_json(silent=True) or {}
    svc = RecipeService(get_session_factory())

    res = svc.upsert_lane_recipe(lane_addr=lane_addr, payload=payload)
    return jsonify(
        {
            "ok": True,
            "lane_addr": res.lane_addr,
            "recipe_id": res.recipe_id,
            "updated_at_ts": res.updated_at_ts,
        }
    )


@bp.get("/lanes/<int:lane_addr>/recipe")
def get_lane_recipe(lane_addr: int):
    svc = RecipeService(get_session_factory())
    r = svc.get_lane_recipe(lane_addr=lane_addr)
    if r is None:
        return jsonify({"ok": False, "error": "recipe_not_found", "lane_addr": lane_addr}), 404
    return jsonify({"ok": True, "recipe": r})
