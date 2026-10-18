from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PlanStatus = Literal["ok", "clarification_required", "unsupported"]
Aggregation = Literal["none", "sum", "count", "avg", "min", "max", "count_distinct"]
FilterOperator = Literal[
    "eq", "neq", "gt", "gte", "lt", "lte", "contains", "in",
    "between", "date_range", "is_null", "is_not_null",
]
SortDirection = Literal["asc", "desc"]


class StrictModel(BaseModel):
    """Base class: reject unexpected keys rather than silently accepting them."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FilterSpec(StrictModel):
    column: str = Field(min_length=1, max_length=256)
    operator: FilterOperator
    value: Any = None
    second_value: Any = None
    rationale: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_values(self) -> "FilterSpec":
        if self.operator in {"between", "date_range"}:
            if self.value is None or self.second_value is None:
                raise ValueError(f"{self.operator} filters require value and second_value")
        if self.operator in {"is_null", "is_not_null"}:
            if self.value is not None or self.second_value is not None:
                raise ValueError(f"{self.operator} filters must not include values")
        if self.operator == "in" and not isinstance(self.value, list):
            raise ValueError("in filters require value to be a JSON array")
        return self


class SortSpec(StrictModel):
    field: str = Field(min_length=1, max_length=256)
    direction: SortDirection = "desc"


class QueryPlan(StrictModel):
    status: PlanStatus
    intent: str = Field(min_length=1, max_length=1000, description="Brief description of the requested analysis")
    table_names: list[str] = Field(default_factory=list, max_length=20)
    metric: str | None = Field(default=None, max_length=256)
    aggregation: Aggregation = "none"
    group_by: list[str] = Field(default_factory=list, max_length=30)
    filters: list[FilterSpec] = Field(default_factory=list, max_length=50)
    order_by: list[SortSpec] = Field(default_factory=list, max_length=20)
    limit: int | None = Field(default=None, ge=1, le=1000)
    candidate_sql: str | None = Field(default=None, max_length=20000)
    clarification_question: str | None = Field(default=None, max_length=1000)
    assumptions: list[str] = Field(default_factory=list, max_length=30)
    warnings: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="before")
    @classmethod
    def normalize_non_executable_aggregation(cls, data: Any) -> Any:
        if isinstance(data, dict):
            status = data.get("status")
            if status in {"unsupported", "clarification_required"} and data.get("aggregation") is None:
                data = dict(data)
                data["aggregation"] = "none"
        return data

    @model_validator(mode="after")
    def validate_status_contract(self) -> "QueryPlan":
        if self.status == "ok":
            if not self.candidate_sql or not self.candidate_sql.strip():
                raise ValueError("status='ok' requires candidate_sql")
            if not self.table_names:
                raise ValueError("status='ok' requires at least one table name")
            if self.clarification_question:
                raise ValueError("status='ok' must not include clarification_question")
        elif self.status == "clarification_required":
            if not self.clarification_question or not self.clarification_question.strip():
                raise ValueError("clarification_required requires clarification_question")
        return self


class ColumnInfo(StrictModel):
    name: str = Field(min_length=1, max_length=256)
    data_type: str = Field(default="unknown", max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class TableInfo(StrictModel):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=1000)
    columns: list[ColumnInfo] = Field(min_length=1, max_length=500)


class PlannerInput(StrictModel):
    question: str = Field(min_length=2, max_length=2000)
    database_schema: list[TableInfo] = Field(alias="schema", min_length=1, max_length=100)
    conversation_context: list[str] = Field(default_factory=list, max_length=6)
    today: date | None = Field(
        default=None,
        description="Reference date for relative periods like 'last month'. Defaults to today (UTC).",
    )

    @model_validator(mode="after")
    def validate_context(self) -> "PlannerInput":
        if any(len(item) > 2000 for item in self.conversation_context):
            raise ValueError("each conversation_context item must be at most 2000 characters")
        return self
