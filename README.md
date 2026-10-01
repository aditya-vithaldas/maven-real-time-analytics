# Maven Real-Time Analytics

A local voice analytics training demo that compares four levels of model context over the same Meridian synthetic e-commerce database. Ask the same question in each tab to see how database structure, query guidance, and domain intelligence affect the answer. The interface shows one primary result and measures time to first speech for voice.

The repository includes the application, runtime prompts, principles, domain intelligence, workflows, schema, dataset generator, and benchmark reports. API credentials, database binaries, installed dependencies, and local cloud download records stay outside Git.

See the [prompt and knowledge file guide](prompts/README.md) for the separate app-building prompt, four Gemini runtime prompts, and supporting principles/domain/workflow documents.

## Start from a fresh clone

You need Python 3.12, Node.js with npm, and a Gemini API key with access to the configured `gemini-3.8-live` and `gemini-3.8-flash` models. The application runs locally and uses Gemini remotely for model responses.

```sh
git clone https://github.com/aditya-vithaldas/maven-real-time-analytics.git
cd maven-real-time-analytics
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Add your key to `GEMINI_API_KEY` in `.env`. Keep the default `DUCKDB_PATH=./data/ecommerce.duckdb` for the generated dataset. Then create the data and launch the app:

```sh
(cd dataset-generator && npm ci)
DATA_DIR=./data DEMO_SCALE=1 node dataset-generator/build-demo.mjs
.venv/bin/python check_setup.py
.venv/bin/python server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Allow microphone access to use Start talking; typed questions also work. On macOS, `start.command` starts the app after setup.

The generator replaces its tables. Run it in a fresh data directory when preserving an existing database; see the regeneration instructions below.

## Dataset and local files

- Database: `data/ecommerce.duckdb`, 10 million rows across 12 tables.
- Trading period: **30 September 2025 through 29 September 2026**, inclusive (365 days).
- Schema, relationships, category catalog, and metric definitions: `data/schema.json`.
- Gemini key and database path: your local `.env` (excluded from Git).
- Python environment and dependencies: your local `.venv`, installed from `requirements.txt`.

The included Meridian v5 generator creates orders, items, customers, products, sessions, payments, shipments, calendar, regions, categories, 60 business events, and 5,840 market snapshots. Customer signup and shipment dates can fall outside the trading period. All records, business events, and competitor snapshots are synthetic. No Google Cloud credentials are needed to generate or query the local database. Start with [local-assets.md](local-assets.md) for the complete build pack.

## Run the four-tab demo

```sh
.venv/bin/python server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). This is local-only; nothing is deployed. The compact layout is ready for recording a training/demo video, with a fixed model and no view toggles.

| Tab | Knowledge given to the model |
| --- | --- |
| Runtime discovery | No supplied structure; discovers raw tables and columns using runtime database tools. |
| Schema only | Table names, columns, and SQL types; no commerce meanings or query recipes. |
| Guided queries | Structure plus field meanings, relationships, grain, and key query recipes. |
| Domain + workflows | All of the above plus principles, commerce intelligence, and investigation workflows. |

The right panel is labelled **Gemini runtime prompt**. It starts with short cumulative summaries: Tab 1 provides A (database access); Tab 2 inherits Tab 1 and adds B (structure); Tab 3 inherits Tab 2 and adds C/D (field meanings and joins/query recipes); Tab 4 inherits Tab 3 and adds E/F (principles/domain intelligence and workflows). Each tab shows only its additions, followed by a separator and the complete exact prompt. The summaries help the audience understand what each level provides without reading the full prompt. The small document/code icon at the top opens the **app-building prompt**, a consolidated rebuild brief saved in `prompts/app-build.md`, with Copy, Close, and Escape support. It is displayed only when opened and is never sent to Gemini as runtime context.

The exact system prompt is visible and copyable inside every tab, and saved in `prompts/01-runtime-discovery.md` through `prompts/04-domain-workflows.md`. Runtime discovery uses a minimal prompt with no supplied schema or business guidance. Schema only adds the raw structure to equally brief instructions; the third and fourth tabs retain detailed guidance. All prompts require brief responses, database-backed results, read-only access, one primary widget, and the fixed live engine. Every tab queries `data/ecommerce.duckdb`. Each tab keeps separate conversation context. Reloading the page starts a fresh demo session. Switching tabs stops the microphone and closes the current live session.

**Talk path:** click Start talking and allow microphone access. All four use **Google Gemini 3.8 Live (`gemini-3.8-live`)**, with short native spoken replies, transcripts, and database tools. The permanent API key stays server-side; the browser receives an expiring single-session token. A stopped/disconnected Live session starts fresh on reconnect; existing on-screen messages remain, but are not silently imported into a new Live connection. Typed conversation history is separate from Live history.

**Text path:** uses the fixed Gemini 3.8 Flash model. Model selection, Reset tab, and presentation/standard view controls are removed from the demo. Hold the question constant across tabs for the clearest context comparison. The main body shows only the current question and one primary result: a total-number card, time-series line graph, category bar chart, or detail table. The model selects a widget from an actual query result via show_widget; it cannot supply invented widget data. Conversation history is preserved internally for follow-ups, without a chat feed. The top toolbar shows one timing: **time to first speech** for voice, measured from the end of the user’s question to the first non-silent assistant audio scheduled for playback. It freezes at speech onset. Output transcripts and the end of the spoken reply do not stop or extend this timer. Server VAD audio offsets are used when provided; otherwise microphone activity estimates the question end. Typed requests are separately labelled **Text completion time** because that endpoint returns the complete reply. The narrow side panel is devoted to the current tab’s prompt. The workspace fills the window, with a compact toolbar and input controls that stay visible on desktop. SQL/tool evidence remains expandable under the current result. The introductory heading and masthead are removed to focus on the workspace. No canned answers or expected fixture values are injected into prompts.

Query safety is enforced using a parsed SQL allowlist, read-only DuckDB, disabled external access, a query timeout, and bounded results. This does not prove the business meaning of a generated query. Independent model review described in the original principles is not automatically implemented, and the fourth tab's prompt explicitly states that limitation.

The voice timing uses the browser AudioContext playback clock and Google’s [voice activity detection](https://ai.google.dev/gemini-api/docs/live-api/capabilities#voice-activity-detection-vad). Microphone-based endpointing is an estimate and can be affected by noise. The saved five-question benchmark measures completed text responses; its numbers are not first-speech latency.

The live implementation follows Google's [WebSocket guide](https://ai.google.dev/gemini-api/docs/live-api/get-started-websocket) and [ephemeral token guide](https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens).

## Check the setup

From this folder:

```sh
source .venv/bin/activate
python check_setup.py
python check_setup.py --gemini
```

The Gemini check lists available models without requesting content generation. Text generation was verified on all four tabs. Gemini 3.8 Live was verified through an actual database tool call and native audio output; browser microphone connection/shutdown was checked with a simulated microphone. Physical microphone/audio quality still needs a human check.

The saved [five-question comparison](benchmarks/response-comparison.md) and [HTML report](benchmarks/response-comparison.html) include all four tabs. These measure completed text responses, not time to first speech. Raw results and the scripts to repeat the comparison are in `benchmarks/`.

## Query the data

```python
import duckdb

with duckdb.connect("data/ecommerce.duckdb", read_only=True) as db:
    print(db.sql("""
        SELECT order_date, SUM(net_amount) AS revenue
        FROM orders
        WHERE status = 'completed'
        GROUP BY order_date
        ORDER BY order_date DESC
        LIMIT 7
    """).fetchall())
```

Sales means completed-order net revenue, excluding tax and shipping. Read the rules in `data/schema.json` before writing analytical queries; joining orders to order items can multiply order revenue. Anchor relative dates to the dataset end date, 29 September 2026.

## Recreate the environment or dataset

```sh
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

A snapshot of the original generator and its dependency lockfile is in `dataset-generator/`. To create another database in a fresh directory:

```sh
(cd dataset-generator && npm ci)
DATA_DIR=./data-regenerated DEMO_SCALE=1 node dataset-generator/build-demo.mjs
```

The generator replaces its tables, so use a fresh output directory to preserve working data. Set `DUCKDB_PATH=./data-regenerated/ecommerce.duckdb` in `.env` to use that copy. The local comparison application is implemented in `server.py` and `web/`. No application is deployed to a remote service.
