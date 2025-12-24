from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from indigo.hw.transport.base import LaneStatus, LaneTransport


@dataclass
class _SimLane:
    lane_id: str
    state: str = "idle"  # idle|running|error
    last_change_ts: float = 0.0
    message: str | None = None

    def to_status(self) -> LaneStatus:
        extra: dict[str, Any] = {
            "last_change_ts": self.last_change_ts,
        }
        return LaneStatus(
            lane_id=self.lane_id,
            connected=True,
            state=self.state,
            message=self.message,
            extra=extra,
        )


class SimLaneTransport(LaneTransport):
    """
    In-memory simulator.
    Deterministic enough for dev, simple enough to evolve.
    """

    def __init__(self, lane_count: int = 4, seed: int | None = 539):
        self._rng = random.Random(seed)
        self._lanes: dict[str, _SimLane] = {}
        for i in range(1, lane_count + 1):
            lane_id = f"lane{i}"
            self._lanes[lane_id] = _SimLane(lane_id=lane_id, last_change_ts=time.time())

    def ping(self) -> bool:
        return True

    def list_lanes(self) -> list[str]:
        return sorted(self._lanes.keys())

    def get_lane_status(self, lane_id: str) -> LaneStatus:
        lane = self._lanes.get(lane_id)
        if not lane:
            return LaneStatus(lane_id=lane_id, connected=False, state="error", message="Unknown lane")
        return lane.to_status()

    def start_lane(self, lane_id: str) -> None:
        lane = self._lanes.get(lane_id)
        if not lane:
            raise KeyError(f"Unknown lane_id: {lane_id}")

        # Example rule: starting from error resets to running but sets a message
        if lane.state == "error":
            lane.message = "Recovered from error (sim)"
        else:
            lane.message = None

        lane.state = "running"
        lane.last_change_ts = time.time()

        # Optional small chance to simulate a fault after start
        if self._rng.random() < 0.03:
            lane.state = "error"
            lane.message = "Simulated fault on start"
            lane.last_change_ts = time.time()

    def stop_lane(self, lane_id: str) -> None:
        lane = self._lanes.get(lane_id)
        if not lane:
            raise KeyError(f"Unknown lane_id: {lane_id}")
        lane.state = "idle"
        lane.message = None
        lane.last_change_ts = time.time()
