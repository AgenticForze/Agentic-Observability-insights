#!/usr/bin/env python3
"""Rank observability platforms for a preset or custom weights.

Self-contained: needs only PyYAML. Reads the data files next to this skill
(references/), or the repository's data/ folder when run inside the repo.

Examples:
    python rank.py --preset regulated --must selfhost,otel
    python rank.py --weights data=5,cost=4,eval=3 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

HERE = Path(__file__).resolve().parent


def find_data() -> Path:
    for candidate in (HERE.parent / "references", HERE.parents[2] / "data"):
        if (candidate / "platforms.yaml").exists():
            return candidate
    sys.exit("Could not find platforms.yaml in references/ or the repository data/ folder.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", default="equal")
    ap.add_argument("--weights", default="", help="Custom weights, e.g. data=5,cost=4 (others 0)")
    ap.add_argument("--must", default="", help="Comma-separated: selfhost, osi, otel, ci")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    d = find_data()
    platforms = yaml.safe_load((d / "platforms.yaml").read_text(encoding="utf-8"))
    criteria = yaml.safe_load((d / "criteria.yaml").read_text(encoding="utf-8"))
    keys = [c["key"] for c in criteria["criteria"]]
    must_names = {m["key"]: m["name"] for m in criteria["must_haves"]}

    if args.weights:
        weights = {k: 0.0 for k in keys}
        for pair in args.weights.split(","):
            k, _, v = pair.partition("=")
            if k.strip() not in weights:
                sys.exit(f"Unknown criterion '{k}'. Known: {', '.join(keys)}")
            try:
                weights[k.strip()] = float(v)
            except ValueError:
                sys.exit(f"Weight for '{k}' must be a number, got '{v}'.")
        label = "custom"
    else:
        if args.preset not in criteria["presets"]:
            sys.exit(f"Unknown preset '{args.preset}'. Known: {', '.join(criteria['presets'])}")
        weights = {k: float(criteria["presets"][args.preset]["weights"][k]) for k in keys}
        label = args.preset

    required = [m.strip() for m in args.must.split(",") if m.strip()]
    for m in required:
        if m not in must_names:
            sys.exit(f"Unknown must-have '{m}'. Known: {', '.join(must_names)}")

    total = sum(w * 3 for w in weights.values()) or 1.0
    rows = []
    for p in platforms["platforms"]:
        score = sum(weights[k] * p["scores"][k] for k in keys) / total * 100
        missing = [must_names[m] + (" (not confirmed)" if p["must"][m] is None else "")
                   for m in required if p["must"][m] is not True]
        rows.append({"id": p["id"], "name": p["name"], "score": round(score, 1), "missing": missing,
                     "free_tier": p["facts"]["free_tier"], "paid_from": p["facts"]["paid_from"]})
    rows.sort(key=lambda r: (bool(r["missing"]), -r["score"]))

    if args.json:
        print(json.dumps({"preset": label, "weights": weights, "must_haves": required,
                          "as_of": str(platforms["as_of"]), "ranking": rows}, indent=2))
        return 0

    print(f"Ranking for {label} (data as of {platforms['as_of']}; scores are editorial, not benchmarks)\n")
    print(f"{'#':>2}  {'Platform':<18}{'Score':>6}  Missing must-haves")
    rank = 0
    for r in rows:
        rank += 0 if r["missing"] else 1
        pos = "–" if r["missing"] else str(rank)
        print(f"{pos:>2}  {r['name']:<18}{r['score']:>6}  {', '.join(r['missing']) or '—'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
