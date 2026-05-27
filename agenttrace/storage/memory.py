"""In-memory storage backend — keeps all spans in a list."""

from agenttrace.span import Span
from agenttrace.storage.base import StorageBackend


class InMemoryStorage(StorageBackend):
    """Stores spans in a Python list (ephemeral, lost on process exit)."""

    def __init__(self) -> None:
        self._spans: list[Span] = []

    def store(self, span: Span) -> None:
        self._spans.append(span)

    def get_all(self) -> list[Span]:
        return list(self._spans)

    def clear(self) -> None:
        self._spans.clear()

    def count(self) -> int:
        return len(self._spans)
