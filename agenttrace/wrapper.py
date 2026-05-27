"""Decorator and wrapper utilities for instrumenting agent functions with tracing."""

import functools
from typing import Any, Callable, TypeVar

from agenttrace.tracer import Tracer

F = TypeVar("F", bound=Callable[..., Any])

# Global default tracer for use with the @trace decorator
_default_tracer: Tracer | None = None


def set_default_tracer(tracer: Tracer) -> None:
    """Set the global default tracer used by the ``@trace`` decorator."""
    global _default_tracer
    _default_tracer = tracer


def get_default_tracer() -> Tracer:
    """Return the global default tracer, creating one if needed."""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = Tracer("default")
    return _default_tracer


def trace(
    name: str | None = None,
    span_type: str = "tool",
    tracer: Tracer | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function with automatic tracing.

    Usage::

        @trace(span_type="tool")
        def search_web(query: str) -> str:
            ...

    The decorated function's return value becomes the span's output, and
    its keyword arguments are stored as span metadata.

    Args:
        name: Span name (defaults to the function's ``__name__``).
        span_type: Category for the span.
        tracer: Tracer instance (defaults to the global default tracer).
    """
    def decorator(func: F) -> F:
        span_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            t = tracer or get_default_tracer()
            input_preview = _preview(args, kwargs)
            with t.span(span_name, span_type=span_type, input=input_preview) as sp:
                try:
                    result = func(*args, **kwargs)
                    sp.finish(output=str(result)[:2000])
                    return result
                except Exception as exc:
                    sp.finish(output=f"Error: {exc}", error=str(exc))
                    raise

        return wrapper  # type: ignore[return-value]

    return decorator


def _preview(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Create a short string preview of positional and keyword arguments."""
    parts: list[str] = []
    for a in args:
        parts.append(str(a)[:200])
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    return ", ".join(parts)[:2000]
