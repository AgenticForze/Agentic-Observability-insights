---
title: "Build, buy or hybrid: an observability decision framework"
audience: CTO, CIO, platform leads
tags: [strategy, tco, opentelemetry]
---

# Build, buy or hybrid: an observability decision framework

Most observability stacks were never designed. Each team added an agent or a dashboard, and the result is a large, growing bill with high switching costs. AI agents make this worse, because one agent run can produce dozens of spans.

## The principle: own the signal, rent the screen

Split the stack into four layers and decide each one separately.

| Layer | What it does | Decision |
|---|---|---|
| 1. Instrumentation | Emits spans, metrics and logs from your code | **Own it.** Use OpenTelemetry, not proprietary agents. |
| 2. Pipeline | Samples, redacts, enriches and routes telemetry | **Own it.** An OpenTelemetry Collector you control. |
| 3. Storage | Keeps hot (recent, queryable) and cold (cheap, archival) data | Choose per data tier. |
| 4. Analysis and UI | Dashboards, trace explorer, evals, alerts | Usually buy. |

If you own layers 1 and 2, every vendor in layers 3 and 4 becomes replaceable.

## When to buy

- Your platform team is small and speed of delivery matters most.
- Your stack is standard (common languages, common frameworks).
- Telemetry volume is modest or unpredictable.
- You need evaluation features (datasets, LLM-as-judge, CI gates) that are expensive to build.

## When to build

- Telemetry is part of your product, for example you sell monitoring or analytics.
- Data sovereignty or regulation leaves no acceptable vendor.
- Your volume is large and predictable enough that vendor spend reliably exceeds the fully loaded cost of the team that would run the replacement.

## When to go hybrid (the default for most enterprises)

- You own instrumentation and the pipeline.
- Hot, high-value data (errors, slow traces, sampled agent runs) goes to a vendor.
- Everything else goes to low-cost object storage for audits and later analysis.
- Specialised needs, such as LLM evaluation, get a specialised tool fed from the same pipeline.

## The economics

- An in-house platform is a permanent headcount line. Price the engineers, not only the licences.
- Vendor costs scale with volume. Cut ingest with sampling and filtering in your pipeline before you renegotiate.
- Revisit the decision every year. The crossover point moves as volume and vendor prices change.

## The two traps

1. **Building your own UI.** You will spend a year recreating what vendors ship every week. Build the plumbing, not the screens.
2. **Proprietary agents everywhere.** Switching later means changing every service. Instrument once with open standards.

## Related

- [Platform comparison](#/compare) for AI and LLM workloads
- [Carousel: build, buy or hybrid](#/carousels)
