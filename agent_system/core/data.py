"""Load the repository's data files. Everything reads from here."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
INSIGHTS_DIR = REPO_ROOT / "insights"
CAROUSELS_DIR = REPO_ROOT / "carousels"


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def platforms_doc() -> dict[str, Any]:
    return _load(DATA_DIR / "platforms.yaml")


@lru_cache(maxsize=1)
def criteria_doc() -> dict[str, Any]:
    return _load(DATA_DIR / "criteria.yaml")


def platforms() -> list[dict[str, Any]]:
    return platforms_doc()["platforms"]


def platform(platform_id: str) -> dict[str, Any]:
    key = platform_id.strip().lower()
    for p in platforms():
        if p["id"] == key or p["name"].lower() == key:
            return p
    raise KeyError(f"Unknown platform '{platform_id}'. Known: {', '.join(p['id'] for p in platforms())}")


def criteria() -> list[dict[str, Any]]:
    return criteria_doc()["criteria"]


def presets() -> dict[str, dict[str, Any]]:
    return criteria_doc()["presets"]


def must_haves() -> list[dict[str, Any]]:
    return criteria_doc()["must_haves"]
