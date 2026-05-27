"""Example: instrument an agent with AgentTrace to observe its execution.

Usage:
    python examples/basic_tracing.py
"""

import time

from agenttrace.exporter.console import ConsoleExporter
from agenttrace.tracer import Tracer


def main() -> None:
    tracer = Tracer("CustomerSupportBot")

    # Simulate an agent handling a customer query
    with tracer.span("handle_query", span_type="agent", input="Where is my order?") as root:
        # Step 1: Reasoning about the query
        with tracer.span("classify_intent", span_type="thought") as sp:
            time.sleep(0.05)
            sp.finish(output="Intent: order_status, sentiment: neutral")

        # Step 2: Look up order in database (simulated tool call)
        with tracer.span("query_database", span_type="tool", input="SELECT * FROM orders WHERE id=42") as sp:
            time.sleep(0.1)
            sp.finish(output="Order #42: shipped, tracking: TRK123", token_count=0, cost_usd=0.0)

        # Step 3: Call LLM to generate response
        with tracer.span("generate_response", span_type="llm", input="Order status: shipped, tracking: TRK123") as sp:
            time.sleep(0.2)
            sp.finish(
                output="Your order #42 has been shipped! Tracking number: TRK123",
                token_count=85,
                cost_usd=0.002,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
            )

        root.finish(output="Your order #42 has been shipped! Tracking number: TRK123")

    # Display the trace
    exporter = ConsoleExporter()
    exporter.export(tracer.spans)

    print(f"\nTotal tokens used: {tracer.total_tokens}")
    print(f"Total cost: ${tracer.total_cost:.6f}")
    print(f"Total duration: {tracer.total_duration_ms:.0f}ms")


if __name__ == "__main__":
    main()
