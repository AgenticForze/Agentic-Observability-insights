"""Multi-framework agent system for researching, scoring and writing about
LLM observability platforms.

The same four roles (researcher, analyst, writer, reviewer) and the same
tools are wired into three frameworks so they can be compared side by side:

- ``agent_system.frameworks.langgraph_flow``
- ``agent_system.frameworks.crewai_flow``
- ``agent_system.frameworks.openai_agents_flow``

``agent_system.core.pipeline`` runs the same workflow with no LLM at all,
which is what CI and the website build use.
"""
