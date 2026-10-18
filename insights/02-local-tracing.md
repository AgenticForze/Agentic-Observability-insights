---
title: Keeping LLM traces on your own machine
audience: Engineers, students
tags: [phoenix, opentelemetry, langsmith, self-host]
---

# Keeping LLM traces on your own machine

Moving from LangSmith to local tracing takes two changes: stop sending spans to LangSmith, and send them to something that stores data locally.

> **Running in Colab?** "Local" there means the Colab VM, which is wiped when the session ends. Run Jupyter on your laptop, or download the trace files before the session closes.

## Option 1: Arize Phoenix (recommended)

Phoenix is an open-source trace viewer that stores traces in SQLite under `~/.phoenix`.

```bash
pip install arize-phoenix openinference-instrumentation-langchain
phoenix serve        # UI at http://localhost:6006
```

Replace the `LANGSMITH_*` configuration with:

```python
os.environ["LANGSMITH_TRACING"] = "false"     # @traceable becomes a no-op
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

tracer_provider = register(
    project_name="lexagent-rental-law",
    endpoint="http://localhost:6006/v1/traces",
)
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

Add the same lines to any separate process, such as an MCP server.

### Keeping custom spans and cross-process nesting

| LangSmith | OpenTelemetry |
|---|---|
| `@traceable(name=...)` | `tracer.start_as_current_span(...)` |
| `run.metadata["outcome"] = ...` | `span.set_attribute("outcome", ...)` |
| `run.to_headers()` | `propagate.inject(carrier)` |
| `langsmith-trace` header | `traceparent` header |
| `tracing_context(parent=...)` | `propagate.extract(headers)` |

Client side, before an HTTP call to another process:

```python
from opentelemetry.propagate import inject
carrier = {}
inject(carrier)
connection["headers"] = {**(connection.get("headers") or {}), **carrier}
```

Server side:

```python
from opentelemetry.propagate import extract

def otel_parent(ctx):
    try:
        return extract(dict(ctx.request_context.request.headers))
    except Exception:
        return None     # tracing must never break a tool
```

## Option 2: JSON Lines files, no viewer

```python
from langchain_core.tracers.base import BaseTracer

class JsonlTracer(BaseTracer):
    def __init__(self, path="traces.jsonl"):
        super().__init__()
        self.path = path

    def _persist_run(self, run):
        with open(self.path, "a") as f:
            f.write(json.dumps(run.dict(), default=str) + "\n")
```

Pass it as `config={"callbacks": [JsonlTracer()]}`. It only sees LangChain and LangGraph runs and has no UI.

## Option 3: self-hosted LangSmith

Your code works unchanged with `LANGSMITH_ENDPOINT` pointed at your server, but self-hosting requires an Enterprise license.

## Interactive version

[Open the local-tracing guide](explorers/lexagent_local_tracing.html)
