# Maven Real-Time Analytics

This project demonstrates how the context given to an AI analyst affects its ability to answer business questions. It is a local training and demo app with four tabs: database access, database structure, query instructions, and domain intelligence.

Each tab uses the same Meridian e-commerce database and the same configured models. Ask the same question across all four to compare the answer, the SQL, and the response time. The knowledge supplied to the model grows at each step.

## 1. Runtime discovery — give it access to the data

The model starts with a short operating prompt and tools to read the database. It discovers the tables and columns at runtime, formulates SQL, and returns an answer.

This level demonstrates what an analyst can infer from the database itself, how much discovery it needs, and where business meaning remains ambiguous.

**Context:** database tools and basic instructions to query safely, answer briefly, and show a result.

[Exact Gemini prompt](prompts/01-runtime-discovery.md)

## 2. Schema only — add the database structure

Everything in Tab 1, plus table names, column names, and SQL types supplied in advance.

The model has a map of the database before answering. The schema tells it what fields exist, while definitions such as what counts as sales, how tables should be joined, and which metric formula to use are left for it to infer.

**Added context:** the raw database structure.

[Exact Gemini prompt](prompts/02-schema-only.md) · [Database structure](prompts/db-structure.md)

## 3. Guided queries — add the instructions to use it correctly

Everything in Tab 2, plus field meanings, units, table grains, relationships, metric definitions, and key SQL recipes.

For example, the guide defines sales as completed-order net revenue and explains how joining orders to line items can multiply an order total. It distinguishes orders, line-item rows, and units sold. This level demonstrates how explicit guidance can help a model interpret a question and build the right query.

**Added context:** what each field means, what links to what, and how to calculate the key metrics.

[Exact Gemini prompt](prompts/03-guided-queries.md) · [Field and query guide](prompts/field-guide.md)

## 4. Domain + workflows — add the business understanding

Everything in Tab 3, plus analytical principles, commerce intelligence, and investigation workflows.

This level supplies guidance for follow-ups such as “What contributed to the sales decline?” It helps the analyst choose a relevant investigation, preserve the question's scope, distinguish a measured contribution from a causal hypothesis, and recognize missing data.

**Added context:** how to interpret the result, investigate a business question, and communicate the evidence.

[Exact Gemini prompt](prompts/04-domain-workflows.md) · [Principles](principles.md) · [Domain intelligence](domain-intelligence.md) · [Workflows](workflows.md)

## Use it as a training demo

1. Ask a question in Tab 1, such as “What were my sales on 29 September 2026?”
2. Ask the same question in Tabs 2, 3, and 4.
3. Compare the result, query evidence, and timing. Look for differences in definitions, filters, joins, and discovery steps.
4. Try a trend, a category comparison, or a follow-up investigation to explore what the extra context enables.

All four tabs query the actual database. They keep separate conversation context, and reloading the page starts a fresh demo session. For independent comparisons, reload between questions. Switching tabs stops the microphone and closes the current voice connection; reconnecting starts a fresh voice context. Typed and voice histories are separate.

The main body shows the current question and one primary result: a number card, line graph, bar chart, or table. Expand the SQL evidence to inspect how the answer was calculated. The right panel summarizes the added context, then shows the full Gemini system prompt.

The talk path uses **Google Gemini 3.8 Live (`gemini-3.8-live`)** in every tab and gives brief spoken answers. The top timer measures **time to first speech**: from the end of your question until the first non-silent assistant audio is scheduled for playback. It freezes when speech begins. The app uses server voice-activity offsets when available and a microphone-based estimate otherwise. The typed fallback uses **Gemini 3.8 Flash (`gemini-3.8-flash`)** and displays completed text response time.

The demonstration is designed to let you observe the effect of context. More context does not guarantee a correct answer or a faster response. SQL safety is enforced by the app; independent review of business correctness is not automatically implemented.

## Prompts and knowledge files

- [App-building prompt](prompts/app-build.md): the consolidated instructions for a coding agent to recreate this app. The small document/code icon in the toolbar opens it.
- [Gemini runtime prompts](prompts/README.md#2-prompts-sent-to-gemini): the four separate system prompts used to answer questions.
- [Supporting knowledge](prompts/README.md#3-supporting-principles-and-knowledge): principles, domain intelligence, workflows, schema, and field/query guides.

See the [complete prompt and knowledge file guide](prompts/README.md) for every file and its role. Runtime prompts are self-contained snapshots; changes to supporting documents need to be reflected in the relevant runtime prompt files.

## Run locally

You need Python 3.12, Node.js with npm, and your own Gemini API key with access to the configured Live and Flash models. The app runs locally and calls Gemini remotely.

```sh
git clone https://github.com/aditya-vithaldas/maven-real-time-analytics.git
cd maven-real-time-analytics
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Add your key to `GEMINI_API_KEY` in `.env`. Keep `DUCKDB_PATH=./data/ecommerce.duckdb` for the default dataset. Then generate the data and start the app:

```sh
(cd dataset-generator && npm ci)
DATA_DIR=./data DEMO_SCALE=1 node dataset-generator/build-demo.mjs
.venv/bin/python check_setup.py
.venv/bin/python server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) and allow microphone access to use **Start talking**. On macOS, `start.command` launches the app after setup. You can check Gemini access without generating a response using `.venv/bin/python check_setup.py --gemini`.

The repository includes the source, prompts, knowledge documents, schema, generator, and benchmark reports. Credentials, database binaries, and installed dependencies are excluded from Git. The permanent API key stays on the local server; the browser receives an expiring voice-session token.

## The Meridian dataset

The synthetic dataset has **10 million rows across 12 tables**, covering **30 September 2025 through 29 September 2026**. It includes orders, items, customers, products, sessions, payments, shipments, calendar, regions, categories, modeled business events, and competitor snapshots. All monetary amounts are USD, and all records and market observations are synthetic.

Read [data/schema.json](data/schema.json) for the dataset structure and rules, and [examples/questions.json](examples/questions.json) for example questions and reference SQL. Relative dates are anchored to the dataset's latest date. No Google Cloud credentials are needed to generate or query the local database. See [local-assets.md](local-assets.md) for the local file checklist.

The generator replaces its tables. To preserve an existing database, generate another copy in a fresh directory:

```sh
DATA_DIR=./data-regenerated DEMO_SCALE=1 node dataset-generator/build-demo.mjs
```

Set `DUCKDB_PATH=./data-regenerated/ecommerce.duckdb` in `.env` to use that copy.

## Saved comparison

The [five-question comparison](benchmarks/response-comparison.md) and [HTML report](benchmarks/response-comparison.html) contain the saved answers, queries, failures, and reference checks across all four tabs. These are completed text response measurements; they do not measure time to first speech. Raw results and repeatable comparison scripts are in `benchmarks/`.
