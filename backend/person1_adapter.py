"""Adapter from the Person 1 async planner contract to DataMind's API."""

import asyncio
import os
from datetime import date
from typing import Any

from backend.person1_planner.gemma_planner import (
    GemmaPlanner,
    GemmaPlannerError,
    _check_plan_references,
    _clean_candidate_sql,
)
from backend.person1_planner.schemas.ai_plan import QueryPlan


def _schema_tables(schema_context: list[dict[str, str]]) -> list[dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for column in schema_context:
        qualified = column.get("qualified_table", "")
        table_name = column["table"]
        table = tables.setdefault(
            qualified,
            {
                "name": qualified,
                "description": None,
                "columns": [],
            },
        )
        table["columns"].append(
            {
                "name": column["column"],
                "data_type": column["data_type"],
            }
        )
    return list(tables.values())


def _planner_config() -> dict[str, Any]:
    provider = os.getenv("GEMMA_PROVIDER", "google_genai").strip()
    model = os.getenv("GEMMA_MODEL", "").strip()
    api_key = os.getenv("GOOGLE_GENAI_API_KEY", "").strip()
    if provider == "google_genai" and not api_key:
        raise GemmaPlannerError("GOOGLE_GENAI_API_KEY is not configured.")
    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": os.getenv("GEMMA_BASE_URL") or None,
        "max_repairs": int(os.getenv("GEMMA_MAX_REPAIRS", "1")),
        "max_retries": int(os.getenv("GEMMA_MAX_RETRIES", "2")),
    }


def plan_query(
    question: str,
    schema_context: list[dict[str, str]],
) -> dict[str, Any]:
    """Run Person 1's planner and return the existing API's plan shape."""

    if os.getenv("GEMMA_PROVIDER", "google_genai").strip() == "google_genai":
        return _plan_with_verified_google_sdk(question, schema_context)

    request = {
        "question": question,
        "schema": _schema_tables(schema_context),
        "today": date.today().isoformat(),
    }

    async def run() -> dict[str, Any]:
        planner = GemmaPlanner(**_planner_config())
        try:
            plan = await planner.plan(request)
            return {
                "status": plan.status,
                "sql": plan.candidate_sql,
                "clarification_required": plan.status
                in {"clarification_required", "unsupported"},
                "clarification_question": plan.clarification_question
                or (
                    plan.warnings[0]
                    if plan.status == "unsupported" and plan.warnings
                    else None
                ),
                "explanation": plan.intent,
                "assumptions": plan.assumptions,
                "warnings": plan.warnings,
            }
        finally:
            await planner.aclose()

    try:
        return asyncio.run(run())
    except GemmaPlannerError:
        raise
    except RuntimeError as exc:
        raise GemmaPlannerError(
            "The planner could not start in the current execution context."
        ) from exc


def _plan_with_verified_google_sdk(
    question: str,
    schema_context: list[dict[str, str]],
) -> dict[str, Any]:
    """Use the working Google SDK, then apply Person 1's strict checks."""

    from backend.gemma_planner import plan_query as sdk_plan_query

    raw = sdk_plan_query(question=question, schema_context=schema_context)
    status = raw.get("status", "ok")
    if status == "clarification_required" or raw.get("clarification_required"):
        return {
            **raw,
            "status": "clarification_required",
            "sql": None,
        }
    if not raw.get("sql"):
        return {
            **raw,
            "status": "unsupported",
            "sql": None,
        }

    table_names = sorted(
        {
            item["qualified_table"]
            for item in schema_context
            if item.get("qualified_table")
        }
    )
    plan = QueryPlan.model_validate(
        {
            "status": "ok",
            "intent": raw.get("explanation") or "Answer the user's data question.",
            "table_names": table_names,
            "candidate_sql": _clean_candidate_sql(raw["sql"]),
            "assumptions": raw.get("assumptions", []),
            "warnings": raw.get("warnings", []),
        }
    )
    schema = _schema_tables(schema_context)
    _check_plan_references(plan, schema)
    return {
        "status": plan.status,
        "sql": plan.candidate_sql,
        "clarification_required": False,
        "clarification_question": None,
        "explanation": plan.intent,
        "assumptions": plan.assumptions,
        "warnings": plan.warnings,
    }
