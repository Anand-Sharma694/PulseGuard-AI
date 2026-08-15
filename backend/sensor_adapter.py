"""
Hardware integration contract.
Replace the simulator with ESP32/MAX30102 or another approved sensor source later.
The web application expects a BPM stream; hardware should POST JSON to the backend
or use a small gateway that converts sensor readings into BPM values.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass
class HeartRateReading:
    bpm: float
    timestamp: str

class HeartRateSource(Protocol):
    def read(self) -> HeartRateReading: ...

class SimulatedSource:
    """Reference source used by the browser demo. No hardware required."""
    pass
