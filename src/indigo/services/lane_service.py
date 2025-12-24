from __future__ import annotations

import logging
from dataclasses import dataclass

from indigo.hw.transport.base import LaneStatus, LaneTransport

log = logging.getLogger(__name__)


@dataclass
class LaneServiceConfig:
    poll_interval_sec: float = 1.0


class LaneService:
    """
    Thin wrapper around transport that can evolve into:
    - polling
    - caching state
    - eventing
    - safety rules
    """

    def __init__(self, transport: LaneTransport, cfg: LaneServiceConfig | None = None):
        self.transport = transport
        self.cfg = cfg or LaneServiceConfig()

    def list_lanes(self) -> list[str]:
        return self.transport.list_lanes()

    def get_all_statuses(self) -> list[LaneStatus]:
        lanes = self.transport.list_lanes()
        return [self.transport.get_lane_status(lane_id) for lane_id in lanes]

    def start(self, lane_id: str) -> None:
        log.info("Starting lane %s", lane_id)
        self.transport.start_lane(lane_id)

    def stop(self, lane_id: str) -> None:
        log.info("Stopping lane %s", lane_id)
        self.transport.stop_lane(lane_id)
