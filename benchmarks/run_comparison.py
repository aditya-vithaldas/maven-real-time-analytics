"""Measure five independent questions through every local tab, without concurrent requests."""
import datetime as dt
import json
import math
from pathlib import Path
import time
import urllib.error
import urllib.request
import uuid

import duckdb

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8765'
MODEL = 'gemini-3.8-flash'
QUESTIONS = [
    ('daily-sales', 'What were my sales on 29 September 2026?', 'daily-sales'),
    ('daily-trend', 'Show daily sales for the last seven available days.', 'daily-trend'),
    ('top-categories', 'Which five categories had the highest sales on 29 September 2026?', 'category-sales'),
    ('units', 'How many units sold on 29 September 2026?', 'units'),
    ('conversion', 'What was session conversion on 29 September 2026?', 'conversion'),
]


def get_json(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as response:
        return json.load(response)


def selected_result(response):
    for trace in reversed(response.get('trace', [])):
        if trace['name'] == 'show_widget' and trace.get('result', {}).get('widget'):
            return trace['result']['query'], trace['result']['widget']
    queries = response.get('queries', [])
    return (queries[-1], {}) if queries else (None, {})


def check_answer(response, expected):
    query, widget = selected_result(response)
    if not query or not query.get('rows'):
        return {'matchesReference': False, 'note': 'No successful primary data result.', 'widgetSelected': bool(widget)}
    columns, rows = query['columns'], query['rows']
    vi = columns.index(widget['valueColumn']) if widget.get('valueColumn') in columns else next((i for i in range(len(columns)) if any(isinstance(r[i], (int, float)) for r in rows)), None)
    li = columns.index(widget['labelColumn']) if widget.get('labelColumn') in columns else next((i for i in range(len(columns)) if i != vi and any(isinstance(r[i], str) for r in rows)), None)
    if vi is None:
        return {'matchesReference': False, 'note': 'No numeric result column.', 'widgetSelected': bool(widget)}
    if len(expected) == 1:
        values = [r[vi] for r in rows]
        good = len(values) == 1 and isinstance(values[0], (int, float)) and math.isclose(values[0], expected[0][1], abs_tol=.011, rel_tol=0)
    else:
        values = {str(r[li]): r[vi] for r in rows} if li is not None else {}
        good = all(label in values and isinstance(values[label], (int, float)) and math.isclose(values[label], value, abs_tol=.011, rel_tol=0) for label, value in expected)
    return {'matchesReference': good, 'note': 'Selected result agrees with the reference SQL.' if good else 'Selected result differs from the reference SQL; inspect its assumptions and filters.', 'widgetSelected': bool(widget), 'selectedWidget': widget, 'selectedQuery': query}


def main():
    config = get_json('/api/config')
    examples = {e['id']: e for e in json.loads((ROOT / 'examples/questions.json').read_text())['examples']}
    questions = []
    with duckdb.connect(str(ROOT / 'data/ecommerce.duckdb'), read_only=True) as db:
        for ident, question, reference in QUESTIONS:
            sql = examples[reference]['sql']
            if ident == 'top-categories':
                sql += ' LIMIT 5'
            expected = [[str(row[0]), float(row[1])] for row in db.execute(sql).fetchall()]
            questions.append({'id': ident, 'question': question, 'referenceSql': sql, 'referenceRows': expected})
    report = {'startedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'model': MODEL, 'method': 'Sequential HTTP requests; fresh conversation for every question and tab; elapsed wall time includes model and database tools. One attempt per question per tab. No retries.', 'config': config, 'questions': questions, 'runs': []}
    output = ROOT / 'benchmarks/response-comparison.json'
    run_id = uuid.uuid4().hex
    for qi, question in enumerate(questions):
        order = list(range(1, 5))
        order = order[qi % 4:] + order[:qi % 4]
        for mode in order:
            mode_name = next(m['name'] for m in config['modes'] if m['id'] == mode)
            print(f'START {len(report["runs"])+1}/20 · Q{qi+1} · {mode_name}', flush=True)
            payload = {'mode': mode, 'question': question['question'], 'model': MODEL, 'session': f'benchmark-{run_id}-{qi}-{mode}'}
            request = urllib.request.Request(BASE + '/api/query', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            started = time.perf_counter()
            row = {'questionIndex': qi + 1, 'questionId': question['id'], 'mode': mode, 'tab': mode_name}
            try:
                with urllib.request.urlopen(request, timeout=200) as response:
                    result = json.load(response)
                row.update({'ok': True, 'responseSeconds': round(time.perf_counter() - started, 3), 'response': result, 'validation': check_answer(result, question['referenceRows'])})
            except urllib.error.HTTPError as exc:
                row.update({'ok': False, 'responseSeconds': round(time.perf_counter() - started, 3), 'error': json.loads(exc.read())})
            except Exception as exc:
                row.update({'ok': False, 'responseSeconds': round(time.perf_counter() - started, 3), 'error': str(exc)})
            report['runs'].append(row)
            output.write_text(json.dumps(report, indent=2))
            agreement = row.get('validation', {}).get('matchesReference')
            print(f'DONE · {row["responseSeconds"]:.2f}s · {"OK" if row["ok"] else "FAILED"} · reference={agreement}', flush=True)
    report['finishedAt'] = dt.datetime.now(dt.timezone.utc).isoformat()
    output.write_text(json.dumps(report, indent=2))
    print('COMPLETE', output, flush=True)


if __name__ == '__main__':
    main()
