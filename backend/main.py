
import importlib
import os
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

import snowflake.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.dataset_registry import get_active_dataset

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="DataMind Backend")


MAX_QUESTION_LENGTH = 2000
MAX_RESULT_ROWS = 500


def validate_sql(sql: str) -> str:
    """Validate that SQL contains one read-only query on allowed tables."""

    dataset = get_active_dataset()
    try:
        statements = [
            statement
            for statement in sqlglot.parse(sql, read="snowflake")
            if statement is not None
        ]
    except Exception as exc:
        raise ValueError("Invalid SQL syntax.") from exc

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    tree = statements[0]

    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise ValueError("Only SELECT queries are allowed.")

    for node in tree.walk():
        if isinstance(
            node,
            (
                exp.Insert,
                exp.Update,
                exp.Delete,
                exp.Drop,
                exp.Create,
                exp.Alter,
                exp.Command,
                exp.Merge,
                exp.TruncateTable,
            ),
        ):
            raise ValueError("Only read-only SQL is allowed.")

    cte_names = {
        cte.alias_or_name.upper()
        for cte in tree.find_all(exp.CTE)
        if cte.alias_or_name
    }

    for table in tree.find_all(exp.Table):
        table_name = table.name.upper()

        if table_name in cte_names and not table.db and not table.catalog:
            continue

        object_key = (
            table.catalog.upper() if table.catalog else "",
            table.db.upper() if table.db else "",
        )
        allowed_tables = dataset.objects.get(object_key)

        if not allowed_tables or table_name not in allowed_tables:
            raise ValueError(f"Table is not allowed: {table.name}")

        if not table.db or not table.catalog:
            raise ValueError(
                "Tables must use a fully qualified approved database.schema.table "
                "name."
            )

    return tree.sql(dialect="snowflake")


def get_connection():
    dataset = get_active_dataset()
    connection_options = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": dataset.database,
        "schema": dataset.schema,
        "authenticator": os.getenv(
            "SNOWFLAKE_AUTHENTICATOR", "externalbrowser"
        ),
    }

    if os.getenv("SNOWFLAKE_ROLE"):
        connection_options["role"] = os.environ["SNOWFLAKE_ROLE"]

    return snowflake.connector.connect(
        **connection_options,
    )


def quote_identifier(identifier: str) -> str:
    """Quote a Snowflake identifier after rejecting empty values."""

    if not identifier or not identifier.strip():
        raise ValueError("Snowflake identifiers cannot be empty.")

    return '"' + identifier.replace('"', '""') + '"'


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)


class QueryPlan(BaseModel):
    sql: str | None = None
    clarification_required: bool = False
    clarification_question: str | None = None
    explanation: str = ""
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def get_query_plan(
    question: str,
    schema_context: list[dict[str, str]],
) -> QueryPlan:
    """Call the configured Gemma planner without a fabricated fallback."""

    module_name = os.getenv("GEMMA_PLANNER_MODULE", "").strip()
    function_name = os.getenv("GEMMA_PLANNER_FUNCTION", "plan_query").strip()

    if not module_name:
        raise RuntimeError(
            "Gemma planner is not configured. Set GEMMA_PLANNER_MODULE "
            "and GEMMA_PLANNER_FUNCTION."
        )

    try:
        module = importlib.import_module(module_name)
        planner = getattr(module, function_name)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("Configured Gemma planner could not be loaded.") from exc

    try:
        result: Any = planner(
            question=question,
            schema_context=schema_context,
        )
        return QueryPlan.model_validate(result)
    except Exception as exc:
        raise RuntimeError("Gemma planner returned an invalid plan.") from exc


def execute_query(sql: str) -> dict[str, Any]:
    """Execute approved SQL and return only evidence returned by Snowflake."""

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [item[0] for item in cursor.description or []]
            rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
            query_id = cursor.sfqid

        truncated = len(rows) > MAX_RESULT_ROWS
        rows = rows[:MAX_RESULT_ROWS]
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "warnings": (
                [f"Results were limited to {MAX_RESULT_ROWS} rows."]
                if truncated
                else []
            ),
            "query_id": query_id,
        }
    finally:
        if connection is not None:
            connection.close()


@app.get("/")
def home():
    return {
        "message": "Welcome to DataMind!",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "DataMind Backend",
    }


@app.get("/api/schema")
def discover_schema():
    """Return columns from the configured Snowflake schema."""

    try:
        dataset = get_active_dataset()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    database = dataset.database
    schema = dataset.schema

    connection = None
    try:
        connection = get_connection()
        database_sql = quote_identifier(database)

        allowed_tables = dataset.tables

        query = (
            f"SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE "
            f"FROM {database_sql}.INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s "
            "AND TABLE_NAME IN (%s) "
            "ORDER BY TABLE_NAME, ORDINAL_POSITION"
        )
        table_parameters = ", ".join(["%s"] * len(allowed_tables))
        query = query.replace("(%s)", f"({table_parameters})")

        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (schema, *sorted(allowed_tables)),
            )
            rows = cursor.fetchall()

        columns = [
            {
                "table": row[0],
                "column": row[1],
                "data_type": row[2],
                "qualified_table": (
                    f"{database}.{schema}.{row[0]}"
                ),
            }
            for row in rows
        ]

        return {
            "status": "ok",
            "database": database,
            "schema": schema,
            "dataset": dataset.key,
            "dataset_description": dataset.description,
            "columns": columns,
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Schema discovery error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Schema discovery failed. Check configuration and permissions.",
        )
    finally:
        if connection is not None:
            connection.close()


@app.get("/api/test-snowflake")
def test_snowflake():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT CURRENT_VERSION(), CURRENT_DATABASE(), "
                "CURRENT_SCHEMA(), CURRENT_WAREHOUSE()"
            )
            row = cursor.fetchone()

        return {
            "status": "ok",
            "snowflake_version": row[0],
            "database": row[1],
            "schema": row[2],
            "warehouse": row[3],
        }
    except Exception as exc:
        print(f"Snowflake connection error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Snowflake connection failed. Check the VS Code terminal.",
        )
    finally:
        if connection is not None:
            connection.close()


@app.get("/api/test-query")
def test_query():
    connection = None

    try:
        dataset = get_active_dataset()
        table = sorted(dataset.tables)[0]
        table_sql = ".".join(
            quote_identifier(value)
            for value in (dataset.database, dataset.schema, table)
        )
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_sql} LIMIT 5")

            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()

        return {
            "status": "ok",
            "dataset": dataset.key,
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows)
        }

    except Exception as exc:
        print(f"Test query error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Test query failed. Check the VS Code terminal."
        )

    finally:
        if connection is not None:
            connection.close()


@app.get("/api/test-validator")
def test_validator():
    test_cases = [
        (
            "Safe SELECT",
            "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER LIMIT 5",
        ),
        (
            "Safe WHERE",
            "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER "
            "WHERE C_ACCTBAL > 1000",
        ),
        (
            "Safe CTE",
            "WITH high_balance AS ("
            "SELECT C_NAME FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER "
            "WHERE C_ACCTBAL > 1000) SELECT C_NAME FROM high_balance",
        ),
        (
            "Safe Bank Marketing",
            "SELECT Y, COUNT(*) AS CUSTOMERS "
            "FROM DATAMIND.BANK_MARKETING.BANK_MARKETING GROUP BY Y",
        ),
        (
            "Blocked unqualified table",
            "SELECT * FROM CUSTOMER",
        ),
        (
            "Blocked table",
            "SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SECRET_TABLE",
        ),
        (
            "Blocked DELETE",
            "DELETE FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER",
        ),
        ("Blocked multiple statements", "SELECT 1; SELECT 2"),
    ]

    results = []

    for name, sql in test_cases:
        try:
            validated_sql = validate_sql(sql)
            results.append({
                "test": name,
                "passed": name.startswith("Safe"),
                "result": "Accepted",
                "sql": validated_sql,
            })
        except ValueError as exc:
            results.append({
                "test": name,
                "passed": not name.startswith("Safe"),
                "result": "Rejected",
                "reason": str(exc),
            })

    return {"status": "ok", "results": results}


@app.post("/api/query")
def query_data(request: QueryRequest):
    """Plan, validate, execute, and package an evidence-backed query."""

    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a data question.",
        )

    try:
        schema = discover_schema()
        plan = get_query_plan(question, schema["columns"])
    except HTTPException:
        raise
    except RuntimeError as exc:
        print(f"Query planner error: {exc}")
        raise HTTPException(
            status_code=503,
            detail="The Gemma query planner is not available.",
        ) from exc

    if plan.clarification_required:
        return {
            "status": "clarification_required",
            "question": plan.clarification_question
            or "Please clarify your data question.",
            "sql": None,
            "columns": [],
            "rows": [],
            "explanation": plan.explanation,
            "assumptions": plan.assumptions,
            "warnings": plan.warnings,
            "query_id": None,
        }

    if not plan.sql or not plan.sql.strip():
        raise HTTPException(
            status_code=422,
            detail="The Gemma planner did not provide a query.",
        )

    try:
        approved_sql = validate_sql(plan.sql)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        evidence = execute_query(approved_sql)
    except Exception as exc:
        print(f"Snowflake query error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="The approved query could not be completed in Snowflake.",
        ) from exc

    status = "empty" if not evidence["rows"] else "ok"
    return {
        "status": status,
        "answer": (
            "Snowflake returned no matching rows."
            if status == "empty"
            else "Results were computed from the returned Snowflake rows."
        ),
        "sql": approved_sql,
        "columns": evidence["columns"],
        "rows": evidence["rows"],
        "explanation": plan.explanation,
        "assumptions": plan.assumptions,
        "warnings": plan.warnings + evidence["warnings"],
        "query_id": evidence["query_id"],
    }