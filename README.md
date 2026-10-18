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

The SQL policy only permits one read-only query against fully qualified
tables in the active dataset selected by `DATAMIND_DATASET`.

## Local setup

Create a `.env` file in the project root. Keep it out of Git. Select either
supported dataset without changing Python code:

```dotenv
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=DATAMIND
SNOWFLAKE_SCHEMA=BANK_MARKETING
SNOWFLAKE_AUTHENTICATOR=OAUTH_AUTHORIZATION_CODE
DATAMIND_DATASET=bank_marketing
```

Install the backend dependencies in the virtual environment, then start the
API:

```powershell
D:\Projects\Hackobter\datamind\.venv\Scripts\python.exe -m pip install -r requirements.txt
D:\Projects\Hackobter\datamind\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The same schema-aware `POST /api/query` flow works for both datasets. The
backend discovers the active Snowflake schema, asks Gemma for a SQL proposal,
validates it against only the active dataset, and returns actual Snowflake
evidence.

To switch to TPC-H, use:

```dotenv
DATAMIND_DATASET=tpch
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
```

The registry is defined in
[`backend/dataset_registry.py`](D:/Projects/Hackobter/datamind/backend/dataset_registry.py).
It controls the active Snowflake connection, schema discovery, SQL allowlist,
and dataset context supplied to Gemma. Adding another dataset means adding a
registry entry rather than changing the query endpoint.

The integrated Person 1 planner exposes a function matching
[`backend/planner_contract.py`](D:/Projects/Hackobter/datamind/backend/planner_contract.py)
through [`backend/person1_adapter.py`](D:/Projects/Hackobter/datamind/backend/person1_adapter.py).
It applies Person 1's strict JSON contract, schema-reference checks, repair
logic, retries, caching, and token-level SQL sanity checks. The final
Snowflake AST allowlist in `backend/main.py` remains authoritative. For
Google AI Studio, the adapter uses the official `google-genai` SDK because
that is the verified transport for the selected Gemma model:

Configure it in `.env`:

```dotenv
GEMMA_PLANNER_MODULE=backend.person1_adapter
GEMMA_PLANNER_FUNCTION=plan_query
GEMMA_MODEL=gemma-4-31b-it
GOOGLE_GENAI_API_KEY=your_google_ai_studio_key
GEMMA_PROVIDER=google_genai
```

The alternate Person 1 OpenAI-compatible transport remains available by
setting `GEMMA_PROVIDER=openai_compatible`, `GEMMA_MODEL`, and
`GEMMA_BASE_URL`.

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

For a clean UCI download without requiring a browser login, the optional
`ucimlrepo` dependency can fetch dataset 222:

```python
from ucimlrepo import fetch_ucirepo

bank_marketing = fetch_ucirepo(id=222)
print(bank_marketing.metadata.num_instances)
print(bank_marketing.data.original)
```

`ucimlrepo` is only for reproducible source acquisition or tests. The
application still uses Snowflake as its analytics source and never calculates
API answers from the downloaded dataframe.

## Reuse tests

Run the configuration and SQL-policy tests with:

```powershell
D:\Projects\Hackobter\datamind\.venv\Scripts\python.exe -m pytest tests -q
```

The tests switch between `bank_marketing` and `tpch` using configuration and
verify that a query from one dataset cannot access the other dataset.