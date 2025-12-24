from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LaneStatus:
    lane_id: str
    connected: bool
    state: str  # "idle" | "running" | "error"
    message: str | None = None
    extra: dict[str, Any] | None = None


class LaneTransport(ABC):
    """
    Hardware abstraction layer.

    The rest of the system ONLY talks to this interface.
    You can swap implementations:
      - SimLaneTransport (dev/testing)
      - RealSerialLaneTransport (production hardware)
      - ReplayLaneTransport (future)
    """

    @abstractmethod
    def ping(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_lanes(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def get_lane_status(self, lane_id: str) -> LaneStatus:
        raise NotImplementedError

    @abstractmethod
    def start_lane(self, lane_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop_lane(self, lane_id: str) -> None:
        raise NotImplementedError
