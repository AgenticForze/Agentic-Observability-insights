---
title: "LexAgent: following one request through a traced ReAct agent"
audience: Students
tags: [react, langgraph, mcp, distributed-tracing, evaluation]
---

# LexAgent: following one request through a traced ReAct agent

LexAgent is a teaching notebook (Week 15, Monitoring and Observability). A LangGraph ReAct agent answers New York rental-law questions using tools served by a separate FastMCP server process. Every step is traced to LangSmith as one tree.

## The 14 steps

| # | Step | Key concept |
|---|---|---|
| 1 | Configure tracing, start the MCP server | Set tracing env vars before building any Runnable |
| 2 | Query enters the root span | `query_id` as a correlation ID inherited by every child |
| 3 | Build prompt, call the LLM | `stop=["\nObservation:"]` prevents invented tool results |
| 4 | Parse Thought and Action | Outcome recorded as data: `tool_call`, `final_answer`, `malformed_react` |
| 5 | Route | `should_continue` writes `route` as a filterable field |
| 6 | Cross the process boundary | `langsmith-trace` and `baggage` headers carry trace context |
| 7 | Server runs the tool | `ctx: Context` is injected and hidden from the LLM's schema |
| 8 | Result returns | `tool_status`, `mcp_latency_ms` |
| 9 | Append Observation | Real output becomes a `ToolMessage`; errors are labelled system notes |
| 10 | Loop | The agent chooses web search itself when the corpus has a gap |
| 11 | Final Answer | Step cap of 8 produces an explicit partial answer |
| 12 | Roll-ups on root | `tool_sequence`, `n_tool_calls`, `answered`; return `run_id` |
| 13 | Export | Flush notebook tracers, pause, then stop the server |
| 14 | Evaluate | Six task checks plus a gpt-4o judge, wrapped in one parent span |

## agent_node in one paragraph

Each call is one ReAct turn. It enforces the step cap, rebuilds the full scratchpad, calls the model with the Observation stop sequence, parses the reply into a tool call, a final answer or a malformed turn, repairs tool inputs, and returns a structured `tool_calls` entry so LangGraph can route. It never runs a tool.

## The five demo runs

| Run | Topic | Lesson |
|---|---|---|
| 1 | Security deposit cap | Clean baseline trace |
| 2 | Non-payment and Airbnb sublet | Multi-source reasoning |
| 3 | Rewrite a draft lease | Server-side nested LLM span |
| 4 | Out of scope | Task checks pass, groundedness is 0: you need both eval layers |
| 5 | Good Cause Eviction Law | Agent detects a corpus gap and uses web search |

## Interactive version

[Open the walkthrough](explorers/lexagent_walkthrough.html): animated sequence diagram, span tree, runs and a quiz.
