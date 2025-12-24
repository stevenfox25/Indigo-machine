from __future__ import annotations

from dataclasses import dataclass

from indigo.hw.protocol.codec import Frame

# ----------------------------
# Message / Response Types
# ----------------------------
MSG_STATUS_REQ = 0x20
MSG_RECOVER = 0x21
MSG_CYCLE = 0x22

MSG_LID = 0x30
MSG_ARM = 0x31

MSG_VAC_VALVE = 0x32
MSG_SOLVENT_VALVE = 0x33
MSG_WATER_VALVE = 0x34
MSG_N2_VALVE = 0x35
MSG_VENT = 0x36

MSG_STIR = 0x40
MSG_PRESSURE = 0x50

MSG_THERMAL = 0x60
MSG_REFLUX_ONLY = 0x61
MSG_THERMAL_ONLY = 0x62

MSG_CAL_PARAMS = 0x70

RESP_LANE_STATUS = 0x80
RESP_ACK = 0xFF


def _i16_from_le(b0: int, b1: int) -> int:
    v = b0 | (b1 << 8)
    if v & 0x8000:
        v = -((~v & 0xFFFF) + 1)
    return v


def _scaled_i16_100(b0: int, b1: int) -> float:
    return _i16_from_le(b0, b1) / 100.0


@dataclass(frozen=True)
class LaneStatus:
    addr: int
    online: bool
    error_status: int

    # payload group A (byte0): outputs
    cooling_valve_thermal: bool
    cooling_valve_reflux: bool
    cleaning_valve_water: bool
    cleaning_valve_solvent: bool
    vial_valve_n2: bool
    vial_valve_vac: bool
    lid_solenoid_down: bool
    lid_solenoid_up: bool

    # payload group B (byte1): outputs + inputs
    arm_solenoid_extend: bool
    arm_solenoid_retract: bool
    lid_switch_up: bool
    lid_switch_mid: bool
    lid_switch_down: bool
    arm_switch_retract: bool
    arm_switch_extend: bool
    heater_relay_on: bool

    # numeric values
    reflux_temp_c: float
    thermal_temp_c: float
    reflux_sp_c: float
    thermal_sp_c: float
    stir_speed_cmd: int
    pressure_raw: int  # keep raw int for now (you can define units later)
    stir_running: bool


class LaneboardClient:
    """
    SIM-first device client.
    Bus handles transport; we only build/parse Frames.

    Status payload format (SIM 2.6):
      byte0: outputs group A (matches old payload4Byte)
      byte1: outputs+inputs group B (matches old payload5Byte)
      byte2-3: reflux temp (i16, /100)
      byte4-5: thermal temp (i16, /100)
      byte6-7: reflux setpoint (i16, /100)
      byte8-9: thermal setpoint (i16, /100)
      byte10-11: stir speed commanded (u16)
      byte12-13: pressure raw (u16)
      byte14: stir running (0/1)
      byte15: error status (u8)
    Total: 16 bytes
    """

    def __init__(self, addr: int) -> None:
        self.addr = addr

    def build_status_request(self) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_STATUS_REQ, payload=b"")

    def build_recover(self) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_RECOVER, payload=b"")

    def build_cycle(self, action: int) -> Frame:
        # action: 0=stop, 1=start, 2=complete, 3=purge (future)
        return Frame(addr=self.addr, msg_type=MSG_CYCLE, payload=bytes([action & 0xFF]))

    def build_lid(self, extend: bool) -> Frame:
        # 0=retract, 1=extend
        return Frame(addr=self.addr, msg_type=MSG_LID, payload=bytes([1 if extend else 0]))

    def build_arm(self, extend: bool) -> Frame:
        # 0=retract, 1=extend
        return Frame(addr=self.addr, msg_type=MSG_ARM, payload=bytes([1 if extend else 0]))

    def build_vac_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_VAC_VALVE, payload=bytes([1 if open_ else 0]))

    def build_solvent_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_SOLVENT_VALVE, payload=bytes([1 if open_ else 0]))

    def build_water_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_WATER_VALVE, payload=bytes([1 if open_ else 0]))

    def build_n2_valve(self, open_: bool) -> Frame:
        return Frame(addr=self.addr, msg_type=MSG_N2_VALVE, payload=bytes([1 if open_ else 0]))

    def build_stir(self, on: bool, speed: int = 0) -> Frame:
        # payload: [on(0/1)][speed_lo][speed_hi]
        s = int(speed) & 0xFFFF
        return Frame(addr=self.addr, msg_type=MSG_STIR, payload=bytes([1 if on else 0, s & 0xFF, (s >> 8) & 0xFF]))

    @staticmethod
    def parse_status_response(frame: Frame) -> LaneStatus | None:
        if frame.msg_type != RESP_LANE_STATUS:
            return None
        if len(frame.payload) < 16:
            return None

        b0 = frame.payload[0]
        b1 = frame.payload[1]

        reflux_temp = _scaled_i16_100(frame.payload[2], frame.payload[3])
        thermal_temp = _scaled_i16_100(frame.payload[4], frame.payload[5])
        reflux_sp = _scaled_i16_100(frame.payload[6], frame.payload[7])
        thermal_sp = _scaled_i16_100(frame.payload[8], frame.payload[9])

        stir_speed = frame.payload[10] | (frame.payload[11] << 8)
        pressure_raw = frame.payload[12] | (frame.payload[13] << 8)
        stir_running = bool(frame.payload[14] & 1)
        error_status = frame.payload[15]

        return LaneStatus(
            addr=frame.addr,
            online=True,
            error_status=error_status,
            cooling_valve_thermal=bool(b0 & (1 << 0)),
            cooling_valve_reflux=bool(b0 & (1 << 1)),
            cleaning_valve_water=bool(b0 & (1 << 2)),
            cleaning_valve_solvent=bool(b0 & (1 << 3)),
            vial_valve_n2=bool(b0 & (1 << 4)),
            vial_valve_vac=bool(b0 & (1 << 5)),
            lid_solenoid_down=bool(b0 & (1 << 6)),
            lid_solenoid_up=bool(b0 & (1 << 7)),
            arm_solenoid_extend=bool(b1 & (1 << 0)),
            arm_solenoid_retract=bool(b1 & (1 << 1)),
            lid_switch_up=bool(b1 & (1 << 2)),
            lid_switch_mid=bool(b1 & (1 << 3)),
            lid_switch_down=bool(b1 & (1 << 4)),
            arm_switch_retract=bool(b1 & (1 << 5)),
            arm_switch_extend=bool(b1 & (1 << 6)),
            heater_relay_on=bool(b1 & (1 << 7)),
            reflux_temp_c=reflux_temp,
            thermal_temp_c=thermal_temp,
            reflux_sp_c=reflux_sp,
            thermal_sp_c=thermal_sp,
            stir_speed_cmd=stir_speed,
            pressure_raw=pressure_raw,
            stir_running=stir_running,
        )
