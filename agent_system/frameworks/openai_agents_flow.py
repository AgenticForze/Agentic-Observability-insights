"""OpenAI Agents SDK implementation: an orchestrator using specialists as tools.

The orchestrator decides when to call each specialist. This is the most
flexible of the three designs, and the least predictable, so the
orchestrator's instructions spell out the order and the revision limit.
"""
from __future__ import annotations

import os

from ..core import prompts, tools

ORCHESTRATOR = """You coordinate an analysis team. For every request:
1. Call researcher, then analyst with the research brief.
2. Call writer with the analysis.
3. Call reviewer with the writer's output.
4. If the reviewer says REVISE, call writer again with the feedback, then reviewer again. Do this at most twice.
5. Return the final drafts (saved file paths and carousel) followed by the reviewer's verdict."""


def build_orchestrator(model: str | None = None):
    from agents import Agent, function_tool  # OpenAI Agents SDK

    model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    def specialist(role: str, fns):
        return Agent(name=role, instructions=prompts.ROLES[role], model=model,
                     tools=[function_tool(f) for f in fns])

    team = {
        "researcher": specialist("researcher", tools.RESEARCH_TOOLS),
        "analyst": specialist("analyst", tools.ANALYST_TOOLS),
        "writer": specialist("writer", tools.WRITER_TOOLS),
        "reviewer": specialist("reviewer", tools.REVIEWER_TOOLS),
    }
    return Agent(
        name="orchestrator",
        instructions=ORCHESTRATOR,
        model=model,
        tools=[a.as_tool(tool_name=name, tool_description=f"The {name} specialist.")
               for name, a in team.items()],
    )


def run(request: str) -> str:
    from agents import Runner

    result = Runner.run_sync(build_orchestrator(), request, max_turns=30)
    return str(result.final_output)
