"""Build a readable local report from the saved measurement results."""
import html
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'benchmarks/response-comparison.json'


def main():
    data = json.loads(REPORT.read_text())
    modes = data['config']['modes']
    by_pair = {(r['questionIndex'], r['mode']): r for r in data['runs']}
    summary = []
    for mode in modes:
        runs = [r for r in data['runs'] if r['mode'] == mode['id']]
        timings = [r['responseSeconds'] for r in runs if r['ok']]
        summary.append({'tab': mode['name'], 'id': mode['id'], 'completed': len(timings), 'attempts': len(runs), 'average': statistics.mean(timings) if timings else None, 'median': statistics.median(timings) if timings else None, 'min': min(timings) if timings else None, 'max': max(timings) if timings else None, 'referenceMatches': sum(r.get('validation', {}).get('matchesReference', False) for r in runs)})
    data['summary'] = summary
    REPORT.write_text(json.dumps(data, indent=2))
    md = ['# Meridian completed-text response comparison', '', f'Model: **{data["model"]}**, text path. Five questions × four tabs = 20 requests.', '', data['method'], '', '## Response time in seconds', '', '| Question | Runtime discovery | Schema only | Guided queries | Domain + workflows |', '| --- | ---: | ---: | ---: | ---: |']
    table_rows = []
    for qi, question in enumerate(data['questions'], 1):
        cells = []
        for mode in modes:
            run = by_pair.get((qi, mode['id']))
            cells.append(f'{run["responseSeconds"]:.2f}' + (' (failed)' if not run['ok'] else '') if run else 'Pending')
        md.append('| ' + question['question'] + ' | ' + ' | '.join(cells) + ' |')
        table_rows.append('<tr><th>' + html.escape(question['question']) + '</th>' + ''.join('<td>'+c+'</td>' for c in cells) + '</tr>')
    md += ['', '| Tab | Average | Median | Range | Completed | Reference matches |', '| --- | ---: | ---: | --- | ---: | ---: |']
    summary_rows = []
    for s in summary:
        average = f'{s["average"]:.2f}s' if s['average'] is not None else '—'
        median = f'{s["median"]:.2f}s' if s['median'] is not None else '—'
        interval = f'{s["min"]:.2f}–{s["max"]:.2f}s' if s['min'] is not None else '—'
        md.append(f'| {s["tab"]} | {average} | {median} | {interval} | {s["completed"]}/{s["attempts"]} | {s["referenceMatches"]}/{s["attempts"]} |')
        summary_rows.append(f'<tr><th>{html.escape(s["tab"])}</th><td>{average}</td><td>{median}</td><td>{interval}</td><td>{s["completed"]}/{s["attempts"]}</td><td>{s["referenceMatches"]}/{s["attempts"]}</td></tr>')
    note = 'This is one small sample, not a latency guarantee. Successful-request averages exclude failures, which remain visible in the question table. Reference matching compares the selected numeric query result with reference SQL executed directly on the database; it does not independently judge every sentence. Timings include the full response and database tools, not just the first token or voice audio.'
    md += ['', note, '', '## All responses', '']
    response_sections = []
    for qi, question in enumerate(data['questions'], 1):
        md += [f'### Q{qi}: {question["question"]}', '', 'Reference result:', '', '```json', json.dumps(question['referenceRows'], indent=2), '```', '']
        answers = []
        for mode in modes:
            run = by_pair.get((qi, mode['id']))
            if not run:
                continue
            answer = run.get('response', {}).get('answer') or json.dumps(run.get('error'))
            validation = run.get('validation', {})
            status = 'Matches reference' if validation.get('matchesReference') else 'Inspect result / assumptions' if run['ok'] else 'Request failed'
            md += [f'**{mode["name"]} — {run["responseSeconds"]:.2f}s — {status}**', '', answer, '']
            if validation.get('selectedQuery'):
                md += ['```sql', validation['selectedQuery']['sql'], '```', '']
            query = validation.get('selectedQuery', {})
            query_html = '<details><summary>SQL and returned data</summary><pre>'+html.escape(query.get('sql', 'No selected result'))+'</pre><pre>'+html.escape(json.dumps({'columns':query.get('columns'), 'rows':query.get('rows')}, indent=2))+'</pre></details>'
            answers.append(f'<article><div class="answer-title"><strong>{html.escape(mode["name"])}</strong><span>{run["responseSeconds"]:.2f}s</span></div><p>{html.escape(answer)}</p><small>{status}</small>{query_html}</article>')
        reference = html.escape(json.dumps(question['referenceRows'], indent=2))
        response_sections.append(f'<section class="question"><h2>Q{qi} · {html.escape(question["question"])}</h2><div class="answers">'+''.join(answers)+f'</div><details><summary>Reference SQL and expected values</summary><pre>{html.escape(question["referenceSql"])}</pre><pre>{reference}</pre></details></section>')
    (ROOT / 'benchmarks/response-comparison.md').write_text('\n'.join(md)+'\n')
    style = '''body{font:14px/1.6 system-ui,sans-serif;color:#25364e;background:#f4f6fa;margin:0;padding:28px}main{max-width:1300px;margin:auto}h1{font-size:28px;margin:0 0 8px}h2{font-size:18px}p{white-space:pre-wrap}table{width:100%;border-collapse:collapse;background:white;margin:20px 0;font-size:13px}th,td{text-align:left;padding:12px;border-bottom:1px solid #e1e7ef}td{text-align:right;font-variant-numeric:tabular-nums}thead{background:#edf2fc}.table-wrap{overflow:auto}.note,small{color:#62738b}.question{padding:20px;background:#fff;border:1px solid #e1e7ef;border-radius:10px;margin:20px 0}.answers{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{padding:16px;background:#f9fbff;border:1px solid #e1e7ef;border-radius:8px}.answer-title{display:flex;justify-content:space-between;gap:12px}.answer-title span{color:#2d57dc;font-weight:700}details{margin-top:12px}summary{cursor:pointer;font-size:12px;color:#46628b}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11px/1.6 ui-monospace,monospace;background:#f1f4f9;padding:12px;max-height:350px;overflow:auto}a{color:#2d57dc}@media(max-width:760px){body{padding:12px}.answers{grid-template-columns:1fr}th,td{padding:8px}}'''
    title_row = '<thead><tr><th>Question</th>'+''.join('<th>'+html.escape(m['name'])+'</th>' for m in modes)+'</tr></thead>'
    summary_head = '<thead><tr><th>Tab</th><th>Average</th><th>Median</th><th>Range</th><th>Completed</th><th>Reference matches</th></tr></thead>'
    output = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Meridian completed-text response comparison</title><style>'+style+'</style><main><h1>Completed text response time across four tabs</h1><p>Gemini 3.8 Flash · Text path · Five questions per tab · Fresh context per request</p><p class="note">'+html.escape(data['method'])+'</p><h2>Seconds per question</h2><div class="table-wrap"><table>'+title_row+'<tbody>'+''.join(table_rows)+'</tbody></table></div><h2>Summary</h2><div class="table-wrap"><table>'+summary_head+'<tbody>'+''.join(summary_rows)+'</tbody></table></div><p class="note">'+html.escape(note)+'</p>'+''.join(response_sections)+'</main></html>'
    (ROOT / 'benchmarks/response-comparison.html').write_text(output)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
