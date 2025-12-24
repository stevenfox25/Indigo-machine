from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from indigo.db.orm.tables import Recipe, RecipePinBreakStep


def _get_arr(payload: dict[str, Any], key: str) -> list[Any]:
    v = payload.get(key)
    if v is None:
        return []
    if isinstance(v, list):
        return v
    # tolerate Mongo-ish types or single values
    return [v]


class RecipeStore:
    def __init__(self, session: Session):
        self.session = session

    def set_lane_recipe(
        self,
        lane: int,
        payload: dict[str, Any],
        *,
        name: str | None = None,
        activate: bool = True,
    ) -> Recipe:
        """
        Upserts a new recipe version for a lane. Leaves history in DB.
        If activate=True, deactivates other recipes for that lane.
        """
        sha = Recipe.compute_sha256_from_payload(payload)

        # Deactivate any current active recipe for lane
        if activate:
            self.session.query(Recipe).filter(Recipe.lane == lane, Recipe.active.is_(True)).update({"active": False})

        r = Recipe(
            lane=lane,
            name=name,
            cycle_type=str(payload.get("cycletype", "full")),
            fixed_hold_time=bool(payload.get("fixedholdtime", False)),
            autopinbreak_enabled=bool(payload.get("autopinbreak", False)),
            num_autopinbreaks=int(payload.get("numberofautopinbreaks", 0) or 0),
            attempt_time_s=int(payload.get("attempttime", 0) or 0),
            thermal_temp_c=float(payload.get("thermaltemp", 0) or 0),
            reflux_enabled=bool(payload.get("refluxenabled", False)),
            reflux_temp_c=float(payload.get("refluxtemp", 0) or 0),
            purge_vac_switchpoint=float(payload.get("purgevacswitchpoint", 0) or 0),
            stir_speed_rpm=int(payload.get("stirspeed", 0) or 0),
            purge_set_pressure=float(payload.get("purgesetpressure", 0) or 0),
            sha256=sha,
            active=activate,
        )

        # Build steps from arrays (they must align by index)
        t_ms = _get_arr(payload, "autopinbreaktime")
        p = _get_arr(payload, "autopinbreakpressure")
        post_t = _get_arr(payload, "postpinbreakthermaltemp")
        post_p = _get_arr(payload, "postpinbreakpressure")
        post_r = _get_arr(payload, "postpinbreakrefluxtemp")
        post_s = _get_arr(payload, "postpinbreakstirspeed")

        # Determine N: prefer explicit number, otherwise longest array
        n = r.num_autopinbreaks
        if n <= 0:
            n = max(len(t_ms), len(p), len(post_t), len(post_p), len(post_r), len(post_s), 0)

        for i in range(n):
            step = RecipePinBreakStep(
                step_index=i,
                autopinbreak_time_ms=int(t_ms[i]) if i < len(t_ms) and t_ms[i] is not None else None,
                autopinbreak_pressure=float(p[i]) if i < len(p) and p[i] is not None else None,
                postpinbreak_thermal_temp_c=float(post_t[i]) if i < len(post_t) and post_t[i] is not None else None,
                postpinbreak_pressure=float(post_p[i]) if i < len(post_p) and post_p[i] is not None else None,
                postpinbreak_reflux_temp_c=float(post_r[i]) if i < len(post_r) and post_r[i] is not None else None,
                postpinbreak_stir_speed_rpm=int(post_s[i]) if i < len(post_s) and post_s[i] is not None else None,
            )
            r.pinbreak_steps.append(step)

        self.session.add(r)
        self.session.commit()
        return r

    def get_active_recipe(self, lane: int) -> Recipe | None:
        return self.session.query(Recipe).filter(Recipe.lane == lane, Recipe.active.is_(True)).one_or_none()

    def list_recipes(self, lane: int) -> list[Recipe]:
        return self.session.query(Recipe).filter(Recipe.lane == lane).order_by(Recipe.created_ts.desc()).all()
