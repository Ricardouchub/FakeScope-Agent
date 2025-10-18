from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass
class TelemetryTrace:
    run_id: str


class TelemetryClient:
    def __init__(self, config: Any | None = None) -> None:
        self.enabled = False

    def start_trace(self, name: str, **payload: Any) -> None:
        return None

    def log_event(self, trace: Any, name: str, **payload: Any) -> None:
        return

    def log_score_by_id(
        self,
        run_id: str | None,
        name: str,
        value: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        return

    def log_score(
        self,
        trace: Any,
        name: str,
        value: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        return

    def finish_trace(self, trace: Any, output: Any | None = None, error: BaseException | None = None) -> None:
        return

    def latest_run_id(self) -> None:
        return None

    def flush(self) -> None:
        return

    def handler(self):
        return None


@lru_cache(maxsize=1)
def get_telemetry() -> TelemetryClient:
    return TelemetryClient(None)


__all__ = ["get_telemetry", "TelemetryClient", "TelemetryTrace"]
