# DataMind Frontend Handoff

This document is the implementation contract for Person 3. It describes the
current backend, the frontend responsibilities, the API shapes, and the
acceptance criteria for the PS1 "Talk to Your Data" application.

The frontend must be an evidence-first natural-language analytics interface.
It must never calculate, invent, or silently transform analytics results.
Every displayed result must come from the DataMind API response.

## 1. Product goal

Build a frontend where a user can:

1. Enter a natural-language question about the active dataset.
2. Submit the question to the FastAPI backend.
3. See the answer status.
4. Inspect the generated SQL.
5. Inspect the actual rows returned by Snowflake.
6. Read the explanation, assumptions, warnings, and Snowflake query ID.
7. Respond to clarification questions.
8. Clearly see unsupported questions, empty results, validation failures, and
   service errors.

The main user flow is:

```text
Natural-language question
        |
        v
POST /api/query
        |
        v
Gemma proposes SQL
        |
        v
Backend validates SQL
        |
        v
Snowflake computes the result
        |
        v
Frontend renders API evidence
```

Gemma does not provide the final numeric answer. Snowflake is the source of
truth for all result rows and values.

## 2. Current repository structure

```text
datamind/
|-- backend/
|   |-- __init__.py                         # Python package marker if present
|   |-- main.py                             # FastAPI app and API routes
|   |-- dataset_registry.py                 # Active dataset configuration
|   |-- gemma_planner.py                    # Verified Google Gen AI planner
|   |-- person1_adapter.py                  # Person 1 planner adapter
|   |-- planner_contract.py                 # Planner interface documentation
|   |-- person1_planner/
|       |-- __init__.py
|       |-- gemma_planner.py                # Person 1 robust planner
|       |-- sql_sanity.py                   # Token-level candidate SQL checks
|       |-- schemas/
|           |-- __init__.py
|           |-- ai_plan.py                   # Strict planner Pydantic models
|-- datasets/
|   |-- README.md                           # Dataset provenance and loading notes
|   |-- bank/                               # Ignored local UCI raw files
|   |-- bank-additional/                    # Ignored local UCI raw files
|-- scripts/
|   |-- load_bank_marketing.py              # UCI CSV -> Snowflake loader
|-- tests/
|   |-- conftest.py
|   |-- test_dataset_reuse.py               # Dataset switching and SQL policy tests
|-- info/                                   # Problem statement and project references
|-- .env                                    # Local secrets; never commit or expose
|-- .env.example                            # Safe configuration template
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- FRONTEND_HANDOFF.md                     # This document
```

The frontend may be implemented as a new sibling directory, for example:

```text
datamind/
|-- frontend/
|   |-- package.json
|   |-- src/
|   |   |-- api/
|   |   |-- components/
|   |   |-- types/
|   |   |-- App.*
|   |-- ...
```

Do not move or rewrite the backend to build the frontend.

## 3. Starting the backend

From PowerShell:

```powershell
cd D:\Projects\Hackobter\datamind
D:\Projects\Hackobter\datamind\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The API base URL is:

```text
http://127.0.0.1:8000
```

OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Only run one Uvicorn process on port 8000. If the browser reports connection
refused, start the backend. If Uvicorn reports that the port is already in
use, use the existing server or stop the process that owns port 8000.

## 4. API endpoints

### 4.1 `GET /health`

Use this to show backend availability.

Successful response:

```json
{
  "status": "ok",
  "service": "DataMind Backend"
}
```

### 4.2 `GET /api/schema`

Use this on application startup to show the active dataset and optionally
display a compact "Data source" panel.

Successful response:

```json
{
  "status": "ok",
  "database": "DATAMIND",
  "schema": "BANK_MARKETING",
  "dataset": "bank_marketing",
  "dataset_description": "UCI Bank Marketing campaign data",
  "columns": [
    {
      "table": "BANK_MARKETING",
      "column": "AGE",
      "data_type": "NUMBER",
      "qualified_table": "DATAMIND.BANK_MARKETING.BANK_MARKETING"
    },
    {
      "table": "BANK_MARKETING",
      "column": "Y",
      "data_type": "TEXT",
      "qualified_table": "DATAMIND.BANK_MARKETING.BANK_MARKETING"
    }
  ]
}
```

Do not assume that the active dataset is always Bank Marketing. The backend
also supports TPC-H through configuration. Render the `dataset`,
`dataset_description`, `database`, and `schema` values returned by this
endpoint.

### 4.3 `POST /api/query`

Request:

```http
POST /api/query
Content-Type: application/json
```

```json
{
  "question": "How many customers subscribed to a term deposit?"
}
```

The question must contain 1 to 2,000 characters. Trim whitespace before
submitting and prevent empty submissions.

#### Successful result: `status = "ok"`

Example:

```json
{
  "status": "ok",
  "answer": "Results were computed from the returned Snowflake rows.",
  "sql": "SELECT COUNT(*) FROM DATAMIND.BANK_MARKETING.BANK_MARKETING WHERE Y = 'yes'",
  "columns": ["COUNT(*)"],
  "rows": [[5289]],
  "explanation": "Counts the number of customers who subscribed to a term deposit by filtering for 'yes' in the Y column.",
  "assumptions": [
    "Assuming that the value 'yes' in the Y column indicates a successful subscription to a term deposit."
  ],
  "warnings": [],
  "query_id": "01c7cf6c-0002-35f0-0000-000fe7e6c615"
}
```

Render:

- A positive result/status indicator.
- The answer summary.
- A result table using `columns` and `rows`.
- SQL in a code block with copy action.
- Explanation.
- Assumptions, if non-empty.
- Warnings, if non-empty.
- Query ID in an evidence/details section with copy action.

Do not hard-code `5289`. It is only an example of a value returned by
Snowflake.

#### Empty result: `status = "empty"`

Example shape:

```json
{
  "status": "empty",
  "answer": "Snowflake returned no matching rows.",
  "sql": "SELECT ...",
  "columns": ["..."],
  "rows": [],
  "explanation": "...",
  "assumptions": [],
  "warnings": [],
  "query_id": "..."
}
```

Render an explicit empty-state message. Do not display an error and do not
claim that the query failed.

#### Clarification: `status = "clarification_required"`

Example shape:

```json
{
  "status": "clarification_required",
  "question": "Which month or date range should I use?",
  "sql": null,
  "columns": [],
  "rows": [],
  "explanation": "...",
  "assumptions": [],
  "warnings": [],
  "query_id": null
}
```

Render the clarification question prominently. Keep the original question in
the conversation history and let the user submit a new, more specific
question. Do not render a result table for this response.

#### Unsupported question: `status = "unsupported"`

Example shape:

```json
{
  "status": "unsupported",
  "question": "This question cannot be answered from the active dataset.",
  "sql": null,
  "columns": [],
  "rows": [],
  "explanation": "...",
  "assumptions": [],
  "warnings": ["..."],
  "query_id": null
}
```

Render this as a clear limitation, not as a successful answer.

### 4.4 `GET /api/test-snowflake`

Diagnostic endpoint for development only. It returns the Snowflake version,
current database, schema, and warehouse. It does not need to be part of the
main user interface.

### 4.5 `GET /api/test-query`

Diagnostic endpoint for development only. It returns five rows from the first
table in the active configured dataset. It does not need to be part of the
main user interface.

### 4.6 `GET /api/test-validator`

Diagnostic endpoint for development only. It reports SQL allowlist test cases.
It does not need to be part of the main user interface.

## 5. TypeScript types

Use types equivalent to these in the frontend:

```ts
export type QueryStatus =
  | "ok"
  | "empty"
  | "clarification_required"
  | "unsupported";

export interface SchemaColumn {
  table: string;
  column: string;
  data_type: string;
  qualified_table: string;
}

export interface SchemaResponse {
  status: "ok";
  database: string;
  schema: string;
  dataset: string;
  dataset_description: string;
  columns: SchemaColumn[];
}

export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  status: QueryStatus;
  answer?: string;
  question?: string;
  sql: string | null;
  columns: string[];
  rows: unknown[][];
  explanation: string;
  assumptions: string[];
  warnings: string[];
  query_id: string | null;
}

export interface ApiError {
  detail: string | Array<{
    type: string;
    loc: Array<string | number>;
    msg: string;
  }>;
}
```

Rows must be displayed by pairing:

```ts
const displayRows = response.rows.map((row) =>
  Object.fromEntries(
    response.columns.map((column, index) => [column, row[index]])
  )
);
```

Do not infer column names from the question or from hard-coded dataset
knowledge.

## 6. Required UI states

Implement these states explicitly:

1. **Initial**
   - Question input.
   - Example questions.
   - Dataset/source indicator.
   - Submit button enabled only for non-empty input.

2. **Loading**
   - Disable duplicate submissions.
   - Show that Gemma is planning and Snowflake is computing.
   - Keep the submitted question visible.

3. **Success**
   - Show result summary, data table, SQL, explanation, metadata, and query ID.

4. **Empty**
   - Show that Snowflake returned no matching rows.

5. **Clarification required**
   - Show the focused clarification question.
   - Allow the user to submit a refined question.

6. **Unsupported**
   - Explain that the active schema cannot answer the question.
   - Preserve warnings and assumptions.

7. **Validation/API error**
   - Show a user-friendly error.
   - Preserve the HTTP status in development diagnostics.
   - Never display a fake answer.

8. **Backend unavailable**
   - Show a connection message for `fetch` failures or HTTP 503.
   - Suggest checking that FastAPI is running at `http://127.0.0.1:8000`.

## 7. Recommended component structure

The exact framework is Person 3's choice. A practical component breakdown is:

```text
src/
|-- api/
|   |-- client.ts              # fetch wrapper and typed endpoint functions
|   |-- types.ts               # API interfaces above
|-- components/
|   |-- AppShell.*
|   |-- DatasetBadge.*
|   |-- QuestionComposer.*
|   |-- ConversationView.*
|   |-- QueryMessage.*
|   |-- ResultTable.*
|   |-- SqlPanel.*
|   |-- EvidencePanel.*
|   |-- WarningList.*
|   |-- EmptyState.*
|   |-- ErrorState.*
|-- App.*
```

The API client should expose functions similar to:

```ts
export async function getHealth(): Promise<HealthResponse>;
export async function getSchema(): Promise<SchemaResponse>;
export async function askQuestion(
  request: QueryRequest
): Promise<QueryResponse>;
```

Use one shared API base URL:

```ts
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
```

If the frontend is served by a separate development server, either configure
a development proxy or add CORS middleware to FastAPI. Do not use a browser
proxy that hides API failures. The production deployment must configure the
real backend URL through an environment variable.

## 8. Rendering rules

### SQL

- Display the exact `sql` string returned by the backend.
- Use syntax highlighting if available.
- Add a copy button.
- Do not allow arbitrary SQL execution from the frontend.
- Do not add client-side SQL editing to the MVP.

### Rows

- Use the returned `columns` order.
- Render null values as an explicit visual value such as `—`.
- Escape text safely.
- Support horizontal scrolling for wide tables.
- Display a row count based on `rows.length`.
- If a warning says results were limited to 500 rows, show the warning near
  the table.

### Explanation and assumptions

- Show the explanation after the result.
- Show assumptions in a separate disclosure/card.
- Never rewrite assumptions into stronger claims.

### Query ID

- Show it as an evidence/reference identifier.
- Provide a copy button.
- Do not call it a fabricated answer or model response ID.

### Warnings

- Warnings must be visually distinct from errors.
- Never hide non-empty warnings.

## 9. Example questions for the UI

These are examples only. The frontend must send them to the API and render
the returned values:

```text
How many customers subscribed to a term deposit?
```

```text
What is the subscription rate by job?
```

```text
How does housing-loan status relate to term-deposit subscription?
```

```text
Which month had the highest number of successful campaigns?
```

Do not show expected numeric answers in the UI. The backend and Snowflake
must provide the values at runtime.

## 10. Error handling contract

### HTTP 400

Usually means unsafe or invalid SQL was rejected. Show:

```text
The generated query could not be accepted safely. Please rephrase your question.
```

Do not expose internal parser details in the normal UI, but log them in
development if appropriate.

### HTTP 422

Usually means an invalid request or a planner did not produce a usable query.
Show:

```text
The question could not be converted into a usable data query.
```

### HTTP 503

Means Gemma, Snowflake, configuration, or schema discovery is unavailable.
Show:

```text
DataMind is temporarily unavailable. Check the backend connection and try again.
```

### Network failure

Show a connection error with a retry action. Do not clear the conversation.

## 11. Security and trust requirements

- Never put `GOOGLE_GENAI_API_KEY` in frontend code.
- Never put Snowflake credentials in frontend code.
- Never commit `.env`.
- Do not send credentials from the browser.
- Treat all SQL and result text as backend-provided content.
- Do not execute SQL in the browser.
- Do not calculate an answer from raw CSV files.
- Do not replace an API error with a successful-looking empty response.
- Render user/model text safely to prevent HTML/script injection.

## 12. Backend/frontend integration caveat: CORS

The current backend is primarily intended to run locally at port 8000. If the
frontend uses another origin, such as `http://localhost:5173`, the browser
may block requests unless one of these is used:

1. A frontend development proxy that forwards `/api` and `/health` to
   `http://127.0.0.1:8000`; or
2. FastAPI CORS middleware configured for the exact frontend origin.

Prefer a development proxy for the first local demo. Do not use
`Access-Control-Allow-Origin: *` together with credentials.

## 13. Acceptance checklist for Person 3

The frontend is ready for integration when:

- [ ] The app starts with one documented command.
- [ ] The backend URL is configurable.
- [ ] Startup checks `/health` and shows service state.
- [ ] Startup loads `/api/schema` and displays the active dataset.
- [ ] A user can submit a natural-language question.
- [ ] Loading state prevents duplicate submissions.
- [ ] A successful response renders actual `rows` and `columns`.
- [ ] SQL is visible and copyable.
- [ ] Explanation is visible.
- [ ] Assumptions are visible when present.
- [ ] Warnings are visible when present.
- [ ] Query ID is visible and copyable.
- [ ] Empty responses have a dedicated empty state.
- [ ] Clarification responses have a dedicated clarification state.
- [ ] Unsupported responses have a dedicated unsupported state.
- [ ] 400, 422, 503, and network errors are handled.
- [ ] No API key or Snowflake secret appears in frontend code.
- [ ] No result values are hard-coded.
- [ ] The UI works when the active dataset is changed from Bank Marketing to
      TPC-H by backend configuration.
- [ ] The app is usable at a demo screen size.

## 14. Suggested prompt for Person 3's coding AI

Copy this prompt into the frontend coding AI:

```text
You are implementing the Person 3 frontend for the DataMind project.
Read FRONTEND_HANDOFF.md completely and follow it as the API contract.

Build a polished evidence-first natural-language analytics UI. Use the
backend at VITE_API_BASE_URL, defaulting to http://127.0.0.1:8000.

Requirements:
- On startup call GET /health and GET /api/schema.
- Provide a question composer and example questions.
- Submit POST /api/query with {"question": "..."}.
- Render status values ok, empty, clarification_required, and unsupported
  as separate UI states.
- For status ok, render answer, actual columns/rows, exact SQL, explanation,
  assumptions, warnings, and query_id.
- Treat rows as unknown[][] and map them using the returned columns array.
- Handle HTTP 400, 422, 503, network errors, loading, and retry.
- Never calculate or hard-code result values.
- Never expose API keys or Snowflake credentials.
- Make SQL and query_id copyable.
- Make the result table horizontally scrollable and safely render nulls/text.
- Keep the UI modular and accessible.
- Add tests for the API client and every response state.

Do not rewrite the backend. Do not add mock analytics results to the
production UI. Use a development API proxy if needed for CORS.
```

