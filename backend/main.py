
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
ALLOWED_DATABASE = "SNOWFLAKE_SAMPLE_DATA"
ALLOWED_SCHEMA = "TPCH_SF1"
ALLOWED_OBJECTS = {
    (
        ALLOWED_DATABASE,
        ALLOWED_SCHEMA,
    ): ALLOWED_TABLES,
    (
        "DATAMIND",
        "BANK_MARKETING",
    ): {"BANK_MARKETING"},
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
        allowed_tables = ALLOWED_OBJECTS.get(object_key)

        if not allowed_tables or table_name not in allowed_tables:
            raise ValueError(f"Table is not allowed: {table.name}")

        if not table.db or not table.catalog:
            raise ValueError(
                "Tables must use a fully qualified approved database.schema.table "
                "name."
            )

    return tree.sql(dialect="snowflake")


def get_connection():
    connection_options = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
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

    database = os.getenv("SNOWFLAKE_DATABASE", "").strip()
    schema = os.getenv("SNOWFLAKE_SCHEMA", "").strip()

    if not database or not schema:
        raise HTTPException(
            status_code=503,
            detail="Snowflake database and schema are not configured.",
        )

    connection = None
    try:
        connection = get_connection()
        database_sql = quote_identifier(database)

        allowed_tables = ALLOWED_OBJECTS.get(
            (database.upper(), schema.upper()),
            set(),
        )
        if not allowed_tables:
            raise ValueError("The configured database and schema are not allowlisted.")

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
            }
            for row in rows
        ]

        return {
            "status": "ok",
            "database": database,
            "schema": schema,
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