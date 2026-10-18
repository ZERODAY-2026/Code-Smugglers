# DataMind

DataMind is the backend for the PS1 "Talk to Your Data" project. It uses
FastAPI and Snowflake to prepare a schema-grounded natural-language data
agent.

## Current backend

The backend currently provides:

- `GET /health` - service health check.
- `GET /api/test-snowflake` - verifies the configured Snowflake connection.
- `GET /api/test-query` - executes a real sample query against TPC-H data.
- `GET /api/schema` - discovers the configured allowlisted tables and columns.
- `GET /api/test-validator` - exercises the SQL safety policy.
- `POST /api/query` - calls the configured Gemma planner, validates its SQL,
  executes it in Snowflake, and returns actual rows as evidence.

The SQL policy only permits one read-only query against fully qualified tables
in the approved TPC-H schema or Bank Marketing table:

```text
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PART
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PARTSUPP
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION
DATAMIND.BANK_MARKETING.BANK_MARKETING
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

The included Google AI Studio planner exposes a function matching
[`backend/planner_contract.py`](D:/Projects/Hackobter/datamind/backend/planner_contract.py)
and uses the official `google-genai` SDK. Configure it in `.env`:

```dotenv
GEMMA_PLANNER_MODULE=backend.gemma_planner
GEMMA_PLANNER_FUNCTION=plan_query
GEMMA_MODEL=gemma-3-27b-it
GOOGLE_GENAI_API_KEY=your_google_ai_studio_key
```

Create the API key at [Google AI Studio](https://aistudio.google.com/apikey).
Never paste it into chat, source code, or Git. The `.env` file is ignored.
Until this is configured, `POST /api/query` returns `503` rather than
pretending that Gemma ran or inventing a result.

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