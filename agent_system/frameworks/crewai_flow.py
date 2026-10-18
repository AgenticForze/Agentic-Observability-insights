"""CrewAI implementation: role-based agents running sequential tasks.

CrewAI models the team directly (role, goal, backstory). Tasks pass context
forward; the reviewer's verdict is the final output. CrewAI has no built-in
conditional loop here, so revision is a single extra writer pass when the
reviewer says REVISE.
"""
from __future__ import annotations

import os

from ..core import prompts, tools


def _wrap(fns):
    from crewai.tools import tool
    return [tool(f.__name__)(f) for f in fns]


def build_crew(request: str, llm: str | None = None, feedback: str = ""):
    from crewai import Agent, Crew, Process, Task

    llm = llm or os.getenv("LLM_MODEL", "gpt-4o-mini")

    def agent(role: str, goal: str, fns):
        return Agent(role=role.title(), goal=goal, backstory=prompts.ROLES[role],
                     tools=_wrap(fns), llm=llm, allow_delegation=False, verbose=False)

    researcher = agent("researcher", "Establish current, sourced facts about relevant platforms", tools.RESEARCH_TOOLS)
    analyst = agent("analyst", "Rank platforms for the audience and recommend build, buy or hybrid", tools.ANALYST_TOOLS)
    writer = agent("writer", "Draft an insight and a validated LinkedIn carousel", tools.WRITER_TOOLS)
    reviewer = agent("reviewer", "Approve or reject drafts against the dataset", tools.REVIEWER_TOOLS)

    t_research = Task(description=f"Research for this request: {request}",
                      expected_output="A research brief with platforms, key facts, staleness and sources.",
                      agent=researcher)
    t_analyse = Task(description=f"Analyse for this request: {request}",
                     expected_output="Top three platforms with scores, trade-offs and a build/buy/hybrid call.",
                     agent=analyst, context=[t_research])
    t_write = Task(description=f"Write the insight and carousel for: {request}."
                               + (f"\nFix this reviewer feedback: {feedback}" if feedback else ""),
                   expected_output="Saved insight path, saved carousel path, and the carousel YAML.",
                   agent=writer, context=[t_analyse])
    t_review = Task(description="Review the drafts. First line must be APPROVED or REVISE.",
                    expected_output="APPROVED or REVISE followed by problems and fixes.",
                    agent=reviewer, context=[t_write])
    return Crew(agents=[researcher, analyst, writer, reviewer],
                tasks=[t_research, t_analyse, t_write, t_review],
                process=Process.sequential, verbose=False)


def run(request: str) -> str:
    result = str(build_crew(request).kickoff())
    if result.strip().upper().startswith("REVISE"):
        result = str(build_crew(request, feedback=result).kickoff())
    return result
