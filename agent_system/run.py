"""Command-line entry point.

    python -m agent_system.run --framework offline --preset regulated --must selfhost,otel
    python -m agent_system.run --framework langgraph "Write a carousel for regulated banks"
"""
from __future__ import annotations

import argparse
import importlib
import sys

FRAMEWORKS = {
    "langgraph": "agent_system.frameworks.langgraph_flow",
    "crewai": "agent_system.frameworks.crewai_flow",
    "openai": "agent_system.frameworks.openai_agents_flow",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Observability platform analysis agents")
    ap.add_argument("request", nargs="?", default="",
                    help="What to produce (LLM frameworks only).")
    ap.add_argument("--framework", choices=["offline", *FRAMEWORKS], default="offline")
    ap.add_argument("--preset", default="course", help="Offline mode: audience preset.")
    ap.add_argument("--must", default="", help="Offline mode: comma-separated must-haves.")
    args = ap.parse_args(argv)

    if args.framework == "offline":
        from agent_system.core import pipeline
        must = [m.strip() for m in args.must.split(",") if m.strip()]
        try:
            report = pipeline.run(args.preset, must)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        print(report.to_markdown())
        return 0 if report.review["approved"] else 1

    if not args.request:
        ap.error("LLM frameworks need a request, for example: \"Carousel for regulated banks\"")
    try:
        module = importlib.import_module(FRAMEWORKS[args.framework])
        print(module.run(args.request))
    except ImportError as e:
        print(f"Missing dependency for {args.framework}: {e}. "
              f"Install with: pip install -r requirements-{args.framework}.txt", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
