"""Main tracer — instruments AI agent execution with span-based tracing."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from agenttrace.span import Span
from agenttrace.storage.base import StorageBackend
from agenttrace.storage.memory import InMemoryStorage


class Tracer:
    """Instruments agent execution by creating and managing spans.

    Typical usage::

        tracer = Tracer("my_agent")

        with tracer.span("process_query", span_type="agent") as root:
            with tracer.span("call_llm", span_type="llm") as llm_span:
                response = llm.generate(prompt)
                llm_span.finish(token_count=150, cost_usd=0.003)

            with tracer.span("search_web", span_type="tool") as tool_span:
                result = web_search(query)
                tool_span.finish(output=result)

    Args:
        name: Name for this tracer (typically the agent name).
        storage: Backend for storing completed spans. Defaults to
            in-memory storage.
        enabled: Set to ``False`` to disable tracing (useful in production).
    """

    def __init__(
        self,
        name: str = "agent",
        storage: StorageBackend | None = None,
        enabled: bool = True,
    ) -> None:
        self.name = name
        self.storage = storage or InMemoryStorage()
        self.enabled = enabled
        self._stack: list[Span] = []

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def start(
        self,
        name: str,
        span_type: str = "agent",
        input: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Span:
        """Begin a new span as a child of the current span (if any)."""
        parent_id = self._stack[-1].span_id if self._stack else None
        span = Span.create(
            name=name,
            span_type=span_type,
            parent_id=parent_id,
            input=input,
            metadata=metadata,
        )
        self._stack.append(span)
        self.storage.store(span)
        return span

    def end(self, output: str = "", **extra_meta: Any) -> Span:
        """Finish the current span and pop it from the stack.

        Returns the completed span.
        """
        span = self._stack.pop()
        span.finish(output=output, **extra_meta)
        return span

    @contextmanager
    def span(
        self,
        name: str,
        span_type: str = "agent",
        input: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[Span]:
        """Context manager that creates and automatically finishes a span.

        Usage::

            with tracer.span("search_db", span_type="tool", input=query) as sp:
                result = db.query(query)
                sp.finish(output=str(result))
        """
        span = self.start(name, span_type, input, metadata)
        try:
            yield span
        finally:
            if self._stack and self._stack[-1] is span:
                self._stack.pop()
            if not span.is_complete:
                span.finish()
            # span is already stored - no need to re-store

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def trace_llm(self, name: str = "llm_call", input: str = "") -> Span:
        """Start an LLM call span."""
        return self.start(name, span_type="llm", input=input)

    def trace_tool(self, name: str, input: str = "") -> Span:
        """Start a tool execution span."""
        return self.start(name, span_type="tool", input=input)

    def trace_thought(self, name: str = "reasoning", input: str = "") -> Span:
        """Start a reasoning / thought span."""
        return self.start(name, span_type="thought", input=input)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def spans(self) -> list[Span]:
        """Return all stored spans."""
        return self.storage.get_all()

    @property
    def current_span(self) -> Span | None:
        """Return the currently active span, or ``None``."""
        return self._stack[-1] if self._stack else None

    @property
    def is_active(self) -> bool:
        """Whether a span is currently being traced."""
        return len(self._stack) > 0

    def clear(self) -> None:
        """Remove all stored spans."""
        self.storage.clear()
        self._stack.clear()

    @property
    def total_cost(self) -> float:
        """Sum of *cost_usd* across all spans."""
        return sum(s.cost_usd for s in self.spans)

    @property
    def total_tokens(self) -> int:
        """Sum of *token_count* across all spans."""
        return sum(s.token_count for s in self.spans)

    @property
    def total_duration_ms(self) -> float:
        """Total wall-clock time from the first to the last span's end."""
        spans = self.spans
        if not spans:
            return 0.0
        t_min = min(s.start_time for s in spans)
        t_max = max((s.end_time or t_min) for s in spans)
        return (t_max - t_min) * 1000
