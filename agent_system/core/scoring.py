"""Weighted scoring, must-have filtering, freshness and validation logic.

Pure functions with no LLM calls, shared by the tools, the skill script,
the offline pipeline, the tests and the website build.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable

from . import data

MAX_SCORE = 3
CAROUSEL_MAX_WORDS = 40
CAROUSEL_SLIDES = (8, 10)


@dataclass
class Ranked:
    id: str
    name: str
    score: float                       # 0-100
    breakdown: dict[str, float]        # criterion -> points contributed
    missing: list[str] = field(default_factory=list)

    @property
    def eligible(self) -> bool:
        return not self.missing


def resolve_weights(preset: str | None = None, weights: dict[str, float] | None = None) -> dict[str, float]:
    keys = [c["key"] for c in data.criteria()]
    if weights:
        unknown = set(weights) - set(keys)
        if unknown:
            raise ValueError(f"Unknown criteria: {sorted(unknown)}")
        return {k: float(weights.get(k, 0)) for k in keys}
    name = (preset or "equal").strip().lower()
    presets = data.presets()
    if name not in presets:
        raise ValueError(f"Unknown preset '{preset}'. Known: {', '.join(presets)}")
    return {k: float(presets[name]["weights"][k]) for k in keys}


def missing_must_haves(p: dict[str, Any], required: Iterable[str]) -> list[str]:
    names = {m["key"]: m["name"] for m in data.must_haves()}
    out = []
    for key in required:
        if key not in names:
            raise ValueError(f"Unknown must-have '{key}'. Known: {', '.join(names)}")
        value = p["must"].get(key)
        if value is not True:
            out.append(names[key] + (" (not confirmed)" if value is None else ""))
    return out


def rank(preset: str | None = None, weights: dict[str, float] | None = None,
         required: Iterable[str] = ()) -> list[Ranked]:
    """Rank all platforms. Eligible platforms first, then by score."""
    w = resolve_weights(preset, weights)
    total = sum(v * MAX_SCORE for v in w.values()) or 1.0
    required = [r for r in required if r]
    results = []
    for p in data.platforms():
        breakdown = {k: round(w[k] * p["scores"][k] / total * 100, 2) for k in w}
        results.append(Ranked(p["id"], p["name"], round(sum(breakdown.values()), 1),
                              breakdown, missing_must_haves(p, required)))
    results.sort(key=lambda r: (not r.eligible, -r.score))
    return results


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def freshness(today: date | None = None, max_age_months: int = 6) -> dict[str, Any]:
    """Report whether the dataset's as_of date is older than max_age_months."""
    today = today or date.today()
    raw = str(data.platforms_doc()["as_of"])
    year, month = (int(x) for x in raw.split("-")[:2])
    age = months_between(date(year, month, 1), today)
    return {"as_of": raw, "age_months": age, "stale": age > max_age_months,
            "max_age_months": max_age_months}


def _words(text: str) -> int:
    return len(re.findall(r"[\w$%'’/.+-]+", text))


def validate_carousel(doc: dict[str, Any]) -> list[str]:
    """Return a list of problems. An empty list means the carousel passes."""
    problems = []
    slides = doc.get("slides") or []
    lo, hi = CAROUSEL_SLIDES
    if not lo <= len(slides) <= hi:
        problems.append(f"Carousel has {len(slides)} slides; expected {lo}-{hi}.")
    for i, s in enumerate(slides, 1):
        if not s.get("headline"):
            problems.append(f"Slide {i} has no headline.")
        body = s.get("body") or []
        if isinstance(body, str):
            body = [body]
        n = _words(" ".join(body))
        if n > CAROUSEL_MAX_WORDS:
            problems.append(f"Slide {i} body has {n} words; limit is {CAROUSEL_MAX_WORDS}.")
        if not s.get("visual"):
            problems.append(f"Slide {i} has no visual/layout note.")
    caption = doc.get("caption", "")
    hashtags = re.findall(r"#\w+", caption)
    if len(hashtags) > 3:
        problems.append(f"Caption has {len(hashtags)} hashtags; limit is 3.")
    if not caption.strip():
        problems.append("Caption is empty.")
    return problems


_PRICE = re.compile(r"\$\s?(\d[\d,]*)")


def fact_check(text: str) -> list[dict[str, str]]:
    """Flag prices that appear near a platform name but differ from the data file.

    A deliberately simple heuristic: for each sentence that names exactly one
    platform, every dollar figure in it must appear in that platform's
    free_tier or paid_from fact.
    """
    issues = []
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    names = {p["id"]: [p["name"].lower(), p["id"]] for p in data.platforms()}
    for sentence in sentences:
        low = sentence.lower()
        hits = [pid for pid, aliases in names.items() if any(a in low for a in aliases)]
        if len(hits) != 1:
            continue
        p = data.platform(hits[0])
        known = _PRICE.findall(p["facts"]["free_tier"] + " " + p["facts"]["paid_from"])
        for price in _PRICE.findall(sentence):
            if price not in known:
                issues.append({"platform": p["name"], "claim": sentence.strip(),
                               "expected": f"{p['facts']['free_tier']} / {p['facts']['paid_from']}"})
    return issues
