# Prompt and knowledge file guide

The project keeps three different kinds of instructions in separate files: a prompt for the coding agent to build the app, four system prompts for Gemini to answer questions, and supporting knowledge documents.

## 1. Prompt to create the app

[app-build.md](app-build.md) is the consolidated rebuild prompt. Give it to a coding agent together with this repository's files to recreate the local demonstration. It describes the four tabs, UI, database tools, voice path, widgets, timing, and verification.

The small document/code icon in the app opens this file. It is not sent to Gemini when answering a question.

## 2. Prompts sent to Gemini

Each tab has its own complete system prompt. The selected file is used for both typed requests and Live voice sessions, and its exact contents appear in the right-hand panel.

| Tab | Exact runtime prompt | Added knowledge |
| --- | --- | --- |
| 1 — Runtime discovery | [01-runtime-discovery.md](01-runtime-discovery.md) | Minimal operating instructions; discover the database at runtime. |
| 2 — Schema only | [02-schema-only.md](02-schema-only.md) | Raw table names, columns, and SQL types. |
| 3 — Guided queries | [03-guided-queries.md](03-guided-queries.md) | Field meanings, grains, relationships, metric definitions, and SQL recipes. |
| 4 — Domain + workflows | [04-domain-workflows.md](04-domain-workflows.md) | Principles, commerce intelligence, and investigation workflows. |

All four use the same database tools and require brief answers backed by actual query results. Gemini also receives tool declarations and the current question; conversation context is isolated by tab.

The short cumulative summaries in the UI explain each level to the audience. They are display metadata in `server.py`, not additional model instructions.

## 3. Supporting principles and knowledge

These files explain the context used to design and maintain the runtime prompts:

| File | Purpose | Relevant tabs |
| --- | --- | --- |
| [db-structure.md](db-structure.md) | Raw database table and column structure. | 2, 3, 4 |
| [field-guide.md](field-guide.md) | Field definitions, units, grains, joins, metric definitions, and key query recipes. | 3, 4 |
| [principles.md](../principles.md) | Analytical and conversational principles: answer first, preserve scope, ground results, and separate contribution from cause. | 4 |
| [domain-intelligence.md](../domain-intelligence.md) | Commerce priorities, metric interpretation, time anchors, missing data, and synthetic-context limits. | 4 |
| [workflows.md](../workflows.md) | Investigation steps for sales, traffic, conversion, and follow-up questions. | 4 |
| [schema.json](../data/schema.json) | Dataset metadata, exact column types, row counts, category catalog, and query rules. | Source reference for schema and guides |

The runtime files are self-contained snapshots. `server.py` reads the selected runtime file directly; it does not dynamically append these supporting documents. When changing a knowledge document, update its corresponding content in the relevant runtime prompts too. Tabs 1 and 2 must retain their limited context for a fair demonstration.

Additional rebuild references:

- [build-spec.md](../build-spec.md): implementation contracts and broader product direction; distinguishes implemented features from future work.
- [design-guide.md](../design-guide.md) and [Meridian visual reference](../references/meridian-design-guide.html): visual and interaction guidance.
- [questions.json](../examples/questions.json): example questions, reference SQL, expected results, and missing-data cases; these are not injected as answers into Gemini.
- [local-assets.md](../local-assets.md): the local file checklist.
- [Project README](../README.md): installation, data generation, launch, and benchmark instructions.
