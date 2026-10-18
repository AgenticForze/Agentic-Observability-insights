import json
from datetime import date

import pytest
import yaml

from agent_system.core import data, pipeline, scoring, tools


def test_every_platform_has_all_scores_facts_and_sources():
    keys = {c["key"] for c in data.criteria()}
    musts = {m["key"] for m in data.must_haves()}
    source_ids = {s["id"] for s in data.platforms_doc()["sources"]}
    for p in data.platforms():
        assert set(p["scores"]) == keys, p["id"]
        assert all(0 <= v <= 3 for v in p["scores"].values()), p["id"]
        assert set(p["must"]) == musts, p["id"]
        assert set(p["sources"]) <= source_ids, p["id"]
        for field in ("license", "selfhost", "free_tier", "paid_from", "otel"):
            assert p["facts"][field], (p["id"], field)


def test_rank_scores_are_0_to_100_and_sorted():
    ranked = scoring.rank("equal")
    assert all(0 <= r.score <= 100 for r in ranked)
    assert [r.score for r in ranked] == sorted((r.score for r in ranked), reverse=True)


def test_perfect_platform_scores_100():
    ranked = scoring.rank(weights={"data": 1, "instr": 0, "agent": 0, "eval": 0, "cost": 0, "ops": 0, "ease": 0})
    assert ranked[0].score == 100.0


def test_must_haves_push_platforms_last():
    ranked = scoring.rank("course", required=["osi"])
    first_ineligible = next(i for i, r in enumerate(ranked) if not r.eligible)
    assert all(not r.eligible for r in ranked[first_ineligible:])
    assert "LangSmith" in [r.name for r in ranked[first_ineligible:]]


def test_unknown_preset_and_must_have_raise():
    with pytest.raises(ValueError):
        scoring.rank("nope")
    with pytest.raises(ValueError):
        scoring.rank("equal", required=["nope"])


def test_freshness():
    assert scoring.freshness(today=date(2026, 11, 1), max_age_months=6)["stale"] is False
    assert scoring.freshness(today=date(2027, 12, 1), max_age_months=6)["stale"] is True


def test_validate_carousel_flags_long_slides():
    doc = {"slides": [{"headline": "h", "visual": "v", "body": ["word " * 41]}] * 9, "caption": "x #a #b"}
    problems = scoring.validate_carousel(doc)
    assert any("41 words" in p for p in problems)


def test_repository_carousels_pass_validation():
    for path in data.CAROUSELS_DIR.rglob("*.yaml"):
        doc = yaml.safe_load(path.read_text())
        assert scoring.validate_carousel(doc) == [], path


def test_fact_check_catches_wrong_price():
    assert scoring.fact_check("Langfuse paid plans start at $99/mo.")
    assert not scoring.fact_check("Langfuse paid plans start at $29/mo.")


def test_tools_return_json():
    for fn, kwargs in [(tools.list_platforms, {}), (tools.get_platform, {"platform_id": "langfuse"}),
                       (tools.rank_platforms, {"preset": "startup", "must_haves": "otel"}),
                       (tools.compare_platforms, {"platform_ids": "langfuse,phoenix", "group": "evaluation"}),
                       (tools.check_freshness, {}), (tools.web_search, {"query": "x"}),
                       (tools.fact_check, {"text": "Helicone costs $79/mo."})]:
        json.loads(fn(**kwargs))


def test_tool_errors_are_returned_not_raised():
    assert "error" in json.loads(tools.get_platform("nope"))
    assert "error" in json.loads(tools.rank_platforms("nope"))
    assert "error" in json.loads(tools.compare_platforms("langfuse", group="nope"))


def test_save_carousel_refuses_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CAROUSELS_DIR", tmp_path)
    out = json.loads(tools.save_carousel("bad", "slides: []\ncaption: ''"))
    assert out["saved"] is None and out["problems"]


def test_offline_pipeline_approves_repository():
    report = pipeline.run("regulated", ["selfhost"])
    assert report.review["approved"], report.review["problems"]
    assert "Platform brief" in report.to_markdown()
