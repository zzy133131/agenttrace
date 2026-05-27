"""Example: use the @trace decorator to instrument individual functions.

Usage:
    python examples/with_decorator.py
"""

import time

from agenttrace.exporter.console import ConsoleExporter
from agenttrace.tracer import Tracer
from agenttrace.wrapper import set_default_tracer, trace

# Create and set a global tracer
tracer = Tracer("DecoratedAgent")
set_default_tracer(tracer)


@trace(span_type="tool")
def search_database(query: str) -> str:
    """Simulate searching a database."""
    time.sleep(0.1)
    return f"Results for '{query}': item_1, item_2, item_3"


@trace(span_type="llm")
def call_llm(prompt: str) -> str:
    """Simulate calling an LLM."""
    time.sleep(0.2)
    return f"Generated response for: {prompt[:30]}..."


@trace(span_type="tool")
def save_to_file(content: str, filename: str) -> str:
    """Simulate saving to a file."""
    time.sleep(0.05)
    return f"Saved {len(content)} bytes to {filename}"


def main() -> None:
    with tracer.span("process_data_pipeline", span_type="agent") as root:
        results = search_database("active users")
        response = call_llm(f"Summarize these results: {results}")
        result = save_to_file(response, "output.txt")
        root.finish(output=result)

    exporter = ConsoleExporter()
    exporter.export(tracer.spans)

    print(f"\nTotal: {tracer.total_duration_ms:.0f}ms, ${tracer.total_cost:.6f}")


if __name__ == "__main__":
    main()
