from __future__ import annotations

from indigo.config.settings import get_settings
from indigo.db.engine import init_db
from indigo.services.recipe_store import RecipeStore


def test_recipe_store_roundtrip(tmp_path, monkeypatch):
    # Force INDIGO_DATA_DIR to temp for sqlite file
    monkeypatch.setenv("INDIGO_DATA_DIR", str(tmp_path))

    s = get_settings()
    SessionLocal = init_db(s)

    payload = {
        "cycletype": "full",
        "fixedholdtime": True,
        "numberofautopinbreaks": 3,
        "autopinbreak": True,
        "autopinbreaktime": [100, 200, 300],
        "autopinbreakpressure": [1.1, 1.2, 1.3],
        "postpinbreakthermaltemp": [10, 11, 12],
        "postpinbreakpressure": [2.1, 2.2, 2.3],
        "postpinbreakrefluxtemp": [3.1, 3.2, 3.3],
        "postpinbreakstirspeed": [400, 500, 600],
        "attempttime": 52200,
        "thermaltemp": -10,
        "refluxenabled": True,
        "refluxtemp": 1,
        "purgevacswitchpoint": 0,
        "stirspeed": 500,
        "purgesetpressure": 1,
    }

    with SessionLocal() as db:
        store = RecipeStore(db)
        r = store.set_lane_recipe(1, payload, name="Lane 1", activate=True)

        assert r.lane == 1
        assert r.active is True
        assert r.num_autopinbreaks == 3
        assert len(r.pinbreak_steps) == 3
        assert r.pinbreak_steps[1].autopinbreak_time_ms == 200

        active = store.get_active_recipe(1)
        assert active is not None
        assert active.sha256 == r.sha256
