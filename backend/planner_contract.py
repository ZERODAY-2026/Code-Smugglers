"""Contract for the team's Gemma query planner.

The planner must return a dictionary accepted by ``QueryPlan`` in
``backend.main``. It must propose SQL or ask for clarification, but must never
return fabricated rows or numerical answers.
"""

from typing import TypedDict


class PlannerResult(TypedDict, total=False):
    sql: str
    clarification_required: bool
    clarification_question: str
    explanation: str
    assumptions: list[str]
    warnings: list[str]


def plan_query(
    question: str,
    schema_context: list[dict[str, str]],
) -> PlannerResult:
    """Interface Person 1's Gemma implementation must replace."""

    raise NotImplementedError(
        "Implement this function with the selected Gemma runtime."
    )
