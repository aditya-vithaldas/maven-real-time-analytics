# Build specification — voice commerce analyst

Status: the four-tab local training demonstration is implemented in server.py and web/. Each mode has an isolated visible prompt, actual DuckDB tools, a fixed Gemini 3.8 Flash text model, and the fixed Gemini 3.8 Live talk path. It generates SQL directly and validates safety; it does not yet compile a constrained analytical intent or automatically perform independent business-correctness review. The remaining sections preserve broader product direction, not claims of implemented features.

## Outcome and initial flow

A user opens the local app, selects the Meridian sample data, and asks a question by voice or text. The app shows a database-derived answer and an appropriate chart, gives a short spoken answer, and preserves context for follow-up investigation. The same query path serves voice and text.

First build: sample DuckDB, typed questions, verified results, then live voice. Subsequent work: uploaded sources, proactive monitoring, workspace memory, and connectors. Prioritize a fully working core flow before those additions.

## Components and contracts

- Browser interface: microphone control, transcript, connection state, answer card/chart, three investigation choices when relevant, and evidence/details.
- Backend: keeps the Gemini credential server-side, owns model configuration and query execution, and issues limited-lived browser credentials if the selected voice integration requires them.
- Context loader: principles.md, domain-intelligence.md, schema.json, current selected answer, and the latest five questions/results. Keep context available across voice reconnects.
- Planner: produces structured intent with metric, aggregation, grain, date range, status filter, dimensions, assumptions, and chart type. Voice tool requests and typed requests use this contract.
- Query executor: compiles supported intents into SELECT/CTE queries and runs DuckDB read-only. Limit returned chart groups and execution time; prevent file reads, extension loading, external/network access, system-table queries, and mutations. Do not trust a SELECT prefix check alone.
- Validator: checks schema and types, date range, metric grain, status filter, finite output values, and additive breakdown/control totals. Principle 10 requires independent intent review; implement it explicitly or document any accepted latency tradeoff before claiming complete compliance. Deterministic checks alone do not prove correct question interpretation.
- Presenter: produces answer text/speech only from returned results and recorded assumptions. Choose a number for a single-date aggregate, line for time series, and bars for category comparisons.

Proposed endpoints: GET /health, GET /schema, POST /query, and POST /voice/session. A query response should include request ID, resolved intent, SQL/evidence, rows, chart configuration, spoken summary, assumptions, and validation outcome. These are proposed contracts, not existing endpoints.

## Voice behavior

Expose listening, transcribing, querying, speaking, interrupted, and disconnected states. Cancel obsolete speech/results when the user interrupts. Preserve conversation state on reconnect. Keep an obvious text fallback. Use the currently available Gemini model verified against the account; put the selected model in server configuration rather than inventing a model ID here.

## Demonstration and acceptance

Use examples/questions.json as deterministic fixtures and calculate expected answers from the actual database. Verify: daily sales, monthly trend, regional/category breakdown, follow-up scope preservation, yesterday resolution, orders versus units, missing funnel data, and synthetic competitor context. Verify one complete microphone exchange, interruption, and reconnect before calling live voice ready. Never hardcode demonstration answers into the product.

## Later capabilities

A proactive service needs saved watch definitions, scheduled evaluation, known baselines, instrumentation gaps, evidence, deduplication, and owned follow-up actions. Workspace learning should preserve version history and distinguish user contributions from measured data. Implement external connectors only when explicitly part of the build scope; they are not needed for the local demonstration.
