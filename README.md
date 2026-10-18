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

## Bank Marketing demo dataset

The canonical demo source is the UCI `bank-full.csv` file under
[`datasets/bank/`](D:/Projects/Hackobter/datamind/datasets/bank/). The raw
download is ignored by Git. Load it into Snowflake with:

```powershell
python scripts/load_bank_marketing.py
```

The loader creates `DATAMIND.BANK_MARKETING.BANK_MARKETING`, copies the
semicolon-delimited source file with Snowflake's `PUT` and `COPY INTO`, and
verifies the loaded row count. It performs no local analytics and does not
generate values.

The load has been verified in Snowflake with exactly 45,211 rows. A grouping
query against the Snowflake table also returned the source-backed counts
`no = 39,922` and `yes = 5,289`. These values are not hard-coded into the
application.

If you run the loader yourself, set these local `.env` values so `/api/schema`
describes the Bank Marketing table:

```dotenv
DATAMIND_DATABASE=DATAMIND
DATAMIND_SCHEMA=BANK_MARKETING
SNOWFLAKE_DATABASE=DATAMIND
SNOWFLAKE_SCHEMA=BANK_MARKETING
```

Restart FastAPI and verify `/api/schema` before connecting Gemma. Gemma must
receive that live schema and propose SQL only; the backend validates the SQL,
Snowflake computes the result, and the response exposes the actual returned
rows as evidence.