"""The four-role workflow run deterministically, with no LLM.

Used by CI and the website build, and as a reference for what each role in
the LLM-backed frameworks is expected to produce.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from . import data, scoring

RECOMMENDATION = {
    "course": "hybrid-lite: self-host an open tool locally for free; keep instrumentation on OpenTelemetry.",
    "startup": "buy: use a managed platform with a free tier; keep instrumentation on OpenTelemetry so you can leave later.",
    "regulated": "hybrid: own the OpenTelemetry pipeline, keep sensitive traces self-hosted, buy evaluation features.",
    "langchain": "buy: LangSmith is the lowest-friction choice; add an OpenTelemetry exporter to limit lock-in.",
    "equal": "hybrid: own instrumentation and the pipeline, buy analysis and UI.",
}


@dataclass
class Report:
    preset: str
    must_haves: list[str]
    research: dict[str, Any]
    ranking: list[scoring.Ranked]
    recommendation: str
    review: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        crit = {c["key"]: c["name"] for c in data.criteria()}
        lines = [
            f"# Platform brief: {data.presets()[self.preset]['name']}",
            "",
            f"Data as of {self.research['freshness']['as_of']}"
            + (" (stale: re-verify pricing)" if self.research["freshness"]["stale"] else "") + ".",
            "Scores are editorial (0-3 per criterion), not benchmarks.",
            "",
            "## Ranking",
            "",
            "| # | Platform | Score | Missing must-haves |",
            "|---|---|---|---|",
        ]
        for i, r in enumerate(self.ranking, 1):
            lines.append(f"| {i if r.eligible else '–'} | {r.name} | {r.score} | {', '.join(r.missing) or '—'} |")
        lines += ["", "## Top three", ""]
        for r in [r for r in self.ranking if r.eligible][:3]:
            p = data.platform(r.id)
            top = max(r.breakdown, key=r.breakdown.get)
            lines.append(f"- **{p['name']}** ({r.score}): {p['summary']} Strongest contribution: {crit[top]}. "
                         f"Watch out: {p['watch_out'][0]}.")
        lines += ["", "## Recommendation", "", self.recommendation, "", "## Review", ""]
        if self.review.get("approved"):
            lines.append("APPROVED: carousels and insights pass validation and price checks.")
        else:
            lines.append("REVISE:")
            lines += [f"- {p}" for p in self.review.get("problems", [])]
        return "\n".join(lines) + "\n"


def research() -> dict[str, Any]:
    return {"freshness": scoring.freshness(),
            "platforms": [p["id"] for p in data.platforms()]}


def analyse(preset: str, must_haves: list[str]) -> list[scoring.Ranked]:
    return scoring.rank(preset=preset, required=must_haves)


def review_repository() -> dict[str, Any]:
    problems: list[str] = []
    for path in sorted(data.CAROUSELS_DIR.rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for p in scoring.validate_carousel(doc):
            problems.append(f"{path.relative_to(data.REPO_ROOT)}: {p}")
        for issue in scoring.fact_check(doc.get("caption", "")):
            problems.append(f"{path.relative_to(data.REPO_ROOT)}: price mismatch for {issue['platform']}")
    for path in sorted(data.INSIGHTS_DIR.rglob("*.md")):
        for issue in scoring.fact_check(path.read_text(encoding="utf-8")):
            problems.append(f"{path.relative_to(data.REPO_ROOT)}: price mismatch for {issue['platform']}: "
                            f"\"{issue['claim'][:80]}\" (dataset: {issue['expected']})")
    return {"approved": not problems, "problems": problems}


def run(preset: str = "course", must_haves: list[str] | None = None) -> Report:
    must_haves = must_haves or []
    if preset not in data.presets():
        raise ValueError(f"Unknown preset '{preset}'. Known: {', '.join(data.presets())}")
    return Report(preset=preset, must_haves=must_haves, research=research(),
                  ranking=analyse(preset, must_haves),
                  recommendation=RECOMMENDATION[preset], review=review_repository())
