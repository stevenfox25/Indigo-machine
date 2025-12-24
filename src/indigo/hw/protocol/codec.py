from __future__ import annotations
from dataclasses import dataclass


PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class Frame:
    addr: int
    msg_type: int
    payload: bytes


# NOTE:
# The functions below are intentionally present for Phase 3 (UART/RS-485).
# SIM mode currently uses Frame objects directly and does not encode bytes.


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    poly = 0x1021
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def cobs_encode(data: bytes) -> bytes:
    if not data:
        return b"\x01"
    out = bytearray()
    idx = 0
    while idx < len(data):
        code_idx = len(out)
        out.append(0)
        code = 1
        while idx < len(data) and data[idx] != 0 and code < 0xFF:
            out.append(data[idx])
            idx += 1
            code += 1
        out[code_idx] = code
        if idx < len(data) and data[idx] == 0:
            idx += 1
    return bytes(out)


def cobs_decode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        code = data[i]
        if code == 0:
            raise ValueError("Invalid COBS (zero code)")
        i += 1
        for _ in range(code - 1):
            if i >= len(data):
                raise ValueError("Invalid COBS (overrun)")
            out.append(data[i])
            i += 1
        if code != 0xFF and i < len(data):
            out.append(0)
    return bytes(out)


def encode_frame(frame: Frame) -> bytes:
    # Placeholder for Phase 3 UART framing:
    # [ver][addr][type][len][payload...][crc_lo][crc_hi]
    payload_len = len(frame.payload)
    header = bytes([PROTOCOL_VERSION, frame.addr & 0xFF, frame.msg_type & 0xFF, payload_len & 0xFF])
    body = header + frame.payload
    crc = crc16_ccitt_false(body)
    raw = body + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    return cobs_encode(raw) + b"\x00"  # 0-delimited stream


def decode_frame(packet: bytes) -> Frame:
    if packet.endswith(b"\x00"):
        packet = packet[:-1]
    raw = cobs_decode(packet)
    if len(raw) < 6:
        raise ValueError("Frame too short")
    ver, addr, msg_type, payload_len = raw[0], raw[1], raw[2], raw[3]
    if ver != PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version {ver}")
    payload = raw[4 : 4 + payload_len]
    crc_lo = raw[4 + payload_len]
    crc_hi = raw[5 + payload_len]
    got_crc = crc_lo | (crc_hi << 8)
    calc_crc = crc16_ccitt_false(raw[: 4 + payload_len])
    if got_crc != calc_crc:
        raise ValueError("CRC mismatch")
    return Frame(addr=addr, msg_type=msg_type, payload=payload)
