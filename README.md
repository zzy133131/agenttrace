# AgentTrace

## Project Introduction / 项目介绍

**English:** AgentTrace is an observability and tracing toolkit for AI agent execution. It helps developers understand, debug, and optimize agents by capturing detailed traces for LLM calls, tool invocations, reasoning steps, timing, cost, and token usage.

**中文：** AgentTrace 是一个面向 AI 智能体执行过程的可观测性与追踪工具包。它可以记录 LLM 调用、工具调用、推理步骤、耗时、成本和 token 使用情况，帮助开发者理解、调试并优化智能体工作流。

## Features

- **Span-Based Tracing** — Record every step of agent execution as a tree of spans
- **Context Manager API** — Clean `with tracer.span(...)` syntax for instrumenting code
- **`@trace` Decorator** — One-line instrumentation of any function
- **Console Visualiser** — Rich terminal output with tree view and details table
- **HTML Timeline** — Self-contained interactive Gantt-chart visualisation
- **Cost & Token Tracking** — Track estimated costs and token usage per span
- **Persistent Storage** — File-based JSONL storage for cross-session analysis
- **CLI Interface** — View, export, simulate, and manage traces from the terminal

## Quick Start

```bash
# Install from source
cd agenttrace
pip install -e .
```

### Basic Tracing

```python
from agenttrace.tracer import Tracer
from agenttrace.exporter.console import ConsoleExporter

tracer = Tracer("MyAgent")

with tracer.span("handle_query", span_type="agent", input="What's the weather?") as root:
    with tracer.span("call_weather_api", span_type="tool", input="London") as tool:
        tool.finish(output="22°C, partly cloudy")

    with tracer.span("generate_response", span_type="llm", input="Weather: 22°C") as llm:
        llm.finish(output="It's 22°C and partly cloudy in London.",
                   token_count=45, cost_usd=0.001,
                   metadata={"model": "claude-sonnet-4-20250514"})

    root.finish(output="It's 22°C and partly cloudy in London.")

ConsoleExporter().export(tracer.spans)
```

### Using the @trace Decorator

```python
from agenttrace.tracer import Tracer
from agenttrace.wrapper import set_default_tracer, trace

tracer = Tracer("MyAgent")
set_default_tracer(tracer)

@trace(span_type="tool")
def search_database(query: str) -> str:
    return f"Results for: {query}"

@trace(span_type="llm")
def call_llm(prompt: str) -> str:
    return f"Response to: {prompt}"

with tracer.span("pipeline") as root:
    results = search_database("users")
    response = call_llm(f"Summarise: {results}")
    root.finish(output=response)
```

## CLI Usage

```bash
# View the most recent trace
agenttrace view

# Generate HTML timeline
agenttrace view --html
agenttrace view --html --output trace_report.html

# Simulate a demo trace
agenttrace simulate

# Show trace data summary
agenttrace info

# Clear all stored traces
agenttrace clear

# Export trace data as JSON
agenttrace export --output my_trace.json

# Specify a custom data directory
agenttrace view --data ./my_traces
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Your Agent Code                     │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Tracer                                             ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             ││
│  │  │ Span 1  │→ │ Span 2  │→ │ Span 3  │  ...        ││
│  │  │ (root)  │  │ (LLM)   │  │ (tool)  │             ││
│  │  └─────────┘  └─────────┘  └─────────┘             ││
│  └─────────────────────────────────────────────────────┘│
│                        ↓                                 │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Storage Backend    ←──   Exporters                 ││
│  │  (memory / file)          (console / HTML / JSON)   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Span Types

| Type | Colour | Icon | Purpose |
|------|--------|------|---------|
| `agent` | Blue | 🤖 | Top-level agent execution |
| `llm` | Green | 🧠 | LLM inference calls |
| `tool` | Yellow | 🔧 | Tool/function invocations |
| `thought` | Purple | 💭 | Reasoning or planning steps |

## Storage Backends

| Backend | Persistence | Use Case |
|---------|-------------|----------|
| `InMemoryStorage` | Ephemeral | Testing, short-lived scripts |
| `FileStorage` | Disk (JSONL) | Cross-session analysis, debugging |

## Examples

Check the `examples/` directory:

- `basic_tracing.py` — Instrument a simulated customer-support agent
- `html_report.py` — Generate an interactive HTML timeline visualisation
- `with_decorator.py` — Use the `@trace` decorator on individual functions

## Running Tests

```bash
pip install pytest
pytest tests/
```

## Project Structure

```
agenttrace/
├── agenttrace/
│   ├── span.py          # Span data model & SpanTree
│   ├── tracer.py        # Core tracer with context manager API
│   ├── wrapper.py       # @trace decorator
│   ├── exporter/        # Console and HTML exporters
│   ├── storage/         # In-memory and file-based storage
│   └── cli/             # CLI interface
├── examples/            # Usage examples
├── tests/               # Test suite
└── pyproject.toml       # Project metadata
```

## Use Cases

- **Debugging** — See exactly what your agent did, in what order, and how long each step took
- **Cost Optimisation** — Identify expensive LLM calls and optimise prompt design
- **Performance Analysis** — Find bottlenecks in multi-step agent pipelines
- **Audit Logging** — Maintain a persistent record of all agent actions for compliance
- **CI Integration** — Export traces in CI to monitor agent behaviour across versions

## License

MIT
