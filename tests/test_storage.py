"""Tests for storage backends."""

import tempfile
from pathlib import Path

from agenttrace.span import Span
from agenttrace.storage.file import FileStorage
from agenttrace.storage.memory import InMemoryStorage


class TestInMemoryStorage:
    def setup_method(self) -> None:
        self.storage = InMemoryStorage()

    def test_store_and_get(self) -> None:
        span = Span.create("test")
        self.storage.store(span)
        assert self.storage.count() == 1
        assert self.storage.get_all()[0].span_id == span.span_id

    def test_clear(self) -> None:
        self.storage.store(Span.create("a"))
        self.storage.store(Span.create("b"))
        assert self.storage.count() == 2
        self.storage.clear()
        assert self.storage.count() == 0

    def test_get_all_returns_copy(self) -> None:
        s = Span.create("a")
        self.storage.store(s)
        spans = self.storage.get_all()
        spans.clear()
        assert self.storage.count() == 1  # original unaffected


class TestFileStorage:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.storage = FileStorage(self.tmpdir)

    def test_store_and_get(self) -> None:
        span = Span.create("file_test", span_type="llm", input="hello")
        span.finish(output="world", token_count=50)
        self.storage.store(span)

        loaded = self.storage.get_all()
        assert len(loaded) == 1
        assert loaded[0].name == "file_test"
        assert loaded[0].span_type == "llm"
        assert loaded[0].input == "hello"
        assert loaded[0].output == "world"
        assert loaded[0].token_count == 50

    def test_persistence(self) -> None:
        s1 = Span.create("first")
        s1.finish()
        self.storage.store(s1)

        # Create a new storage instance pointing to the same directory
        storage2 = FileStorage(self.tmpdir)
        assert storage2.count() == 1

    def test_clear(self) -> None:
        self.storage.store(Span.create("a"))
        assert self.storage.count() == 1
        self.storage.clear()
        assert self.storage.count() == 0

    def test_no_file_when_empty(self) -> None:
        assert self.storage.count() == 0

    def test_roundtrip_metadata(self) -> None:
        span = Span.create("meta_test", metadata={"key": "value", "num": 42})
        span.finish(output="done")
        self.storage.store(span)

        loaded = self.storage.get_all()
        assert loaded[0].metadata == {"key": "value", "num": 42}
