from __future__ import annotations

from dataclasses import dataclass, field

from indigo.hw.devices import LaneStatus, UtilityStatus


@dataclass
class DeviceRegistry:
    lane_addrs: list[int]
    utility_addr: int

    lanes: dict[int, LaneStatus] = field(default_factory=dict)
    utility: UtilityStatus | None = None

    last_seen_ts: dict[int, float] = field(default_factory=dict)

    def set_lane_status(self, status: LaneStatus, ts: float) -> None:
        self.lanes[status.addr] = status
        self.last_seen_ts[status.addr] = ts

    def set_utility_status(self, status: UtilityStatus, ts: float) -> None:
        self.utility = status
        self.last_seen_ts[status.addr] = ts

    def lane_snapshot(self) -> list[dict]:
        out: list[dict] = []
        for addr in self.lane_addrs:
            st = self.lanes.get(addr)
            out.append(
                {
                    "addr": addr,
                    "online": bool(st and st.online),
                    "error_status": st.error_status if st else None,
                    "status": st.__dict__ if st else None,
                    "last_seen_ts": self.last_seen_ts.get(addr),
                }
            )
        return out

    def utility_snapshot(self) -> dict:
        st = self.utility
        return {
            "addr": self.utility_addr,
            "online": bool(st and st.online),
            "error_status": st.error_status if st else None,
            "status": st.__dict__ if st else None,
            "last_seen_ts": self.last_seen_ts.get(self.utility_addr),
        }
