#!/usr/bin/env python3
"""Build site/content.json from the repository and sync the skill's data.

    python scripts/build_site.py           # build
    python scripts/build_site.py --check   # fail if the skill's references are out of date
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_system.core import data, pipeline, scoring  # noqa: E402

SITE = ROOT / "site"
SKILL_REFS = ROOT / "skills" / "observability-platform-analyst" / "references"
SKILL_SYNC = {
    ROOT / "data" / "platforms.yaml": SKILL_REFS / "platforms.yaml",
    ROOT / "data" / "criteria.yaml": SKILL_REFS / "criteria.yaml",
    ROOT / "insights" / "01-build-buy-hybrid.md": SKILL_REFS / "build-buy-hybrid.md",
}
TEXT_EXT = {".md", ".yaml", ".yml", ".py", ".txt", ".toml", ".json", ".cfg"}
# carousels/ stays in the repo (agents write drafts there) but is not published on the site.
SKIP_DIRS = {".git", "site", "carousels", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
MAX_BYTES = 200_000


def sync_skill(check: bool) -> list[str]:
    stale = []
    SKILL_REFS.mkdir(parents=True, exist_ok=True)
    for src, dst in SKILL_SYNC.items():
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            stale.append(str(dst.relative_to(ROOT)))
            if not check:
                shutil.copyfile(src, dst)
    return stale


def front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def repo_files() -> list[dict]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if path.is_dir() or any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.name == ".gitkeep":
            continue
        entry = {"path": rel.as_posix(), "size": path.stat().st_size}
        if (path.suffix in TEXT_EXT or path.name in {"LICENSE", ".gitignore"}) and entry["size"] <= MAX_BYTES:
            entry["content"] = path.read_text(encoding="utf-8", errors="replace")
        files.append(entry)
    return files


def insights() -> list[dict]:
    out = []
    for path in sorted(data.INSIGHTS_DIR.rglob("*.md")):
        meta, body = front_matter(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT).as_posix()
        out.append({"slug": path.stem, "path": rel, "draft": "drafts" in path.parts,
                    "title": meta.get("title", path.stem), "audience": meta.get("audience", ""),
                    "tags": meta.get("tags", []), "status": meta.get("status", "published"),
                    "body": body})
    return out



def git_info() -> dict:
    def run(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return ""
    return {"commit": run("rev-parse", "--short", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    stale = sync_skill(args.check)
    if args.check:
        if stale:
            print("Skill references out of date (run scripts/build_site.py):\n  " + "\n  ".join(stale))
            return 1
        print("Skill references are in sync.")
        return 0

    reports = {key: pipeline.run(key).to_markdown() for key in data.presets()}
    review = pipeline.review_repository()
    content = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": {"owner": "AgenticForze", "name": "agentic-observability-insights", **git_info()},
        "platforms": data.platforms_doc(),
        "criteria": data.criteria_doc(),
        "insights": insights(),
        "reports": reports,
        "review": review,
        "freshness": scoring.freshness(),
        "files": repo_files(),
    }
    out = SITE / "content.json"
    out.write_text(json.dumps(content, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB, {len(content['files'])} files). "
          f"Review: {'APPROVED' if review['approved'] else 'REVISE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
