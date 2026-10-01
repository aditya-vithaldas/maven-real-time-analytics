"""Local four-context training lab. Run: .venv/bin/python server.py"""
import argparse
import datetime as dt
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import threading
import time
import uuid
from urllib.parse import urlparse

import duckdb
from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests
import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
DB = Path(os.getenv('DUCKDB_PATH', 'data/ecommerce.duckdb'))
if not DB.is_absolute():
    DB = ROOT / DB
LIVE_MODEL = 'gemini-3.8-live'
TEXT_MODELS = ['gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-2.5-flash']
MODES = [
    {'id': 1, 'name': 'Runtime discovery', 'file': '01-runtime-discovery.md', 'description': 'Discover the database as you go.', 'knowledge': ['Runtime database tools'], 'summary': [
        {'label': 'A', 'heading': 'Read the database', 'detail': 'Discover its structure, query it and answer briefly.'},
    ]},
    {'id': 2, 'name': 'Schema only', 'file': '02-schema-only.md', 'description': 'Names and types. No business guidance.', 'knowledge': ['Table and column structure'], 'summaryBase': 'Everything in Tab 1, plus:', 'summary': [
        {'label': 'B', 'heading': 'Database structure', 'detail': 'Table names, columns and SQL types.'},
    ]},
    {'id': 3, 'name': 'Guided queries', 'file': '03-guided-queries.md', 'description': 'Field meanings, joins, and query recipes.', 'knowledge': ['Table and column structure', 'Field meanings and relationships', 'Key query recipes'], 'summaryBase': 'Everything in Tab 2, plus:', 'summary': [
        {'label': 'C', 'heading': 'Field meanings', 'detail': 'Definitions, units and table grains.'},
        {'label': 'D', 'heading': 'Joins + key queries', 'detail': 'Relationships and metric recipes.'},
    ]},
    {'id': 4, 'name': 'Domain + workflows', 'file': '04-domain-workflows.md', 'description': 'Commerce intelligence and investigation workflows.', 'knowledge': ['Table and column structure', 'Field meanings and relationships', 'Key query recipes', 'Principles and domain intelligence', 'Investigation workflows'], 'summaryBase': 'Everything in Tab 3, plus:', 'summary': [
        {'label': 'E', 'heading': 'Principles + domain intelligence', 'detail': 'Commerce rules and business context.'},
        {'label': 'F', 'heading': 'Investigation workflows', 'detail': 'Driver analysis and follow-ups.'},
    ]},
]
HISTORIES = {}
HISTORY_LOCK = threading.Lock()
MODEL_SLOTS = threading.BoundedSemaphore(4)
RESULTS = {}
RESULT_LOCK = threading.Lock()


def connect():
    return duckdb.connect(str(DB), read_only=True, config={
        'enable_external_access': 'false', 'autoinstall_known_extensions': 'false',
        'autoload_known_extensions': 'false', 'allow_community_extensions': 'false',
        'threads': '2', 'memory_limit': '512MB',
    })


with connect() as _db:
    TABLES = {row[0] for row in _db.execute('SHOW TABLES').fetchall()}

ALLOWED_FUNCS = set('AND OR NOT ABS AVG COUNT SUM MIN MAX ROUND COALESCE NULLIF CAST TRY_CAST IF CASE '
    'DATE DATE_ADD DATE_SUB DATE_DIFF DATE_TRUNC DATEDIFF TIMESTAMPDIFF STRFTIME EXTRACT '
    'YEAR MONTH DAY DAYOFWEEK QUARTER LOWER UPPER CONCAT SUBSTRING LENGTH TRIM '
    'ROW_NUMBER RANK DENSE_RANK LAG LEAD FIRST_VALUE LAST_VALUE '
    'STDDEV STDDEV_SAMP STDDEV_POP VARIANCE MEDIAN QUANTILE_CONT '
    'GREATEST LEAST FLOOR CEIL CEILING POWER SQRT PERCENTILE_CONT '
    'TIME_TO_STR TS_OR_DS_TO_DATE TS_OR_DS_ADD TS_OR_DS_DIFF TIMESTAMP_TRUNC TIMESTAMP_ADD TIMESTAMP_SUB'.split())


def safe_sql(sql):
    if not isinstance(sql, str) or len(sql) > 20000:
        raise ValueError('Provide one SQL query, at most 20,000 characters.')
    trees = sqlglot.parse(sql, read='duckdb')
    if len(trees) != 1 or not isinstance(trees[0], (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise ValueError('Only one read-only SELECT or CTE query is allowed.')
    tree = trees[0]
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Command, exp.Into)
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise ValueError('Database changes and command statements are not allowed.')
    ctes = {node.alias_or_name.lower() for node in tree.find_all(exp.CTE)}
    if not any(table.name.lower() in TABLES for table in tree.find_all(exp.Table)):
        raise ValueError("Query at least one actual dataset table.")
    for table in tree.find_all(exp.Table):
        if table.db or table.catalog or not isinstance(table.this, exp.Identifier):
            raise ValueError('External sources and system tables are not allowed.')
        if table.name.lower() not in TABLES | ctes:
            raise ValueError('Query only the available dataset tables.')
    for func in tree.find_all(exp.Func):
        name = func.name.upper() if isinstance(func, exp.Anonymous) else func.sql_name().upper()
        if name not in ALLOWED_FUNCS:
            raise ValueError(f'Function {name} is not enabled in this read-only demo.')
    return sql


def scalar(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def execute_tool(name, args):
    started = time.monotonic()
    if name == 'list_tables':
        with connect() as db:
            result = {'tables': [r[0] for r in db.execute('SHOW TABLES').fetchall()]}
    elif name == 'describe_table':
        table = args.get('table', '')
        if table not in TABLES:
            raise ValueError('Unknown dataset table.')
        with connect() as db:
            result = {'table': table, 'columns': [{'name': r[0], 'type': r[1]} for r in db.execute(f'DESCRIBE "{table}"').fetchall()]}
    elif name == 'run_query':
        sql = safe_sql(args.get('sql'))
        with connect() as db:
            timer = threading.Timer(12, db.interrupt)
            timer.start()
            try:
                cursor = db.execute(sql)
                columns = [d[0] for d in cursor.description]
                values = cursor.fetchmany(201)
                result = {'sql': sql, 'columns': columns, 'rows': [[scalar(v) for v in row] for row in values[:200]], 'truncated': len(values) > 200}
            finally:
                timer.cancel()
                timer.join()
        result['resultId'] = uuid.uuid4().hex
        with RESULT_LOCK:
            if len(RESULTS) >= 500:
                RESULTS.pop(next(iter(RESULTS)))
            RESULTS[result['resultId']] = result
    elif name == 'show_widget':
        with RESULT_LOCK:
            query = RESULTS.get(args.get('result_id'))
        if not query:
            raise ValueError('Choose the resultId returned by a successful run_query.')
        kind = args.get('type')
        if kind not in ('number', 'line', 'bar', 'table'):
            raise ValueError('Widget type must be number, line, bar, or table.')
        value = args.get('value_column')
        label = args.get('label_column')
        if kind != 'table':
            if value not in query['columns']:
                raise ValueError('Choose an actual numeric result column.')
            index = query['columns'].index(value)
            if not any(isinstance(row[index], (int, float)) for row in query['rows']):
                raise ValueError('The value column has no numeric data.')
            if kind == 'number' and len(query['rows']) != 1:
                raise ValueError('A total-number widget requires exactly one result row.')
            if kind in ('line', 'bar') and label not in query['columns']:
                raise ValueError('Choose an actual label/date column.')
        result = {'widget': {'type': kind, 'title': str(args.get('title', 'Result'))[:150],
            'unit': str(args.get('unit', ''))[:40], 'resultId': query['resultId'],
            'valueColumn': value, 'labelColumn': label}, 'query': query}
    else:
        raise ValueError('Unknown database tool.')
    result['elapsedMs'] = round((time.monotonic() - started) * 1000)
    return result


DECLARATIONS = [
    {'name': 'list_tables', 'description': 'Discover available table names directly from the database at runtime.', 'parameters': {'type': 'OBJECT', 'properties': {}}},
    {'name': 'describe_table', 'description': 'Read raw column names and SQL types for one table at runtime. Does not provide field meanings.', 'parameters': {'type': 'OBJECT', 'properties': {'table': {'type': 'STRING'}}, 'required': ['table']}},
    {'name': 'run_query', 'description': 'Execute one read-only DuckDB SELECT/CTE query against dataset tables. Returns up to 200 rows and an explicit truncation flag. Use aggregates for large tables.', 'parameters': {'type': 'OBJECT', 'properties': {'sql': {'type': 'STRING'}}, 'required': ['sql']}},
    {'name': 'show_widget', 'description': 'Choose the ONE primary widget for the current question using a successful run_query resultId. Call after analysis/control queries. Never invent values. Number for a scalar total, line for time series, bar for category comparison, table for detail.', 'parameters': {'type': 'OBJECT', 'properties': {
        'result_id': {'type': 'STRING'}, 'type': {'type': 'STRING', 'enum': ['number', 'line', 'bar', 'table']},
        'title': {'type': 'STRING'}, 'unit': {'type': 'STRING'}, 'value_column': {'type': 'STRING'}, 'label_column': {'type': 'STRING'}},
        'required': ['result_id', 'type', 'title']}},
]


def mode_for(value):
    mode = next((m for m in MODES if m['id'] == value), None)
    if not mode:
        raise ValueError('Choose one of the four tabs.')
    return mode


def prompt_for(mode):
    return (ROOT / 'prompts' / mode['file']).read_text()


def ask(data):
    mode = mode_for(data.get('mode'))
    question = data.get('question', '')
    session = data.get('session', '')
    model = data.get('model', TEXT_MODELS[0])
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise ValueError('Enter a question, at most 4,000 characters.')
    if not isinstance(session, str) or not 1 <= len(session) <= 100 or model not in TEXT_MODELS:
        raise ValueError('Invalid session or model.')
    key = (session, mode['id'], model)
    with HISTORY_LOCK:
        history = list(HISTORIES.get(key, []))
    contents = [types.Content(role='user', parts=[types.Part.from_text(text='Previous exchanges in this tab only:\n' + json.dumps(history) + '\n\nCurrent question: ' + question)])]
    trace, usage = [], {'inputTokens': 0, 'outputTokens': 0}
    start = time.monotonic()
    with genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(timeout=45000)) as client:
        for _ in range(24):
            response = client.models.generate_content(model=model, contents=contents, config=types.GenerateContentConfig(
                system_instruction=prompt_for(mode), temperature=0.2, max_output_tokens=3000,
                tools=[types.Tool(function_declarations=DECLARATIONS)],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
            if response.usage_metadata:
                usage['inputTokens'] += response.usage_metadata.prompt_token_count or 0
                usage['outputTokens'] += response.usage_metadata.candidates_token_count or 0
            if not response.candidates or not response.candidates[0].content:
                raise RuntimeError('The model returned no response. Try again.')
            content = response.candidates[0].content
            contents.append(content)
            calls = [p.function_call for p in content.parts or [] if p.function_call]
            if not calls:
                answer = '\n'.join(p.text for p in content.parts or [] if p.text and not p.thought)
                if not answer:
                    raise RuntimeError('The model returned no answer. Try again.')
                queries = [t['result'] for t in trace if t['name'] == 'run_query' and 'error' not in t['result']]
                with HISTORY_LOCK:
                    if len(HISTORIES) > 200:
                        HISTORIES.clear()
                    HISTORIES[key] = (history + [{'question': question, 'answer': answer, 'queries': queries}])[-5:]
                return {'answer': answer, 'trace': trace, 'queries': queries, 'elapsedMs': round((time.monotonic()-start)*1000), 'usage': usage, 'model': model, 'mode': mode['id']}
            parts = []
            for call in calls:
                try:
                    result = execute_tool(call.name, dict(call.args or {}))
                except Exception as exc:
                    result = {'error': str(exc)[:500]}
                trace.append({'name': call.name, 'args': dict(call.args or {}), 'result': result})
                parts.append(types.Part.from_function_response(name=call.name, response=result))
            contents.append(types.Content(role='user', parts=parts))
            if time.monotonic()-start > 150:
                raise RuntimeError('This question reached the time limit. Try a narrower question.')
    raise RuntimeError('This question reached the tool limit. Try a narrower question.')


class Handler(BaseHTTPRequestHandler):
    def valid_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def reply(self, value, status=200):
        body = json.dumps(value, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.valid_host():
            return self.reply({'error': 'Use localhost to access this application.'}, 403)
        path = urlparse(self.path).path
        if path == '/api/app-prompt':
            return self.reply({'prompt': (ROOT / 'prompts' / 'app-build.md').read_text()})
        if path == '/api/config':
            return self.reply({'modes': [{**m, 'prompt': prompt_for(m)} for m in MODES], 'liveModel': LIVE_MODEL, 'textModels': TEXT_MODELS, 'dataset': {'name': 'Meridian commerce', 'rows': 10000000, 'start': '2025-09-30', 'end': '2026-09-29'}})
        files = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/live.js': 'live.js', '/capture.js': 'capture.js'}
        if path not in files:
            return self.reply({'error': 'Not found'}, 404)
        file = ROOT / 'web' / files[path]
        body = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html' if file.suffix == '.html' else 'text/css' if file.suffix == '.css' else 'text/javascript')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self.valid_host():
            return self.reply({'error': 'Use localhost to access this application.'}, 403)
        origin = self.headers.get('Origin')
        if origin and origin != f'http://{self.headers.get("Host")}':
            return self.reply({'error': 'Use the local application origin.'}, 403)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 30000:
                raise ValueError('Invalid request size.')
            data = json.loads(self.rfile.read(length))
            path = urlparse(self.path).path
            if path == '/api/query':
                if not MODEL_SLOTS.acquire(blocking=False):
                    return self.reply({'error': 'Four questions are already running. Wait for one to finish.'}, 429)
                try:
                    return self.reply(ask(data))
                finally:
                    MODEL_SLOTS.release()
            if path == '/api/tool':
                mode_for(data.get('mode'))
                return self.reply(execute_tool(data.get('name'), data.get('args', {})))
            if path == '/api/live':
                mode = mode_for(data.get('mode'))
                now = dt.datetime.now(dt.timezone.utc)
                r = requests.post('https://generativelanguage.googleapis.com/v1beta/auth_tokens',
                    headers={'x-goog-api-key': os.environ['GEMINI_API_KEY']}, json={
                        'uses': 1, 'expireTime': (now+dt.timedelta(minutes=30)).isoformat(),
                        'newSessionExpireTime': (now+dt.timedelta(minutes=2)).isoformat()}, timeout=20)
                if not r.ok:
                    return self.reply({'error': 'Gemini could not issue a live session token. Check account access/quota.'}, 502)
                return self.reply({'token': r.json()['name'], 'model': LIVE_MODEL, 'prompt': prompt_for(mode), 'tools': DECLARATIONS})
            if path == '/api/reset':
                mode = mode_for(data.get('mode'))
                with HISTORY_LOCK:
                    for key in list(HISTORIES):
                        if key[:2] == (data.get('session'), mode['id']):
                            del HISTORIES[key]
                return self.reply({'ok': True})
            self.reply({'error': 'Not found'}, 404)
        except (ValueError, KeyError) as exc:
            self.reply({'error': str(exc)[:500]}, 400)
        except Exception as exc:
            # Do not echo upstream request headers or credentials to the browser.
            print('Request failed:', type(exc).__name__, flush=True)
            self.reply({'error': 'The request failed. Check model access/quota or try a narrower question.'}, 502)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Meridian training lab: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
