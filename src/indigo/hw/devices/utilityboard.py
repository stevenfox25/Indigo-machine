from __future__ import annotations

from dataclasses import dataclass

from indigo.hw.protocol.codec import Frame


# ----------------------------
# Message / Response Types
# ----------------------------
MSG_STATUS_REQ = 0x20
MSG_STOP = 0x24
MSG_INITIALIZE = 0x25

MSG_MAIN_SOLVENT_VALVE = 0x97
MSG_MAIN_N2_VALVE = 0x98
MSG_MAIN_WATER_VALVE = 0x99
MSG_WASTE_VALVE = 0x9A
MSG_MAIN_VAC_VALVE = 0x9B
MSG_VACUUM_PUMP = 0x9C
MSG_WASTE_PUMP = 0x9D

RESP_UTILITY_STATUS = 0x83
RESP_ACK = 0xFF


@dataclass(frozen=True)
class UtilityStatus:
    """
    Mirrors the 'utility board' critical system-level state.

    The simulator currently models:
      - main valves / pumps bits in payload
      - error_status (0 == OK)
      - estop_ok is represented via safe_chain_ok
    """

    addr: int
    online: bool
    error_status: int

    # payload byte 0 (payload1)
    vacuum_valve: bool
    waste_valve: bool
    water_valve: bool
    hpn2_dump_valve: bool
    solvent_valve: bool
    n2_supply_valve: bool
    vacuum_pump: bool
    asp_level: bool

    # payload byte 1 (payload2)
    safe_chain_ok: bool
    waste_pump: bool


class UtilityBoardClient:
    """
    Thin client wrapper around protocol Frames.
    The bus is responsible for actual transport (sim now, uart later).
    """

    def __init__(self, addr: int) -> None:
        self.addr = addr

    def build_status_request(self) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_STATUS_REQ, payload=b"")

    def build_initialize(self) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_INITIALIZE, payload=b"")

    def build_stop(self) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_STOP, payload=b"")

    def build_main_solvent_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_MAIN_SOLVENT_VALVE, payload=bytes([1 if open_ else 0]))

    def build_main_n2_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_MAIN_N2_VALVE, payload=bytes([1 if open_ else 0]))

    def build_main_water_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_MAIN_WATER_VALVE, payload=bytes([1 if open_ else 0]))

    def build_waste_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_WASTE_VALVE, payload=bytes([1 if open_ else 0]))

    def build_main_vac_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_MAIN_VAC_VALVE, payload=bytes([1 if open_ else 0]))

    def build_vacuum_pump(self, on: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_VACUUM_PUMP, payload=bytes([1 if on else 0]))

    def build_waste_pump(self, on: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_WASTE_PUMP, payload=bytes([1 if on else 0]))

    @staticmethod
    def parse_status_response(frame: Frame) -> UtilityStatus | None:
        if frame.msg_type != RESP_UTILITY_STATUS:
            return None

        # Utility status response (SIM):
        # payload[0] = payload1 byte (main outputs + asp)
        # payload[1] = payload2 byte (safe_chain_ok + waste_pump)
        # payload[-1] = error_status
        if len(frame.payload) < 3:
            return None

        payload1 = frame.payload[0]
        payload2 = frame.payload[1]
        error_status = frame.payload[-1]

        return UtilityStatus(
            addr=frame.addr,
            online=True,
            error_status=error_status,
            vacuum_valve=bool(payload1 & (1 << 0)),
            waste_valve=bool(payload1 & (1 << 1)),
            water_valve=bool(payload1 & (1 << 2)),
            hpn2_dump_valve=bool(payload1 & (1 << 3)),
            solvent_valve=bool(payload1 & (1 << 4)),
            n2_supply_valve=bool(payload1 & (1 << 5)),
            vacuum_pump=bool(payload1 & (1 << 6)),
            asp_level=bool(payload1 & (1 << 7)),
            safe_chain_ok=bool(payload2 & (1 << 0)),
            waste_pump=bool(payload2 & (1 << 1)),
        )
