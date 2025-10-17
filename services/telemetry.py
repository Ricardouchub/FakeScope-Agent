from __future__ import annotations

import traceback
from functools import lru_cache
from typing import Any

from loguru import logger

from config.settings import LangfuseConfig, get_settings

try:
    from langfuse import Langfuse
except Exception:  # pragma: no cover - optional dependency
    Langfuse = None  # type: ignore

try:
    from langfuse.langchain import CallbackHandler
except Exception:  # pragma: no cover
    CallbackHandler = None  # type: ignore


class TelemetryClient:
    def __init__(self, config: LangfuseConfig | dict[str, Any]) -> None:
        if isinstance(config, dict):
            config = LangfuseConfig.model_validate(config)
        self._handler = None
        self._client = None
        if not config.enabled:
            return
        if not config.public_key or not config.secret_key:
            logger.warning("Langfuse telemetry enabled but credentials missing.")
            return
        if CallbackHandler:
            try:
                self._handler = CallbackHandler(
                    public_key=config.public_key,
                    secret_key=config.secret_key,
                    base_url=config.host,
                    environment=config.environment,
                    release=config.release,
                )
                self._client = getattr(self._handler, "langfuse", None)
            except Exception as exc:
                logger.warning("Langfuse CallbackHandler init failed: %s", exc)
                self._handler = None
                self._client = None
        if not self._client and Langfuse:
            try:
                self._client = Langfuse(
                    public_key=config.public_key,
                    secret_key=config.secret_key,
                    host=config.host,
                    environment=config.environment,
                    release=config.release,
                )
            except Exception as exc:
                logger.warning("Langfuse client init failed: %s", exc)
                self._client = None

    def start_trace(self, name: str, **payload: Any):
        if not self._client:
            return None
        try:
            return self._client.trace(name=name, **payload)
        except Exception as exc:
            logger.warning("Langfuse start_trace failed: %s", exc)
            return None

    def log_event(self, trace: Any, name: str, **payload: Any) -> None:
        if not trace:
            return
        try:
            trace.event(name=name, **payload)
        except Exception as exc:
            logger.warning("Langfuse event log failed: %s", exc)

    def finish_trace(self, trace: Any, output: Any | None = None, error: BaseException | None = None) -> None:
        if not trace:
            return
        try:
            if error:
                trace.event(name="error", output={"message": str(error), "traceback": traceback.format_exc()})
                trace.update(status="error")
            elif output is not None:
                trace.event(name="result", output=output)
                trace.update(status="success")
            trace.end()
        except Exception as exc:
            logger.warning("Langfuse finish_trace failed: %s", exc)

    def flush(self) -> None:
        if not self._client:
            return
        flush = getattr(self._client, "flush", None)
        if callable(flush):
            try:
                flush()
            except Exception as exc:
                logger.warning("Langfuse flush failed: %s", exc)

    def handler(self):
        return self._handler


@lru_cache(maxsize=1)
def get_telemetry() -> TelemetryClient:
    settings = get_settings()
    return TelemetryClient(settings.langfuse)


__all__ = ["get_telemetry", "TelemetryClient"]
