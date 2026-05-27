"""Tests for the Span and SpanTree data models."""

import time

from agenttrace.span import Span, SpanTree


class TestSpan:
    def test_create_span(self) -> None:
        span = Span.create(name="test", span_type="tool", input="hello")
        assert span.name == "test"
        assert span.span_type == "tool"
        assert span.input == "hello"
        assert span.span_id != ""
        assert span.parent_id is None
        assert span.start_time > 0
        assert span.end_time is None

    def test_creates_unique_ids(self) -> None:
        s1 = Span.create("a")
        s2 = Span.create("b")
        assert s1.span_id != s2.span_id

    def test_finish_sets_end_time(self) -> None:
        span = Span.create("test")
        time.sleep(0.01)
        span.finish(output="done")
        assert span.end_time is not None
        assert span.duration_ms > 0
        assert span.output == "done"

    def test_duration_ms_for_running_span(self) -> None:
        span = Span.create("test")
        time.sleep(0.01)
        # Should use current time if not finished
        assert span.duration_ms > 0

    def test_is_complete(self) -> None:
        span = Span.create("test")
        assert not span.is_complete
        span.finish()
        assert span.is_complete

    def test_timestamp_iso(self) -> None:
        span = Span.create("test")
        assert "T" in span.timestamp_iso

    def test_finish_with_extra_metadata(self) -> None:
        span = Span.create("test")
        span.finish(output="done", model="gpt-4", temperature=0.5)
        assert span.metadata["model"] == "gpt-4"
        assert span.metadata["temperature"] == 0.5


class TestSpanTree:
    def test_empty_tree(self) -> None:
        tree = SpanTree([])
        assert tree.root is None
        assert tree.max_depth() == 0
        assert tree.walk() == []

    def test_single_span(self) -> None:
        root = Span.create("root")
        tree = SpanTree([root])
        assert tree.root is root
        assert tree.max_depth() == 0

    def test_parent_child(self) -> None:
        root = Span.create("root")
        root.span_id = "root"
        child = Span.create("child", parent_id="root")
        child.span_id = "child"

        tree = SpanTree([root, child])
        assert tree.root is root
        assert tree.children_of("root") == [child]
        assert tree.depth_of("child") == 1  # root is 0, child is 1

    def test_walk_order(self) -> None:
        root = Span.create("root")
        root.span_id = "1"
        child_a = Span.create("a", parent_id="1")
        child_a.span_id = "2"
        child_b = Span.create("b", parent_id="2")
        child_b.span_id = "3"

        tree = SpanTree([root, child_a, child_b])
        walked = tree.walk()
        assert len(walked) == 3

    def test_max_depth(self) -> None:
        root = Span.create("root")
        root.span_id = "1"
        child = Span.create("child", parent_id="1")
        child.span_id = "2"
        grandchild = Span.create("grandchild", parent_id="2")
        grandchild.span_id = "3"

        tree = SpanTree([root, child, grandchild])
        # depth_of for grandchild = 2
        assert tree.max_depth() >= 2

    def test_total_duration_ms(self) -> None:
        root = Span.create("root")
        root.finish()
        tree = SpanTree([root])
        assert tree.total_duration_ms() == root.duration_ms
