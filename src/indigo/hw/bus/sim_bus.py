from __future__ import annotations

import time

from indigo.hw.bus.base import Bus
from indigo.hw.protocol.codec import Frame


class SimBus(Bus):
    """
    Phase 2.x simulation bus.

    Behavior (minimal/stable):
      - Echoes status responses for UtilityBoard and LaneBoards
      - ACKs other messages

    This is intentionally simple; it exists to keep the app runnable and testable
    while we evolve real RS-485 transport in Phase 3.
    """

    def __init__(self) -> None:
        # You can add deterministic simulated state here later.
        self._t0 = time.time()

    def send_and_recv(self, frame: Frame, timeout_s: float = 0.25) -> Frame | None:
        # Very small simulated delay
        time.sleep(min(timeout_s, 0.01))

        # Message types we know about:
        # Utility status request: 0x20 -> respond 0x83
        # Lane status request: 0x20 -> respond 0x82 (assuming laneboard uses that)
        if frame.msg_type == 0x20:
            # Heuristic: utility is addr 0x09 by your old code.
            if frame.addr == 0x09:
                # payload1, payload2, reserved..., error_status(last)
                # safe_chain_ok bit set => payload2 bit0 = 1
                payload1 = 0b00000000
                payload2 = 0b00000001
                error_status = 0
                payload = bytes([payload1, payload2, 0, 0, error_status])
                return Frame(addr=frame.addr, msg_type=0x83, payload=payload)

            # Lane default simulated response
            payload = bytes([0, 0, 0, 0, 0])  # keep it simple for now
            return Frame(addr=frame.addr, msg_type=0x82, payload=payload)

        # Otherwise, return ACK
        return Frame(addr=frame.addr, msg_type=0xFF, payload=b"\x00")
