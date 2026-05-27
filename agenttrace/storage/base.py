"""Abstract base class for trace storage backends."""

from abc import ABC, abstractmethod

from agenttrace.span import Span


class StorageBackend(ABC):
    """Interface for storing and retrieving trace spans."""

    @abstractmethod
    def store(self, span: Span) -> None:
        """Persist a single span."""

    @abstractmethod
    def get_all(self) -> list[Span]:
        """Return all stored spans."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all spans from storage."""

    @abstractmethod
    def count(self) -> int:
        """Return the number of stored spans."""
