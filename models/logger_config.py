from dataclasses import dataclass, field
from typing import List


@dataclass
class Request:
    """One polling request, e.g. Request("01 0C", 250)."""
    request: str
    interval_ms: int = 1000


@dataclass
class LoggerConfig:
    """Everything that goes into config.json. Defaults match the template."""
    version: int = 1
    bitrate: int = 500000
    address_bits: int = 11
    tx_id: str = "7DF"
    rx_id: str = "0"
    startup_delay_ms: int = 500
    run_duration_ms: int = 0
    response_timeout_ms: int = 70
    requests: List[Request] = field(default_factory=list)