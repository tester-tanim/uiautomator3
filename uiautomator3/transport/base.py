"""Transport abstraction.

The public client/device API must never depend on a concrete transport
backend directly - only on this protocol. This is what lets the wire
protocol evolve (e.g. HTTP/JSON-RPC today, WebSocket push later) without a
public API break. See docs/UIAUTOMATOR3_ARCHITECTURE.md section 14.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Transport(ABC):
    """Base interface every transport backend must implement."""

    @abstractmethod
    def connect(self) -> None:
        """Establish the underlying connection."""

    @abstractmethod
    def close(self) -> None:
        """Tear down the underlying connection."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether the transport is currently usable."""

    @abstractmethod
    def request(self, method: str, params: Optional[dict] = None, timeout: Optional[float] = None) -> Any:
        """Issue a request and return the decoded result."""
