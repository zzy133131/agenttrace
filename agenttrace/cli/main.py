"""AgentTrace CLI — view, export, and manage trace data from the terminal."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from agenttrace.exporter.console import ConsoleExporter
from agenttrace.exporter.html import HtmlExporter
from agenttrace.storage.file import FileStorage
from agenttrace.tracer import Tracer

app = typer.Typer(help="AgentTrace — observability and tracing for AI agents.")
console = Console()


@app.command()
def view(
    data_dir: str = typer.Option("./trace_data", "--data", "-d", help="Trace data directory"),
    html: bool = typer.Option(False, "--html", help="Generate HTML timeline instead of console view"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for HTML report"),
) -> None:
    """View the most recent trace."""
    storage = FileStorage(data_dir)
    spans = storage.get_all()

    if not spans:
        rprint("[yellow]No trace data found.[/]")
        rprint(f"  Looked in: {data_dir}")
        raise typer.Exit(0)

    # Group spans by root for multi-trace support (simplified: show all as one)
    if html:
        exporter = HtmlExporter()
        out = Path(output or "trace_report.html")
        exporter.export(spans, out)
        rprint(f"[green]HTML trace report saved to:[/] {out.resolve()}")
    else:
        exporter = ConsoleExporter()
        exporter.export(spans)

    rprint(f"\n[dim]Source: {data_dir}/traces.jsonl ({len(spans)} spans)[/]")


@app.command()
def simulate() -> None:
    """Generate a simulated trace to demonstrate AgentTrace's capabilities."""
    tracer = Tracer("DemoAgent", storage=FileStorage("./trace_data"))

    with tracer.span("answer_question", span_type="agent", input="What is the capital of France?") as root:
        with tracer.span("decompose_task", span_type="thought", input="Break down the question") as thought:
            thought.finish(output="Need to: 1) recall facts 2) verify 3) respond")

        with tracer.span("search_memory", span_type="tool", input="query: capital of France") as mem:
            mem.finish(output="Paris", token_count=50, cost_usd=0.001)

        with tracer.span("verify_fact", span_type="llm", input="Confirm: Paris is capital of France") as llm:
            llm.finish(
                output="Paris is the capital and largest city of France.",
                token_count=120,
                cost_usd=0.002,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
            )

        with tracer.span("format_response", span_type="thought") as fmt:
            fmt.finish(output="Capital of France is Paris.")

        root.finish(output="The capital of France is Paris.", token_count=170, cost_usd=0.003)

    rprint("[green]Demo trace generated![/]")
    rprint("  Run [bold]agenttrace view[/] to see it.")

    # Also show CLI
    exporter = ConsoleExporter()
    exporter.export(tracer.spans)


@app.command()
def info(
    data_dir: str = typer.Option("./trace_data", "--data", "-d", help="Trace data directory"),
) -> None:
    """Show summary information about stored trace data."""
    storage = FileStorage(data_dir)
    spans = storage.get_all()

    if not spans:
        rprint("[yellow]No trace data found.[/]")
        return

    total_cost = sum(s.cost_usd for s in spans)
    total_tokens = sum(s.token_count for s in spans)
    type_counts: dict[str, int] = {}
    for s in spans:
        type_counts[s.span_type] = type_counts.get(s.span_type, 0) + 1

    table = Table(title="Trace Data Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Total spans", str(len(spans)))
    table.add_row("Span types", ", ".join(f"{k}={v}" for k, v in type_counts.items()))
    table.add_row("Total tokens", str(total_tokens))
    table.add_row("Total cost", f"${total_cost:.6f}")
    table.add_row("Data directory", data_dir)

    # Earliest and latest timestamps
    start_times = [s.start_time for s in spans if s.start_time]
    if start_times:
        from datetime import UTC, datetime

        table.add_row("Earliest span", datetime.fromtimestamp(min(start_times), tz=UTC).isoformat())
        table.add_row("Latest span", datetime.fromtimestamp(max(start_times), tz=UTC).isoformat())

    console.print(table)


@app.command()
def clear(data_dir: str = typer.Option("./trace_data", "--data", "-d", help="Trace data directory")) -> None:
    """Clear all stored trace data."""
    storage = FileStorage(data_dir)
    count = storage.count()
    storage.clear()
    rprint(f"[green]Cleared {count} spans from {data_dir}[/]")


@app.command()
def export(
    data_dir: str = typer.Option("./trace_data", "--data", "-d", help="Trace data directory"),
    output: str = typer.Option("trace_export.json", "--output", "-o", help="Output JSON file path"),
) -> None:
    """Export trace data as a JSON file."""
    storage = FileStorage(data_dir)
    spans = storage.get_all()

    data = [
        {
            "span_id": s.span_id,
            "parent_id": s.parent_id,
            "name": s.name,
            "span_type": s.span_type,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration_ms": s.duration_ms,
            "input": s.input[:500],
            "output": s.output[:500],
            "token_count": s.token_count,
            "cost_usd": s.cost_usd,
            "metadata": s.metadata,
        }
        for s in spans
    ]

    with open(output, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    rprint(f"[green]Exported {len(spans)} spans to {output}[/]")


if __name__ == "__main__":
    app()
