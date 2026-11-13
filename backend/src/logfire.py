import os
from collections.abc import Sequence
from typing import TYPE_CHECKING, Callable

import httpx
import logfire
from fastapi import FastAPI
from loguru import logger as loguru_logger
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    ParentBased,
    Sampler,
    SamplingResult,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from src.config import settings

if TYPE_CHECKING:
    from opentelemetry.context import Context
    from opentelemetry.trace import Link, SpanKind
    from opentelemetry.trace.span import TraceState
    from opentelemetry.util.types import Attributes

Matcher = Callable[[str, "Attributes | None"], bool]


class IgnoreSampler(Sampler):
    """Drops spans (and so their whole trace) that any matcher matches."""

    def __init__(self, matchers: Sequence[Matcher]) -> None:
        super().__init__()
        self.matchers = matchers

    def should_sample(
        self,
        parent_context: "Context | None",
        trace_id: int,
        name: str,
        kind: "SpanKind | None" = None,
        attributes: "Attributes | None" = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState | None" = None,
    ) -> SamplingResult:
        ignored = any(matcher(name, attributes) for matcher in self.matchers)
        sampler = ALWAYS_OFF if ignored else ALWAYS_ON
        return sampler.should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state
        )

    def get_description(self) -> str:
        return "IgnoreSampler"


def _healthz_matcher(name: str, attributes: "Attributes | None") -> bool:
    return attributes is not None and attributes.get("http.route") in ("", "/health")


def _sqlalchemy_connect_matcher(name: str, attributes: "Attributes | None") -> bool:
    # One "connect" span per pooled connection checkout: noise inside every request.
    return name == "connect"


def _head_sampler() -> Sampler:
    return ParentBased(
        # Root spans (a new request, a background task): drop health checks.
        IgnoreSampler((_healthz_matcher, _sqlalchemy_connect_matcher)),
        # Child spans of a sampled parent: drop only connect spans.
        local_parent_sampled=IgnoreSampler((_sqlalchemy_connect_matcher,)),
    )


def configure_logfire() -> None:
    if settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT:
        os.environ.setdefault(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
        )

    logfire.configure(
        send_to_logfire="if-token-present",
        token=None,
        service_name=settings.SERVICE_NAME,
        environment=settings.APP_ENV,
        min_level=settings.LOGFIRE_MIN_LEVEL,
        console=logfire.ConsoleOptions(),
        sampling=logfire.SamplingOptions(head=_head_sampler()),
        distributed_tracing=False,
    )

    # Spans for pydantic-ai agents (the facts agent) and their model calls.
    logfire.instrument_pydantic_ai()
    # Spans for MCP tool calls.
    logfire.instrument_mcp()
    # Pipecat logs through loguru; send those logs to Logfire too.
    loguru_logger.configure(handlers=[logfire.loguru_handler()])


def instrument_fastapi(app: FastAPI) -> None:
    logfire.instrument_fastapi(app)


def instrument_sqlalchemy(engine: AsyncEngine) -> None:
    """Instrument one engine. Called where the engine is created, because
    instrumenting globally only patches engines created after the call."""
    logfire.instrument_sqlalchemy(engine=engine, skip_dep_check=True)


def instrument_httpx(client: httpx.AsyncClient | httpx.Client | None = None) -> None:
    """Without a client, instruments every httpx client (including the OpenAI and
    Anthropic SDKs). Headers and bodies are not captured."""
    if client is not None:
        logfire.instrument_httpx(client=client)
    else:
        logfire.instrument_httpx()


__all__ = [
    "configure_logfire",
    "instrument_fastapi",
    "instrument_httpx",
    "instrument_sqlalchemy",
]
