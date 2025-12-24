from __future__ import annotations

from abc import ABC, abstractmethod

from indigo.hw.protocol.codec import Frame


class Bus(ABC):
    @abstractmethod
    def send_and_recv(self, frame: Frame, timeout_s: float = 0.25) -> Frame | None:
        raise NotImplementedError
