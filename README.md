# Agentic Observability Insights

Comparisons, insights and tooling for choosing and running LLM observability platforms.

**Browse it:** https://agenticforze.github.io/agentic-observability-insights/

The core idea: **own the signal, rent the screen.** Own your instrumentation (OpenTelemetry) and your telemetry pipeline. Buy or build everything above them based on scale, sovereignty and what actually differentiates you.

## What's inside

| Folder | What it holds |
|---|---|
| [`data/`](data) | The single source of truth: nine platforms with facts, 0-3 scores, must-have flags and sources (`platforms.yaml`), and the seven criteria, must-haves and weight presets (`criteria.yaml`). |
| [`insights/`](insights) | Markdown insights: the build/buy/hybrid framework, local tracing, the LexAgent walkthrough, the evaluation checklist. Agent drafts land in `insights/drafts/`. |
| [`carousels/`](carousels) | LinkedIn carousels as YAML (slides, visual notes, caption, first comment). Agent drafts land in `carousels/drafts/`. |
| [`agent_system/`](agent_system) | The multi-framework agent system: shared tools and prompts in `core/`, and the same workflow in LangGraph, CrewAI and the OpenAI Agents SDK in `frameworks/`. |
| [`skills/`](skills) | The `observability-platform-analyst` Claude skill, with bundled data and a ranking script. |
| [`site/`](site) | The static website that browses this repository, including the expandable carousel and three standalone explorers. |
| [`scripts/`](scripts) | `build_site.py` builds `site/content.json` and syncs the skill's data. |
| [`tests/`](tests) | Tests for data integrity, scoring, tools, validation and the offline pipeline. |

```
.
├── data/                     platforms.yaml, criteria.yaml
├── insights/                 *.md (+ drafts/)
├── carousels/                *.yaml (+ drafts/)
├── agent_system/
│   ├── core/                 data, scoring, tools, prompts, pipeline
│   ├── frameworks/           langgraph_flow, crewai_flow, openai_agents_flow
│   └── run.py                CLI
├── skills/observability-platform-analyst/
│   ├── SKILL.md
│   ├── references/           synced copies of data/ + framework
│   └── scripts/rank.py
├── site/                     index.html, assets/, explorers/, content.json (built)
├── scripts/build_site.py
└── tests/
```

## The agent system

Four roles share one tool set and one dataset:

| Role | Does | Tools |
|---|---|---|
| Researcher | Gathers current facts, checks data freshness, searches the web if stale | `list_platforms`, `get_platform`, `check_freshness`, `web_search` |
| Analyst | Ranks platforms for an audience, compares the top three, calls build/buy/hybrid | `rank_platforms`, `compare_platforms`, `get_platform` |
| Writer | Drafts an insight and a validated carousel | `save_insight`, `save_carousel`, `validate_carousel`, `compare_platforms` |
| Reviewer | Approves or sends back drafts | `validate_carousel`, `fact_check`, `get_platform` |

The same workflow runs in three frameworks so the designs can be compared:

| | LangGraph | CrewAI | OpenAI Agents SDK |
|---|---|---|---|
| Control flow | Explicit state graph | Sequential tasks | Orchestrator with agents as tools |
| Review loop | Conditional edge, max 2 revisions | One extra pass on REVISE | Instructed in the prompt |
| Predictability | Highest | High | Lowest, most flexible |

`agent_system/core/pipeline.py` runs the workflow with no LLM. CI and the site build use it.

### Run

```bash
# Offline (no API keys)
pip install -r requirements.txt
python -m agent_system.run --framework offline --preset regulated --must selfhost,otel

# LLM-backed: one virtual environment per framework
# (CrewAI and the OpenAI Agents SDK need different openai package versions)
pip install -r requirements-langgraph.txt     # or -crewai / -openai
export OPENAI_API_KEY=...                     # optional: TAVILY_API_KEY, LLM_MODEL
python -m agent_system.run --framework langgraph "Carousel on observability for regulated banks"
```

Presets: `course`, `startup`, `regulated`, `langchain`, `equal`. Must-haves: `selfhost`, `osi`, `otel`, `ci`.

## The skill

```bash
cp -r skills/observability-platform-analyst ~/.claude/skills/
python skills/observability-platform-analyst/scripts/rank.py --preset startup --must otel
```

## The website

```bash
python scripts/build_site.py
python -m http.server -d site 8000     # http://localhost:8000
```

On every push to `main`, GitHub Actions runs the tests, builds `site/content.json` and deploys `site/` to GitHub Pages. Each page has **Edit on GitHub** and **Leave feedback** links, so reviewers can comment without cloning the repo.

## Updating the data

1. Edit `data/platforms.yaml`. Every fact should trace to an entry in `sources`. Use `Not confirmed` rather than guessing.
2. Update `as_of`.
3. Run `python scripts/build_site.py` (this also syncs the skill) and `pytest`.
4. Open a pull request.

Scores are an editorial assessment drawn from published 2026 comparisons, not benchmarks. Pricing changes often: verify on vendor pages before buying.

## License

MIT. See [LICENSE](LICENSE).
