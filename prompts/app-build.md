Build Meridian Context Lab, a local voice-and-data training demo that shows how the same analyst performs with four levels of context. Use the supplied local assets and implement a working application, including real database queries and live speech.

## Local assets and implementation

- Use data/ecommerce.duckdb: the Meridian synthetic commerce dataset, with 10 million rows across 12 tables and trading dates from 30 September 2025 through 29 September 2026. Read the existing database; keep it intact.
- Use data/schema.json, prompts/db-structure.md, prompts/field-guide.md, principles.md, domain-intelligence.md, and workflows.md as the supplied knowledge sources. Use design-guide.md and references/meridian-design-guide.html for the visual language.
- Read GEMINI_API_KEY and DUCKDB_PATH from the local .env. Keep credentials on the server and exclude them from source control. Never display the key or expose .env through HTTP.
- Keep the app local at http://127.0.0.1:8765. Use a small Python server, read-only DuckDB, the Google Gen AI SDK, SQL parsing/validation, and ordinary browser HTML/CSS/JavaScript. Include requirements.txt, README.md, setup checks, and a local launcher. Do not deploy it.

## Four tabs and the prompts sent to Gemini

Name the tabs:
1. Runtime discovery: no preloaded schema or business guide. The model discovers tables and columns at runtime and formulates its query. Use a minimal runtime prompt.
2. Schema only: the same minimal operating instructions plus raw table names, column names, and SQL types. Supply no field meanings, relationship guidance, metric definitions, or SQL recipes.
3. Guided queries: supply the schema, field definitions, relationships, grains, metric definitions, and key SQL recipes so a less capable model can manage.
4. Domain + workflows: include the guided context plus the supplied principles, domain intelligence, and investigation workflows.

Keep the runtime prompts in prompts/01-runtime-discovery.md through prompts/04-domain-workflows.md. The right panel must first show a short cumulative summary. Tab 1 has A: database access at runtime. Tab 2 says Everything in Tab 1, plus B: database structure. Tab 3 says Everything in Tab 2, plus C: field meanings and D: joins/query recipes. Tab 4 says Everything in Tab 3, plus E: principles/domain intelligence and F: investigation workflows. Show only the additions using consistent headings and a short explanation; do not repeat the earlier context. Add a separator, then the complete exact prompt sent to Gemini, with a Copy button. The summary explains the knowledge level for the audience; it does not add hidden model instructions. Do not silently append richer knowledge to the first two tabs. The app-building prompt is a separate document for the coding agent; it is never part of Gemini's runtime context.

All four tabs query the same database. Keep each tab’s conversation isolated and retain context internally for follow-ups. Switching tabs stops microphone capture and the current Live connection. Reloading the page starts a fresh demo with new conversation context. Live reconnects start a new voice context; typed history remains separate.

## Voice and typed interactions

Use Google Gemini 3.8 Live (gemini-3.8-live) for the talk path in every tab. Use native audio over WebSocket with expiring session credentials issued by the local server; keep the permanent API key server-side. Capture microphone audio as 16 kHz PCM and play native audio at the rate reported by the API. Handle streaming input/output transcripts, database tool calls, interrupted playback, disconnects, and microphone cleanup.

Speak the answer first, in one or two short sentences. Do not narrate SQL, tool steps, or every chart point. Quantitative answers must come from the database. Show connection/listening/querying/speaking status and an obvious microphone start/stop button.

Provide a typed fallback using the fixed gemini-3.8-flash model in all four tabs. Do not display model selection. Use the same tab-specific runtime prompt and database tools for typed and voice requests.

## Database tools and primary widgets

Expose list_tables, describe_table, run_query, and show_widget. Discovery tools return raw names/types, without business definitions. run_query returns actual SQL results and a unique resultId. show_widget selects that result by its exact ID and validates column references; it never accepts invented widget values.

Enforce read-only access on the server. Parse SQL; allow only supported SELECT/CTE operations on actual dataset tables. Disable external access, file reads, extension loading, system catalogs, and mutations. Bound query time, memory, and returned rows. Report failed queries clearly. Do not claim independent business-correctness review unless it is actually performed.

For each question show exactly one primary result:
- Number card for a total, count, average, or percentage.
- Line graph for a chronological trend.
- Bar chart for a category or segment comparison.
- Table for detailed records or mixed data.

Use query-provided values, labels, units, and dates. Preserve signs, nulls, and precision; disclose omitted values or truncation. The current question and widget replace the previous visible result. Keep a short explanation and expandable database evidence secondary. There is no visible chat feed or chat video.

## Compact presentation and timing

Focus on the main body. Remove the branding masthead and introductory hero. Put four compact tabs across the top, followed by one compact toolbar. Give roughly three quarters of the desktop width to the primary result and a narrow right panel to the Gemini runtime prompt. Fill the window height, let results and long prompts scroll within their areas, and keep the composer visible. Adapt to smaller windows and mobile screens without horizontal overflow.

Show only one performance measure. For voice, label it Time to first speech: measure from the end of the user's question to the first non-silent assistant audio scheduled for playback, using the audio playback clock. Use server voice-activity audio offsets when available and a microphone-based estimate otherwise. Freeze the value when speech begins; transcripts, later audio chunks, and completion must not extend it. For the typed fallback, label the full-request measurement Text completion time. Do not present completed text timings as speech-onset timings.

Use a quiet gray canvas, white panels, blue actions, clear typography, and tight, readable spacing. Use one clean demo layout without presentation/standard view toggles or a Reset tab button. Keep the top toolbar limited to response timing, the fixed voice engine, and the app-building prompt icon. Keep focus indicators, keyboard tab navigation, clear labels, and responsive charts.

Add a small icon in the top toolbar that opens this app-building prompt in a modal with Copy and Close controls. It occupies no persistent content panel. Label the right-hand prompt as the Gemini runtime prompt so the two uses are clear.

## Verification

Verify actual database-backed numbers, time trends, category comparisons, follow-ups, tab isolation, prompt visibility/copying, and fresh context after a page reload. Test microphone connection/cleanup, native audio, interruption, and the first-speech timer. Verify that transcripts and silent audio do not stop the timer, later speech does not increase it, and new questions reset it. Check desktop/mobile layout and keyboard operation. Use database-derived reference results for checks; never inject canned answers into the app or runtime prompts. Report any unverified physical microphone/audio behavior honestly.
