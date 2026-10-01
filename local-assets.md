# Local bootstrap pack

Read in this order when building from scratch:

Start with [prompts/README.md](prompts/README.md) to distinguish the app-building prompt, the exact prompts sent to Gemini, and the supporting knowledge files.

1. principles.md — original Meridian analytical and conversational behavior.
2. domain-intelligence.md — commerce priorities, metric definitions, joins, limitations, and cloud schema rules.
3. build-spec.md — proposed user flow, runtime components, query contracts, voice handling, and completion criteria.
4. design-guide.md and references/meridian-design-guide.html — interaction guidance and the original visual reference.
5. data/schema.json — actual tables, columns, row counts, relationships, and rules.
6. examples/questions.json — representative questions, SQL, expected database-derived results, and missing-data cases.
7. README.md — environment activation, setup checks, example queries, and regeneration instructions.

## Files needed locally

- data/ecommerce.duckdb: Meridian database, September 2025–September 2026. Generate it locally using the included source, or supply an existing compatible copy; database binaries are excluded from Git.
- data/schema.json: table structure, row counts, metric definitions, and synthetic-data rules.
- .env: your Gemini key and DuckDB path. Keep the key server-side.
- .env.example: required variable names without credentials.
- requirements.txt and your local .venv/: Python tooling and SDK versions.
- check_setup.py: local database check and optional Gemini model-listing check.
- dataset-generator/: original generation source, Node package manifest, and lockfile.
- .gitignore: excludes credentials, database binaries, runtime dependencies, and temporary downloads.

Only the Gemini credential is needed for model access in this local demo; DuckDB needs a file path, no database account/password. Google Cloud authentication is not required to generate or query the database. Microphone access is granted by the browser when starting the voice session. Local cloud provenance records, when present, are optional and excluded from Git.

## Remaining implementation

The four-tab local demonstration is runnable using `.venv/bin/python server.py`. See README.md for its text and Gemini 3.8 Live paths. The implementation uses model-generated SQL with safety validation; independent analyst review, proactive scheduling, external connectors, and durable workspace memory remain future product work. The original build specification is preserved as broader product direction.

Existing production artifacts had stale 2025 date anchors in some documentation. This pack uses the downloaded cloud schema's actual end date, 2026-09-29.
