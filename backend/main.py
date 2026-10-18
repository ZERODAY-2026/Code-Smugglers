
import os
from pathlib import Path

import sqlglot
from sqlglot import exp

import snowflake.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="DataMind Backend")


ALLOWED_TABLES = {
    "CUSTOMER",
    "ORDERS",
    "LINEITEM",
    "PART",
    "PARTSUPP",
    "SUPPLIER",
    "NATION",
    "REGION",
}


def validate_sql(sql: str) -> str:
    """Validate that SQL contains one read-only query on allowed tables."""

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
        if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop,
                             exp.Create, exp.Alter, exp.Command)):
            raise ValueError("Only read-only SQL is allowed.")

    for table in tree.find_all(exp.Table):
        if table.name.upper() not in ALLOWED_TABLES:
            raise ValueError(f"Table is not allowed: {table.name}")

        if table.db and table.db.upper() != "TPCH_SF1":
            raise ValueError("Only the TPCH_SF1 schema is allowed.")

        if table.catalog and table.catalog.upper() != "SNOWFLAKE_SAMPLE_DATA":
            raise ValueError("Only SNOWFLAKE_SAMPLE_DATA is allowed.")

    return tree.sql(dialect="snowflake")


def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        authenticator=os.getenv(
            "SNOWFLAKE_AUTHENTICATOR", "externalbrowser"
        ),
    )


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
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    C_CUSTKEY,
                    C_NAME,
                    C_ACCTBAL,
                    C_MKTSEGMENT
                FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
                ORDER BY C_ACCTBAL DESC
                LIMIT 5
            """)

            columns = [item[0] for item in cursor.description]
            rows = cursor.fetchall()

        return {
            "status": "ok",
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
        ("Safe SELECT", "SELECT C_NAME FROM CUSTOMER LIMIT 5"),
        ("Safe WHERE", "SELECT C_NAME FROM CUSTOMER WHERE C_ACCTBAL > 1000"),
        ("Blocked DELETE", "DELETE FROM CUSTOMER"),
        ("Blocked table", "SELECT * FROM SECRET_TABLE"),
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