"""Core span data model for agent execution tracing."""

import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Span:
    """A single unit of work in an agent's execution trace.

    Spans form a tree via *parent_id*. Each span records timing, input/output,
    and metadata such as token counts and cost.
    """

    span_id: str = ""
    """Unique identifier for this span."""

    parent_id: str | None = None
    """ID of the parent span, or ``None`` for the root span."""

    name: str = ""
    """Human-readable name (e.g. ``"call_llm"``, ``"search_web"``)."""

    span_type: str = "agent"
    """Category: ``"agent"``, ``"llm"``, ``"tool"``, ``"thought"``."""

    start_time: float = 0.0
    """Unix timestamp when the span started."""

    end_time: float | None = None
    """Unix timestamp when the span finished."""

    input: str = ""
    """Input / prompt sent (truncated at 2000 chars in storage)."""

    output: str = ""
    """Output / response received."""

    token_count: int = 0
    """Total tokens used (prompt + completion), if known."""

    cost_usd: float = 0.0
    """Estimated cost in USD, if known."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Extra key-value data (model name, tool params, error info, etc.)."""

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def duration_ms(self) -> float:
        """Wall-clock duration in milliseconds, or 0 if still running."""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    @property
    def is_complete(self) -> bool:
        """Whether the span has finished."""
        return self.end_time is not None

    @property
    def timestamp_iso(self) -> str:
        """ISO-8601 timestamp of the start time."""
        return datetime.fromtimestamp(self.start_time, tz=UTC).isoformat()

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        span_type: str = "agent",
        parent_id: str | None = None,
        input: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "Span":
        """Create and start a new span with the current time."""
        return cls(
            span_id=uuid.uuid4().hex[:12],
            parent_id=parent_id,
            name=name,
            span_type=span_type,
            start_time=time.time(),
            input=input,
            metadata=metadata or {},
        )

    def finish(
        self,
        output: str = "",
        token_count: int = 0,
        cost_usd: float = 0.0,
        **extra_meta: Any,
    ) -> None:
        """Mark the span as completed with optional cost and token data."""
        self.end_time = time.time()
        self.output = output
        self.token_count = token_count
        self.cost_usd = cost_usd
        self.metadata.update(extra_meta)


class SpanTree:
    """Builds a tree of spans from a flat list for visualization.

    Args:
        spans: Flat list of Span objects (may be unsorted).
    """

    def __init__(self, spans: list[Span]) -> None:
        self._all = {s.span_id: s for s in spans}
        self._children: dict[str | None, list[Span]] = {}
        for s in spans:
            self._children.setdefault(s.parent_id, []).append(s)
        # Sort children by start time
        for pid in self._children:
            self._children[pid].sort(key=lambda x: x.start_time)

    @property
    def root(self) -> Span | None:
        """Return the root span (one with *parent_id* == ``None``)."""
        roots = self._children.get(None, [])
        return roots[0] if roots else None

    def children_of(self, span_id: str) -> list[Span]:
        """Return direct children of the given span ID."""
        return sorted(self._children.get(span_id, []), key=lambda s: s.start_time)

    def depth_of(self, span_id: str) -> int:
        """Return the nesting depth (0 for root)."""
        depth = 0
        while span_id in self._all:
            parent = self._all[span_id].parent_id
            if parent is None:
                break
            depth += 1
            span_id = parent
        return depth

    def walk(self) -> list[Span]:
        """Return spans in pre-order (root first, then children)."""
        result: list[Span] = []

        def _dfs(sid: str | None) -> None:
            for child in self._children.get(sid, []):
                result.append(child)
                _dfs(child.span_id)

        _dfs(None)
        return result

    def max_depth(self) -> int:
        """Return the maximum nesting depth across the tree."""
        if not self._all:
            return 0
        return max(self.depth_of(sid) for sid in self._all)

    def total_duration_ms(self) -> float:
        """Return the root span's duration, or 0 if no root."""
        root = self.root
        return root.duration_ms if root else 0.0
