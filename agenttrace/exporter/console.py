"""Console exporter — renders trace trees with timing and cost information."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from agenttrace.span import Span, SpanTree

console = Console()

# Colour mapping for span types
_TYPE_COLORS = {
    "agent": "bold blue",
    "llm": "bold green",
    "tool": "bold yellow",
    "thought": "bold magenta",
}

_TYPE_ICONS = {
    "agent": "🤖",
    "llm": "🧠",
    "tool": "🔧",
    "thought": "💭",
}


class ConsoleExporter:
    """Renders a trace tree to the terminal using Rich."""

    def export(self, spans: list[Span]) -> None:
        """Print a formatted trace report for the given spans."""
        if not spans:
            console.print("[dim]No spans to display.[/]")
            return

        tree = SpanTree(spans)
        root = tree.root
        if root is None:
            console.print("[dim]No root span found.[/]")
            return

        # Summary panel
        summary = (
            f"[bold]Trace:[/] {root.name}\n"
            f"[bold]Duration:[/] {root.duration_ms:.0f} ms\n"
            f"[bold]Spans:[/] {len(spans)}\n"
            f"[bold]Total Tokens:[/] {sum(s.token_count for s in spans)}\n"
            f"[bold]Total Cost:[/] [yellow]${sum(s.cost_usd for s in spans):.6f}[/]"
        )
        console.print(Panel(summary, title="[bold]Agent Trace[/]", border_style="blue"))
        console.print("")

        # Tree view
        rich_tree = Tree(f"[bold]{_label(root)}[/]")
        self._build_tree(tree, root, rich_tree)
        console.print(rich_tree)

        # Detailed table
        self._print_details(spans)

    def _build_tree(self, tree_model: SpanTree, node: Span, rich_node: Tree) -> None:
        """Recursively build the Rich Tree."""
        for child in tree_model.children_of(node.span_id):
            child_node = rich_node.add(_label(child))
            self._build_tree(tree_model, child, child_node)

    def _print_details(self, spans: list[Span]) -> None:
        """Print a detailed table of all spans."""
        table = Table(title="Span Details", show_lines=True)
        table.add_column("Span", width=28)
        table.add_column("Type", width=10)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Tokens", justify="right", width=8)
        table.add_column("Cost", justify="right", width=10)

        for s in spans:
            table.add_row(
                s.name,
                s.span_type,
                f"{s.duration_ms:.0f}ms",
                str(s.token_count) if s.token_count else "-",
                f"${s.cost_usd:.6f}" if s.cost_usd else "-",
            )

        console.print("\n")
        console.print(table)


def _label(span: Span) -> str:
    """Format a span label for tree display."""
    icon = _TYPE_ICONS.get(span.span_type, "•")
    color = _TYPE_COLORS.get(span.span_type, "white")
    duration = f"[dim]{span.duration_ms:.0f}ms[/]"
    cost = f"[yellow]${span.cost_usd:.4f}[/]" if span.cost_usd else ""
    parts = [f"[{color}]{icon} {span.name}[/]", duration]
    if cost:
        parts.append(cost)
    if span.token_count:
        parts.append(f"[dim]({span.token_count} tok)[/]")
    return " ".join(parts)
