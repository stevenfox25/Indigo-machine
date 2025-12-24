from __future__ import annotations

import logging
import threading
import time

from indigo.config.settings import get_settings

# Import bus types lazily-ish, but still type-safe enough for runtime.
from indigo.hw.bus.sim_bus import SimBus
from indigo.hw.devices import LaneboardClient, UtilityBoardClient
from indigo.services.device_registry import DeviceRegistry


class BusPollService:
    """
    Polls devices on the bus at a fixed interval.

    Phase 2.6 behavior:
      - Poll UtilityBoard every cycle (critical)
      - Poll lanes in round-robin
    """

    def __init__(
        self,
        *,
        simulation_mode: bool,
        poll_hz: float,
        bus=None,
        registry: DeviceRegistry | None = None,
    ) -> None:
        self.log = logging.getLogger("indigo.bus_poll_service")

        self.simulation_mode = simulation_mode
        self.poll_period_s = 1.0 / max(float(poll_hz), 0.1)

        s = get_settings()

        # Construct defaults if not injected.
        self.bus = bus if bus is not None else SimBus()
        self.registry = registry if registry is not None else DeviceRegistry(
            lane_addrs=list(s.LANE_ADDRS),
            utility_addr=int(s.UTILITY_ADDR),
        )

        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None

        self._lane_clients = {a: LaneboardClient(a) for a in self.registry.lane_addrs}
        self._utility_client = UtilityBoardClient(self.registry.utility_addr)
        self._lane_idx = 0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, name="BusPollService", daemon=True)
        self._thread.start()
        self.log.info("BusPollService started (poll_period=%.3fs)", self.poll_period_s)

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self.log.info("BusPollService stopped")

    def run_forever(self) -> None:
        """
        Used by runner / systemd.

        Keeps the service alive until interrupted.
        """
        self.start()
        try:
            while not self._stop_evt.is_set():
                time.sleep(0.25)
        except KeyboardInterrupt:
            self.log.info("KeyboardInterrupt; stopping BusPollService")
        finally:
            self.stop()

    def _run(self) -> None:
        while not self._stop_evt.is_set():
            ts = time.time()

            # 1) poll utility first (critical)
            try:
                req = self._utility_client.build_status_request()
                resp = self.bus.send_and_recv(req, timeout_s=0.25)
                if resp:
                    ust = UtilityBoardClient.parse_status_response(resp)
                    if ust:
                        self.registry.set_utility_status(ust, ts)
            except Exception as e:
                # Non-fatal in Phase 2.x, but log it.
                self.log.debug("Utility poll failed: %s", e)

            # 2) poll one lane per tick (round-robin)
            lane_addrs = self.registry.lane_addrs
            if lane_addrs:
                addr = lane_addrs[self._lane_idx % len(lane_addrs)]
                self._lane_idx += 1
                try:
                    client = self._lane_clients[addr]
                    req = client.build_status_request()
                    resp = self.bus.send_and_recv(req, timeout_s=0.25)
                    if resp:
                        st = client.parse_status_response(resp)
                        if st:
                            self.registry.set_lane_status(st, ts)
                except Exception as e:
                    self.log.debug("Lane %s poll failed: %s", addr, e)

            time.sleep(self.poll_period_s)
