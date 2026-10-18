"""Load the UCI Bank Marketing CSV into a Snowflake table.

This script copies source CSV values into Snowflake. It does not calculate
answers locally and does not generate or modify dataset values.
"""

import csv
import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
CSV_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "bank"
    / "bank-full.csv"
)
TARGET_DATABASE = os.getenv("DATAMIND_DATABASE", "DATAMIND")
TARGET_SCHEMA = os.getenv("DATAMIND_SCHEMA", "BANK_MARKETING")
TARGET_TABLE = "BANK_MARKETING"

EXPECTED_COLUMNS = [
    "age",
    "job",
    "marital",
    "education",
    "default",
    "balance",
    "housing",
    "loan",
    "contact",
    "day",
    "month",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "poutcome",
    "y",
]


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def qualified_name(database: str, schema: str, table: str) -> str:
    return ".".join(
        quote_identifier(value)
        for value in (database, schema, table)
    )


def validate_source_file() -> int:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Dataset file not found: {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8", newline="") as source:
        reader = csv.reader(source, delimiter=";")
        header = next(reader)
        if header != EXPECTED_COLUMNS:
            raise ValueError(
                "Unexpected Bank Marketing header. "
                f"Expected {EXPECTED_COLUMNS}, received {header}."
            )
        return sum(1 for _ in reader)


def get_connection():
    connection_options = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.getenv("SNOWFLAKE_DATABASE", TARGET_DATABASE),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", TARGET_SCHEMA),
        "authenticator": os.getenv(
            "SNOWFLAKE_AUTHENTICATOR",
            "OAUTH_AUTHORIZATION_CODE",
        ),
    }

    if os.getenv("SNOWFLAKE_ROLE"):
        connection_options["role"] = os.environ["SNOWFLAKE_ROLE"]

    return snowflake.connector.connect(
        **connection_options,
    )


def load_dataset() -> None:
    row_count = validate_source_file()
    connection = get_connection()
    database_sql = quote_identifier(TARGET_DATABASE)
    schema_sql = quote_identifier(TARGET_SCHEMA)
    table_sql = qualified_name(
        TARGET_DATABASE,
        TARGET_SCHEMA,
        TARGET_TABLE,
    )
    stage_sql = qualified_name(
        TARGET_DATABASE,
        TARGET_SCHEMA,
        f"{TARGET_TABLE}_STAGE",
    )
    file_uri = f"file://{CSV_PATH.resolve().as_posix()}"

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_sql}")
            cursor.execute(
                f"CREATE SCHEMA IF NOT EXISTS {database_sql}.{schema_sql}"
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_sql} (
                    age NUMBER,
                    job VARCHAR,
                    marital VARCHAR,
                    education VARCHAR,
                    default_value VARCHAR,
                    balance NUMBER,
                    housing VARCHAR,
                    loan VARCHAR,
                    contact VARCHAR,
                    day NUMBER,
                    month VARCHAR,
                    duration NUMBER,
                    campaign NUMBER,
                    pdays NUMBER,
                    previous NUMBER,
                    poutcome VARCHAR,
                    y VARCHAR
                )
                """
            )
            cursor.execute(f"CREATE STAGE IF NOT EXISTS {stage_sql}")
            cursor.execute(f"TRUNCATE TABLE {table_sql}")
            cursor.execute(
                f"PUT '{file_uri}' @{stage_sql} OVERWRITE = TRUE"
            )
            cursor.execute(
                f"""
                COPY INTO {table_sql}
                FROM @{stage_sql}
                FILE_FORMAT = (
                    TYPE = CSV
                    FIELD_DELIMITER = ';'
                    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                    SKIP_HEADER = 1
                    ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE
                )
                ON_ERROR = 'ABORT_STATEMENT'
                """
            )
            cursor.execute(f"SELECT COUNT(*) FROM {table_sql}")
            loaded_count = cursor.fetchone()[0]

        if loaded_count != row_count:
            raise RuntimeError(
                f"Snowflake loaded {loaded_count} rows, expected {row_count}."
            )
        print(
            f"Loaded {loaded_count} source rows into "
            f"{TARGET_DATABASE}.{TARGET_SCHEMA}.{TARGET_TABLE}."
        )
    finally:
        connection.close()


if __name__ == "__main__":
    load_dataset()
