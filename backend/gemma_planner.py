"""Google AI Studio Gemma planner for schema-grounded SQL proposals."""

import json
import os
from typing import Any

from google import genai
from google.genai import types


def _planner_prompt(
    question: str,
    schema_context: list[dict[str, str]],
) -> str:
    schema_text = "\n".join(
        f"- {item['table']}.{item['column']} ({item['data_type']})"
        for item in schema_context
    )
    return f"""
You are the query-planning component of DataMind.
You may propose SQL, but you must never calculate, guess, or return result
rows or numeric answers. Snowflake is the only source of truth for values.

The backend allows only one read-only SELECT query against these fully
qualified approved objects:
- DATAMIND.BANK_MARKETING.BANK_MARKETING
- SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 tables when present in the supplied schema

Use only columns in the supplied schema. Use the exact table and column names.
The source column DEFAULT_VALUE represents the original UCI field "default".
Return JSON only with this shape:
{{
  "sql": "SELECT ... or null",
  "clarification_required": false,
  "clarification_question": null,
  "explanation": "what the SQL measures",
  "assumptions": [],
  "warnings": []
}}

If the question is ambiguous, unsupported, or asks for destructive actions,
set clarification_required to true, provide one focused clarification question,
and set sql to null. Do not put markdown fences around the JSON.

LIVE SCHEMA:
{schema_text}

USER QUESTION:
{question}
""".strip()


def plan_query(
    question: str,
    schema_context: list[dict[str, str]],
) -> dict[str, Any]:
    """Ask Gemma for a schema-aware SQL proposal."""

    api_key = os.getenv("GOOGLE_GENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GOOGLE_GENAI_API_KEY is not configured.")

    model = os.getenv("GEMMA_MODEL", "gemma-3-27b-it").strip()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=_planner_prompt(question, schema_context),
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemma returned an empty planner response.")

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemma returned invalid planner JSON.") from exc

    if not isinstance(result, dict):
        raise ValueError("Gemma planner output must be a JSON object.")

    return result
