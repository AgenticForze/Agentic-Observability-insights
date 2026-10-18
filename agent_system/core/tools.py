"""Framework-neutral tools.

Every tool takes simple typed arguments, has a docstring the LLM reads, and
returns a JSON string. Framework adapters wrap these functions as-is, so the
three implementations call identical code.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import yaml

from . import data, scoring

GROUPS = {
    "openness": ["license", "selfhost", "free_tier", "paid_from"],
    "tracing": ["otel", "agent_depth", "frameworks"],
    "evaluation": ["datasets", "llm_judge", "online_evals", "human_annotation", "ci_gating"],
    "operations": ["cost_tracking", "prompt_mgmt", "extras"],
}


def _json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not s:
        raise ValueError("Slug is empty after cleaning.")
    return s[:60]


def list_platforms(category: str = "") -> str:
    """List observability platforms with id, name, owner, category and one-line summary.

    Args:
        category: Optional filter: self-host, buy-eval-first, gateway or apm. Empty for all.
    """
    items = [
        {k: p[k] for k in ("id", "name", "owner", "category", "summary")}
        for p in data.platforms()
        if not category or p["category"] == category
    ]
    return _json({"as_of": str(data.platforms_doc()["as_of"]), "platforms": items})


def get_platform(platform_id: str) -> str:
    """Return every fact, score, strength, risk and source for one platform.

    Args:
        platform_id: Platform id or name, for example "langfuse" or "Arize Phoenix".
    """
    try:
        p = data.platform(platform_id)
    except KeyError as e:
        return _json({"error": str(e)})
    srcs = {s["id"]: s for s in data.platforms_doc()["sources"]}
    return _json({**p, "sources": [srcs[s] for s in p["sources"] if s in srcs]})


def rank_platforms(preset: str = "equal", must_haves: str = "") -> str:
    """Rank platforms by weighted score (0-100) for an audience preset.

    Args:
        preset: course, startup, regulated, langchain or equal.
        must_haves: Comma-separated must-haves: selfhost, osi, otel, ci. Platforms missing one are listed last.
    """
    required = [m.strip() for m in must_haves.split(",") if m.strip()]
    try:
        ranked = scoring.rank(preset=preset, required=required)
    except ValueError as e:
        return _json({"error": str(e)})
    return _json({
        "preset": preset,
        "weights": scoring.resolve_weights(preset),
        "must_haves": required,
        "ranking": [{"rank": i + 1 if r.eligible else None, "id": r.id, "name": r.name,
                     "score": r.score, "missing": r.missing} for i, r in enumerate(ranked)],
    })


def compare_platforms(platform_ids: str, group: str = "all") -> str:
    """Compare chosen platforms side by side on one group of facts.

    Args:
        platform_ids: Comma-separated platform ids, for example "langfuse,phoenix,langsmith".
        group: openness, tracing, evaluation, operations or all.
    """
    fields = sum(GROUPS.values(), []) if group == "all" else GROUPS.get(group)
    if fields is None:
        return _json({"error": f"Unknown group '{group}'. Use one of: all, {', '.join(GROUPS)}"})
    out = {}
    for pid in [x.strip() for x in platform_ids.split(",") if x.strip()]:
        try:
            p = data.platform(pid)
        except KeyError as e:
            return _json({"error": str(e)})
        out[p["name"]] = {f: p["facts"][f] for f in fields} | {"scores": p["scores"]}
    return _json(out)


def check_freshness(max_age_months: int = 6) -> str:
    """Report how old the platform dataset is and whether it needs re-verification.

    Args:
        max_age_months: Age in months after which the data counts as stale.
    """
    return _json(scoring.freshness(max_age_months=max_age_months))


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current platform news, pricing or features.

    Uses Tavily when TAVILY_API_KEY is set. Without a key it returns an empty
    result and a note, so the agents still run offline.

    Args:
        query: Search query, for example "Langfuse pricing 2026".
        max_results: Maximum results to return (1-10).
    """
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return _json({"results": [], "note": "TAVILY_API_KEY not set; web search skipped. Use the dataset."})
    try:
        from tavily import TavilyClient
    except ImportError:
        return _json({"results": [], "note": "Install tavily-python to enable web search."})
    try:
        res = TavilyClient(api_key=key).search(query, max_results=max(1, min(10, max_results)))
    except Exception as e:  # network or quota errors must not crash an agent
        return _json({"results": [], "error": f"Search failed: {e}"})
    return _json({"results": [{"title": r.get("title"), "url": r.get("url"),
                               "snippet": (r.get("content") or "")[:400]} for r in res.get("results", [])]})


def validate_carousel(carousel_yaml: str) -> str:
    """Check a carousel draft: 8-10 slides, <=40 words per slide body, headline and visual on each slide, <=3 hashtags.

    Args:
        carousel_yaml: The carousel as YAML with keys slides (headline, body, visual) and caption.
    """
    try:
        doc = yaml.safe_load(carousel_yaml)
    except yaml.YAMLError as e:
        return _json({"ok": False, "problems": [f"Invalid YAML: {e}"]})
    if not isinstance(doc, dict):
        return _json({"ok": False, "problems": ["Carousel must be a YAML mapping."]})
    problems = scoring.validate_carousel(doc)
    return _json({"ok": not problems, "problems": problems})


def fact_check(text: str) -> str:
    """Check prices mentioned next to platform names against the dataset.

    Args:
        text: Draft text (insight, caption or slide copy) to check.
    """
    issues = scoring.fact_check(text)
    return _json({"ok": not issues, "issues": issues})


def save_insight(slug: str, title: str, markdown: str) -> str:
    """Save an insight draft to insights/drafts/<slug>.md for human review.

    Args:
        slug: Short file name, for example "hybrid-for-regulated".
        title: Document title.
        markdown: Body in Markdown, without front matter.
    """
    try:
        path = data.INSIGHTS_DIR / "drafts" / f"{_slug(slug)}.md"
    except ValueError as e:
        return _json({"error": str(e)})
    path.parent.mkdir(parents=True, exist_ok=True)
    front = yaml.safe_dump({"title": title, "status": "draft"}, sort_keys=False)
    path.write_text(f"---\n{front}---\n\n{markdown.strip()}\n", encoding="utf-8")
    return _json({"saved": str(path.relative_to(data.REPO_ROOT))})


def save_carousel(slug: str, carousel_yaml: str) -> str:
    """Validate and save a carousel draft to carousels/drafts/<slug>.yaml. Refuses to save if validation fails.

    Args:
        slug: Short file name, for example "observability-for-regulated".
        carousel_yaml: The carousel YAML (slides and caption).
    """
    check = json.loads(validate_carousel(carousel_yaml))
    if not check["ok"]:
        return _json({"saved": None, **check})
    try:
        path = data.CAROUSELS_DIR / "drafts" / f"{_slug(slug)}.yaml"
    except ValueError as e:
        return _json({"error": str(e)})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(carousel_yaml, encoding="utf-8")
    return _json({"saved": str(path.relative_to(data.REPO_ROOT)), "ok": True})


# Tool sets per role. Adapters read these lists.
RESEARCH_TOOLS = [list_platforms, get_platform, check_freshness, web_search]
ANALYST_TOOLS = [rank_platforms, compare_platforms, get_platform]
WRITER_TOOLS = [get_platform, compare_platforms, save_insight, save_carousel, validate_carousel]
REVIEWER_TOOLS = [validate_carousel, fact_check, get_platform]
ALL_TOOLS = list({t.__name__: t for t in RESEARCH_TOOLS + ANALYST_TOOLS + WRITER_TOOLS + REVIEWER_TOOLS}.values())
