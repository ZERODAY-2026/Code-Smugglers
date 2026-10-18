# DataMind

DataMind is the backend for the PS1 "Talk to Your Data" project. It uses
FastAPI and Snowflake to prepare a schema-grounded natural-language data
agent.

## Current backend

The backend currently provides:

- `GET /health` - service health check.
- `GET /api/test-snowflake` - verifies the configured Snowflake connection.
- `GET /api/test-query` - executes a real sample query against TPC-H data.
- `GET /api/schema` - discovers the allowlisted TPC-H tables and columns.
- `GET /api/test-validator` - exercises the SQL safety policy.

The SQL policy only permits one read-only query against fully qualified tables
in `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`:

```text
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PARTSUPP
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION
```

## Local setup

Create a `.env` file in the project root. Keep it out of Git:

```dotenv
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
SNOWFLAKE_AUTHENTICATOR=OAUTH_AUTHORIZATION_CODE
```

Install the backend dependencies in the virtual environment, then start the
API:

```powershell
python -m uvicorn backend.main:app --reload
```

The next integration step is to connect the team's Gemma planner to a
schema-aware `POST /api/query` flow. Gemma must propose a query or request
clarification; the backend will validate and execute only approved SQL and
return actual Snowflake evidence.