"""LangGraph implementation: an explicit state graph with a review loop.

    researcher -> analyst -> writer -> reviewer --APPROVED--> END
                               ^          |
                               +--REVISE--+   (at most MAX_REVISIONS times)

Each node is a tool-calling agent with its role's tools. The graph, not the
prompt, enforces the order and the revision limit, which makes routing
visible in traces.
"""
from __future__ import annotations

import os
from typing import TypedDict

from ..core import prompts, tools

MAX_REVISIONS = 2


class State(TypedDict):
    request: str
    research: str
    analysis: str
    drafts: str
    review: str
    revisions: int


def _make_agent(model, role: str, fns):
    from langchain_core.tools import StructuredTool

    lc_tools = [StructuredTool.from_function(f) for f in fns]
    try:  # LangChain 1.x
        from langchain.agents import create_agent
        return create_agent(model, lc_tools, system_prompt=prompts.ROLES[role])
    except ImportError:  # LangGraph prebuilt (0.x)
        from langgraph.prebuilt import create_react_agent
        return create_react_agent(model, lc_tools, prompt=prompts.ROLES[role])


def _ask(agent, content: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": content}]})
    return result["messages"][-1].content


def build_graph(model=None):
    from langgraph.graph import END, START, StateGraph

    if model is None:
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0)

    researcher = _make_agent(model, "researcher", tools.RESEARCH_TOOLS)
    analyst = _make_agent(model, "analyst", tools.ANALYST_TOOLS)
    writer = _make_agent(model, "writer", tools.WRITER_TOOLS)
    reviewer = _make_agent(model, "reviewer", tools.REVIEWER_TOOLS)

    def research_node(s: State):
        return {"research": _ask(researcher, s["request"])}

    def analyst_node(s: State):
        return {"analysis": _ask(analyst, f"Request:\n{s['request']}\n\nResearch brief:\n{s['research']}")}

    def writer_node(s: State):
        feedback = f"\n\nReviewer feedback to fix:\n{s['review']}" if s.get("review") else ""
        return {"drafts": _ask(writer, f"Request:\n{s['request']}\n\nAnalysis:\n{s['analysis']}{feedback}")}

    def reviewer_node(s: State):
        return {"review": _ask(reviewer, f"Drafts to review:\n{s['drafts']}"),
                "revisions": s.get("revisions", 0) + 1}

    def route(s: State) -> str:
        approved = s["review"].strip().upper().startswith("APPROVED")
        return END if approved or s["revisions"] > MAX_REVISIONS else "writer"

    g = StateGraph(State)
    g.add_node("researcher", research_node)
    g.add_node("analyst", analyst_node)
    g.add_node("writer", writer_node)
    g.add_node("reviewer", reviewer_node)
    g.add_edge(START, "researcher")
    g.add_edge("researcher", "analyst")
    g.add_edge("analyst", "writer")
    g.add_edge("writer", "reviewer")
    g.add_conditional_edges("reviewer", route, {"writer": "writer", END: END})
    return g.compile()


def run(request: str) -> str:
    app = build_graph()
    final = app.invoke({"request": request, "research": "", "analysis": "",
                        "drafts": "", "review": "", "revisions": 0},
                       config={"tags": ["agentic-observability", "langgraph"]})
    return f"{final['drafts']}\n\n---\nReview:\n{final['review']}"
