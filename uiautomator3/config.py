"""Global configuration for UIAutomator 3.0.

Kept intentionally small for Phase 1 - only the settings needed by the
transport/adb/device layers. Later phases (waits, healing, inspector) will
extend this rather than replace it.
"""

from dataclasses import dataclass


@dataclass
class Config:
    connect_timeout: float = 10.0
    request_timeout: float = 20.0
    log_level: str = "INFO"
    agent_port: int = 9008


_config = Config()


def get_config() -> Config:
    return _config


def set_config(config: Config) -> None:
    global _config
    _config = config
