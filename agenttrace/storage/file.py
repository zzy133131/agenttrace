"""File-based storage backend — persists spans as JSONL for cross-session analysis."""

import json
from pathlib import Path

from agenttrace.span import Span
from agenttrace.storage.base import StorageBackend


class FileStorage(StorageBackend):
    """Persists spans to a JSONL file.

    Each span is stored as one JSON line per row. Survives process restarts.

    Args:
        path: Directory path for the trace file. The file is named
            ``traces.jsonl`` within this directory.
    """

    def __init__(self, path: str | Path = "./trace_data") -> None:
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file = self._path / "traces.jsonl"

    def store(self, span: Span) -> None:
        with open(self._file, "a") as f:
            f.write(json.dumps(_span_to_dict(span), ensure_ascii=False) + "\n")

    def get_all(self) -> list[Span]:
        if not self._file.exists():
            return []
        spans: list[Span] = []
        with open(self._file) as f:
            for line in f:
                line = line.strip()
                if line:
                    spans.append(_dict_to_span(json.loads(line)))
        return spans

    def clear(self) -> None:
        if self._file.exists():
            self._file.unlink()

    def count(self) -> int:
        return len(self.get_all())


# ------------------------------------------------------------------
# Serialisation helpers
# ------------------------------------------------------------------


def _span_to_dict(span: Span) -> dict:
    return {
        "span_id": span.span_id,
        "parent_id": span.parent_id,
        "name": span.name,
        "span_type": span.span_type,
        "start_time": span.start_time,
        "end_time": span.end_time,
        "input": span.input[:2000],
        "output": span.output[:2000],
        "token_count": span.token_count,
        "cost_usd": span.cost_usd,
        "metadata": span.metadata,
    }


def _dict_to_span(data: dict) -> Span:
    return Span(
        span_id=data.get("span_id", ""),
        parent_id=data.get("parent_id"),
        name=data.get("name", ""),
        span_type=data.get("span_type", "agent"),
        start_time=data.get("start_time", 0.0),
        end_time=data.get("end_time"),
        input=data.get("input", ""),
        output=data.get("output", ""),
        token_count=data.get("token_count", 0),
        cost_usd=data.get("cost_usd", 0.0),
        metadata=data.get("metadata", {}),
    )
