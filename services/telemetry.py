from __future__ import annotations

import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Optional

from loguru import logger

from config.settings import LangfuseConfig, get_settings

try:
    from langfuse import Langfuse
    from langfuse.api.resources.ingestion.types import (
        CreateEventBody,
        IngestionEvent_EventCreate,
        IngestionEvent_ScoreCreate,
        IngestionEvent_TraceCreate,
        ScoreBody,
        TraceBody,
    )
except Exception:  # pragma: no cover - optional dependency
    Langfuse = None  # type: ignore
    IngestionEvent_EventCreate = None  # type: ignore
    IngestionEvent_TraceCreate = None  # type: ignore
    IngestionEvent_ScoreCreate = None  # type: ignore
    TraceBody = None  # type: ignore
    CreateEventBody = None  # type: ignore
    ScoreBody = None  # type: ignore


class TelemetryTrace:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id


class TelemetryClient:
    def __init__(self, config: LangfuseConfig | dict[str, Any]) -> None:
        if isinstance(config, dict):
            config = LangfuseConfig.model_validate(config)
        self._config = config
        self._client: Optional[Langfuse] = None
        if not config.enabled:
            logger.debug("Langfuse telemetry disabled via settings.")
            return
        if not Langfuse or not IngestionEvent_TraceCreate or not CreateEventBody:
            logger.warning("Langfuse SDK not available; telemetry disabled.")
            return
        if not config.public_key or not config.secret_key:
            logger.warning("Langfuse telemetry enabled but credentials missing.")
            return
        try:
            self._client = Langfuse(
                public_key=config.public_key,
                secret_key=config.secret_key,
                host=config.host,
                environment=config.environment,
                release=config.release,
            )
            logger.debug("Initialized Langfuse client for telemetry.")
        except Exception as exc:  # pragma: no cover - network/credential issues
            logger.warning("Langfuse client init failed: %s", exc)
            self._client = None

    def _send(self, events: list[Any]) -> None:
        if not self._client or not events:
            return
        try:
            self._client.api.ingestion.batch(batch=events)
        except Exception as exc:
            logger.warning("Langfuse ingestion failed: %s", exc)

    def start_trace(self, name: str, **payload: Any) -> Optional[TelemetryTrace]:
        if not self._client:
            return None
        now = datetime.now(UTC)
        trace_id = str(uuid.uuid4())
        trace_body = TraceBody(
            id=trace_id,
            name=name,
            timestamp=now,
            input=payload.get("input"),
            metadata=payload.get("metadata"),
            environment=self._config.environment,
            release=self._config.release or None,
        )
        event = IngestionEvent_TraceCreate(
            id=str(uuid.uuid4()),
            timestamp=now.isoformat(),
            body=trace_body,
        )
        self._send([event])
        return TelemetryTrace(trace_id)

    def log_event(self, trace: Optional[TelemetryTrace], name: str, **payload: Any) -> None:
        if not trace or not self._client or not IngestionEvent_EventCreate:
            return
        now = datetime.now(UTC)
        event_body = CreateEventBody(
            traceId=trace.trace_id,
            name=name,
            metadata=payload.get("metadata"),
            input=payload.get("input"),
            output=payload.get("output"),
            environment=self._config.environment,
        )
        event = IngestionEvent_EventCreate(
            id=str(uuid.uuid4()),
            timestamp=now.isoformat(),
            body=event_body,
        )
        self._send([event])

    def log_score(
        self,
        trace: Optional[TelemetryTrace],
        name: str,
        value: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not trace:
            return
        self.log_score_by_id(trace.trace_id, name=name, value=value, metadata=metadata)

    def log_score_by_id(
        self,
        trace_id: Optional[str],
        name: str,
        value: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not trace_id or not self._client or not IngestionEvent_ScoreCreate:
            return
        now = datetime.now(UTC)
        score_body = ScoreBody(
            traceId=trace_id,
            name=name,
            value=value,
            metadata=metadata,
            environment=self._config.environment,
        )
        event = IngestionEvent_ScoreCreate(
            id=str(uuid.uuid4()),
            timestamp=now.isoformat(),
            body=score_body,
        )
        self._send([event])

    def finish_trace(
        self,
        trace: Optional[TelemetryTrace],
        output: Any | None = None,
        error: BaseException | None = None,
    ) -> None:
        if not trace or not self._client:
            return
        now = datetime.now(UTC)
        body = TraceBody(
            id=trace.trace_id,
            timestamp=now,
            output={"error": str(error)} if error else output,
            environment=self._config.environment,
            release=self._config.release or None,
        )
        event = IngestionEvent_TraceCreate(
            id=str(uuid.uuid4()),
            timestamp=now.isoformat(),
            body=body,
        )
        self._send([event])

    def flush(self) -> None:
        return

    def handler(self):
        return None


@lru_cache(maxsize=1)
def get_telemetry() -> TelemetryClient:
    settings = get_settings()
    return TelemetryClient(settings.langfuse)


__all__ = ["get_telemetry", "TelemetryClient", "TelemetryTrace"]
