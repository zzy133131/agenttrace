"""Example: generate an interactive HTML timeline visualization of a trace.

Usage:
    python examples/html_report.py
"""

import time

from agenttrace.exporter.html import HtmlExporter
from agenttrace.storage.file import FileStorage
from agenttrace.tracer import Tracer


def main() -> None:
    # Use file storage so the trace persists
    tracer = Tracer("ResearchAgent", storage=FileStorage("./trace_data"))

    with tracer.span("research_topic", span_type="agent", input="Latest AI advancements in 2024") as root:
        with tracer.span("search_web", span_type="tool", input="AI advancements 2024") as sp:
            time.sleep(0.1)
            sp.finish(
                output="Found 15 results about AI advancements",
                token_count=0,
                cost_usd=0.0,
                source="web",
                results_count=15,
            )

        with tracer.span("summarize_findings", span_type="llm", input="15 search results about AI") as sp:
            time.sleep(0.3)
            sp.finish(
                output="Key advancements: multi-modal models, agent frameworks, code generation",
                token_count=250,
                cost_usd=0.005,
                model="claude-opus-4-20250514",
                temperature=0.2,
            )

        with tracer.span("verify_sources", span_type="thought") as sp:
            time.sleep(0.05)
            sp.finish(output="All sources verified, no conflicts found")

        with tracer.span("write_report", span_type="llm", input="Write a brief research summary") as sp:
            time.sleep(0.4)
            sp.finish(
                output="2024 saw major advances in multi-modal AI, autonomous agents, and code generation...",
                token_count=500,
                cost_usd=0.01,
                model="claude-sonnet-4-20250514",
                section="introduction",
            )

        root.finish(output="Research complete. Report generated.")

    # Generate interactive HTML timeline
    exporter = HtmlExporter()
    path = exporter.export(tracer.spans, "research_trace.html")
    print(f"HTML trace report: {path.resolve()}")

    # Show summary
    print(f"Total spans: {len(tracer.spans)}")
    print(f"Total cost: ${tracer.total_cost:.6f}")
    print(f"Total tokens: {tracer.total_tokens}")
    print(f"Duration: {tracer.total_duration_ms:.0f}ms")


if __name__ == "__main__":
    main()
