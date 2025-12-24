from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from indigo.db.orm.tables import Recipe, RecipePinBreakStep


@dataclass(frozen=True)
class RecipeUpsertResult:
    lane_addr: int
    recipe_id: int
    sha256: str
    updated_at_ts: bool


class RecipeService:
    """
    Owns recipe persistence and retrieval.

    Current DB schema (tables.py in this repo):
      - recipes: versioned by sha256, with one active recipe per lane enforced in app logic
      - recipe_pinbreak_steps: normalized rows (step_index 0..N-1)

    API payload is still "legacy-ish" keys (fixedholdtime, autopinbreaktime, etc.),
    but we map it into normalized DB columns.
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def upsert_lane_recipe(self, lane_addr: int, payload: dict[str, Any]) -> RecipeUpsertResult:
        """
        Store a new active recipe version for this lane if payload changed.
        If the currently-active recipe has the same sha256, do nothing (idempotent).
        """
        sha = Recipe.compute_sha256_from_payload(payload)

        # Scalars (legacy keys → new columns)
        name = _get_str(payload, "name", default=None)
        cycle_type = _get_str(payload, "cycletype", "cycle_type", default="full")
        fixed_hold_time = _get_bool(payload, "fixedholdtime", "fixed_hold_time", default=False)

        autopinbreak_enabled = _get_bool(payload, "autopinbreak", "autopinbreak_enabled", default=False)
        num_autopinbreaks = _get_int(payload, "numberofautopinbreaks", "num_autopinbreaks", default=0)

        attempt_time_s = _get_int(payload, "attempttime", "attempt_time_s", default=0)

        thermal_temp_c = _get_float(payload, "thermaltemp", "thermal_temp_c", default=0.0)
        reflux_enabled = _get_bool(payload, "refluxenabled", "reflux_enabled", default=False)
        reflux_temp_c = _get_float(payload, "refluxtemp", "reflux_temp_c", default=0.0)

        purge_vac_switchpoint = _get_float(payload, "purgevacswitchpoint", "purge_vac_switchpoint", default=0.0)
        stir_speed_rpm = _get_int(payload, "stirspeed", "stir_speed_rpm", default=0)
        purge_set_pressure = _get_float(payload, "purgesetpressure", "purge_set_pressure", default=0.0)

        # Arrays (normalized into rows)
        ap_time = _get_list(payload, "autopinbreaktime")
        ap_press = _get_list(payload, "autopinbreakpressure")
        post_th = _get_list(payload, "postpinbreakthermaltemp")
        post_pr = _get_list(payload, "postpinbreakpressure")
        post_rf = _get_list(payload, "postpinbreakrefluxtemp")
        post_st = _get_list(payload, "postpinbreakstirspeed")

        inferred_n = max(len(ap_time), len(ap_press), len(post_th), len(post_pr), len(post_rf), len(post_st), 0)
        nsteps = num_autopinbreaks if num_autopinbreaks > 0 else inferred_n

        with self._session_factory() as session:  # type: Session
            active: Recipe | None = (
                session.query(Recipe)
                .filter(Recipe.lane == lane_addr, Recipe.active.is_(True))
                .order_by(Recipe.created_ts.desc())
                .one_or_none()
            )

            if active is not None and active.sha256 == sha:
                return RecipeUpsertResult(lane_addr=lane_addr, recipe_id=active.id, sha256=sha, updated_at_ts=False)

            # deactivate any existing active recipes for this lane
            session.query(Recipe).filter(Recipe.lane == lane_addr, Recipe.active.is_(True)).update({"active": False})

            r = Recipe(
                lane=lane_addr,
                name=name,
                cycle_type=cycle_type,
                fixed_hold_time=fixed_hold_time,
                autopinbreak_enabled=autopinbreak_enabled,
                num_autopinbreaks=nsteps,
                attempt_time_s=attempt_time_s,
                thermal_temp_c=thermal_temp_c,
                reflux_enabled=reflux_enabled,
                reflux_temp_c=reflux_temp_c,
                purge_vac_switchpoint=purge_vac_switchpoint,
                stir_speed_rpm=stir_speed_rpm,
                purge_set_pressure=purge_set_pressure,
                sha256=sha,
                active=True,
            )
            session.add(r)
            session.flush()  # assigns r.id

            # insert steps (0..nsteps-1)
            for i in range(nsteps):
                step = RecipePinBreakStep(
                    recipe_id=r.id,
                    step_index=i,
                    autopinbreak_time_ms=_safe_int(ap_time, i),
                    autopinbreak_pressure=_safe_float(ap_press, i),
                    postpinbreak_thermal_temp_c=_safe_float(post_th, i),
                    postpinbreak_pressure=_safe_float(post_pr, i),
                    postpinbreak_reflux_temp_c=_safe_float(post_rf, i),
                    postpinbreak_stir_speed_rpm=_safe_int(post_st, i),
                )
                session.add(step)

            session.commit()
            return RecipeUpsertResult(lane_addr=lane_addr, recipe_id=r.id, sha256=sha, updated_at_ts=True)

    def get_lane_recipe(self, lane_addr: int) -> dict[str, Any] | None:
        """
        Return the active recipe for a lane, shaped for API callers.
        """
        with self._session_factory() as session:  # type: Session
            r: Recipe | None = (
                session.query(Recipe)
                .filter(Recipe.lane == lane_addr, Recipe.active.is_(True))
                .order_by(Recipe.created_ts.desc())
                .one_or_none()
            )
            if r is None:
                return None

            steps = (
                session.query(RecipePinBreakStep)
                .filter(RecipePinBreakStep.recipe_id == r.id)
                .order_by(RecipePinBreakStep.step_index.asc())
                .all()
            )

            # Return legacy-ish keys so old clients/tests are easy
            return {
                "lane_addr": r.lane,
                "name": r.name,
                "cycletype": r.cycle_type,
                "fixedholdtime": r.fixed_hold_time,
                "autopinbreak": r.autopinbreak_enabled,
                "numberofautopinbreaks": r.num_autopinbreaks,
                "attempttime": r.attempt_time_s,
                "thermaltemp": r.thermal_temp_c,
                "refluxenabled": r.reflux_enabled,
                "refluxtemp": r.reflux_temp_c,
                "purgevacswitchpoint": r.purge_vac_switchpoint,
                "stirspeed": r.stir_speed_rpm,
                "purgesetpressure": r.purge_set_pressure,
                "sha256": r.sha256,
                "active": r.active,
                "created_ts": r.created_ts.isoformat() if r.created_ts else None,
                "pinbreak_steps": [
                    {
                        "idx": s.step_index,
                        "autopinbreaktime": s.autopinbreak_time_ms,
                        "autopinbreakpressure": s.autopinbreak_pressure,
                        "postpinbreakthermaltemp": s.postpinbreak_thermal_temp_c,
                        "postpinbreakpressure": s.postpinbreak_pressure,
                        "postpinbreakrefluxtemp": s.postpinbreak_reflux_temp_c,
                        "postpinbreakstirspeed": s.postpinbreak_stir_speed_rpm,
                    }
                    for s in steps
                ],
            }


def _get_str(d: dict[str, Any], *keys: str, default: str | None) -> str | None:
    for k in keys:
        if k in d and d[k] is not None:
            return str(d[k])
    return default


def _get_bool(d: dict[str, Any], *keys: str, default: bool) -> bool:
    for k in keys:
        if k in d and d[k] is not None:
            return bool(d[k])
    return default


def _get_int(d: dict[str, Any], *keys: str, default: int) -> int:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return int(d[k])
            except Exception:
                pass
    return default


def _get_float(d: dict[str, Any], *keys: str, default: float) -> float:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except Exception:
                pass
    return default


def _get_list(d: dict[str, Any], key: str) -> list[Any]:
    v = d.get(key, [])
    return list(v) if isinstance(v, (list, tuple)) else []


def _safe_int(arr: list[Any], idx: int) -> int | None:
    try:
        return int(arr[idx])
    except Exception:
        return None


def _safe_float(arr: list[Any], idx: int) -> float | None:
    try:
        return float(arr[idx])
    except Exception:
        return None
