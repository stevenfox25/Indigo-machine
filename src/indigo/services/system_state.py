from __future__ import annotations

from dataclasses import dataclass

from indigo.hw.devices import UtilityStatus


@dataclass(frozen=True)
class SystemState:
    """
    Computed system readiness gate.

    Rule:
      - Utility board must be online
      - Utility board must have safe chain OK (e-stop chain OK)
      - Utility board error_status must be 0
    """

    system_ready: bool
    reason: str
    utility: UtilityStatus | None


def compute_system_state(utility: UtilityStatus | None) -> SystemState:
    if utility is None:
        return SystemState(system_ready=False, reason="UtilityBoard not detected", utility=None)
    if not utility.online:
        return SystemState(system_ready=False, reason="UtilityBoard offline", utility=utility)
    if utility.error_status != 0:
        return SystemState(system_ready=False, reason=f"UtilityBoard error_status={utility.error_status}", utility=utility)
    if not utility.safe_chain_ok:
        return SystemState(system_ready=False, reason="ESTOP / safety chain not OK", utility=utility)
    return SystemState(system_ready=True, reason="OK", utility=utility)
