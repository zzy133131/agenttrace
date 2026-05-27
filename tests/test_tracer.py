"""Tests for the Tracer class."""

import time

from agenttrace.tracer import Tracer


class TestTracer:
    def test_start_and_end(self) -> None:
        tracer = Tracer("test")
        span = tracer.start("operation", span_type="tool", input="data")
        assert span.name == "operation"
        assert span.span_type == "tool"
        assert tracer.is_active

        time.sleep(0.01)
        finished = tracer.end(output="result")
        assert finished.is_complete
        assert finished.output == "result"
        assert not tracer.is_active

    def test_context_manager(self) -> None:
        tracer = Tracer("test")
        with tracer.span("ctx_test", span_type="llm", input="hello") as span:
            assert tracer.is_active
            span.finish(output="world")

        assert not tracer.is_active
        assert span.is_complete
        assert span.output == "world"

    def test_nested_spans(self) -> None:
        tracer = Tracer("nested")
        with tracer.span("root") as root:
            with tracer.span("child") as child:
                child.finish()
            root.finish()

        # Both should be in storage
        assert len(tracer.spans) == 2

    def test_auto_finish_on_exception(self) -> None:
        tracer = Tracer("test")
        try:
            with tracer.span("will_fail"):
                msg = "error!"  # noqa: F841
                1 / 0
        except ZeroDivisionError:
            pass

        assert not tracer.is_active
        assert len(tracer.spans) == 1
        assert tracer.spans[0].is_complete

    def test_clear(self) -> None:
        tracer = Tracer("test")
        with tracer.span("a") as s:
            s.finish()
        assert len(tracer.spans) == 1
        tracer.clear()
        assert len(tracer.spans) == 0
        assert not tracer.is_active

    def test_convenience_methods(self) -> None:
        tracer = Tracer("test")
        s1 = tracer.trace_llm("llm", "prompt")
        s1.finish()
        assert s1.span_type == "llm"
        assert s1.input == "prompt"

        s2 = tracer.trace_tool("tool", "query")
        s2.finish()
        assert s2.span_type == "tool"

        s3 = tracer.trace_thought("think")
        s3.finish()
        assert s3.span_type == "thought"

    def test_current_span(self) -> None:
        tracer = Tracer("test")
        assert tracer.current_span is None
        span = tracer.start("a")
        assert tracer.current_span is span
        tracer.end()
        assert tracer.current_span is None

    def test_total_aggregation(self) -> None:
        tracer = Tracer("test")
        with tracer.span("a") as s:
            s.finish(token_count=100, cost_usd=0.001)
        with tracer.span("b") as s:
            s.finish(token_count=200, cost_usd=0.002)

        assert tracer.total_tokens == 300
        assert tracer.total_cost == 0.003

    def test_disabled_tracer(self) -> None:
        tracer = Tracer("test", enabled=False)
        # Even if disabled, the tracer should still work
        with tracer.span("a") as s:
            s.finish()
        assert len(tracer.spans) == 1
