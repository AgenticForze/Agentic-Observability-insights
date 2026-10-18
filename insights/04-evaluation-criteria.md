---
title: How to evaluate an LLM observability platform
audience: Platform and ML engineering leads
tags: [evaluation, procurement, checklist]
---

# How to evaluate an LLM observability platform

Score each candidate on these criteria (0 to 3), then weight them for your situation. The same criteria drive the [comparison page](#/compare) and the agents in this repository.

| Criterion | Question to ask in a trial | What to check |
|---|---|---|
| Data control | Can we keep trace data where we need it? | License (OSI or source-available), free self-hosting, data region |
| Instrumentation fit | Does it fit how we instrument? | OpenTelemetry support, frameworks, cross-process span nesting |
| Agent depth | Can we see each reasoning step? | Span-level tool calls and inputs, not just request logs |
| Evaluation loop | Does it close the evaluation loop? | Datasets, LLM-as-judge, online evals, annotation, CI gates |
| Cost | What will it cost at our volume? | Billing unit, expected monthly volume, retention |
| Operations | Will it alert us? | Dashboards, alerts, cost per query, links to existing monitoring |
| Ease of setup | How fast is the first trace? | Time from signup to first nested trace, SDK languages |

Also check that you can filter and chart on your own metadata fields, such as `outcome` and `route`.

## Weight presets

| Preset | Highest weights |
|---|---|
| Course or classroom | Data control, cost |
| Startup | Ease of setup, agent depth, evaluation loop |
| Regulated enterprise | Data control, evaluation loop |
| LangChain team | Instrumentation fit, agent depth, ease of setup |

## A note on the scores

Scores in `data/platforms.yaml` are an editorial assessment drawn from published 2026 comparisons, not benchmarks. Pricing changes often. Re-verify before buying, and open a pull request if a fact is out of date.
