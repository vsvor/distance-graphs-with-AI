#!/usr/bin/env python3
"""Run the compiled exhaustive G65 search and verify its positive control."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    graph = ROOT/'data'/'eil65_corrected.json'
    data = json.loads(graph.read_text())
    records = []
    for k in (8, 9):
        command = [str(ROOT/'build'/'color'), str(ROOT/'data'/'eil65_corrected.txt'), str(k), '60']
        result = subprocess.run(command, capture_output=True, text=True, timeout=70)
        (ROOT/'results').mkdir(exist_ok=True)
        (ROOT/'results'/f'g65_{k}color.log').write_text(result.stdout+result.stderr)
        expected = 20 if k == 8 else 10
        word = 'UNSAT' if k == 8 else 'SAT'
        if result.returncode != expected or not result.stdout.startswith(word+' '):
            raise ValueError(f'G65/{k}: expected a completed {word} result: '+result.stdout+result.stderr)
        if k == 9:
            colors = list(map(int, result.stdout.splitlines()[1].split()))
            if (len(colors) != 65 or any(c < 0 or c >= 9 for c in colors) or
                    any(colors[u] == colors[v] for u, v in data['edges'])):
                raise ValueError('The exhaustive solver returned an invalid positive control')
        records.append(dict(colors=k, result=word, exit_code=result.returncode,
                            output=result.stdout.strip(), log=f'g65_{k}color.log'))
    report = dict(status='PASS', graph_sha256=hashlib.sha256(graph.read_bytes()).hexdigest(),
                  solver_source_sha256=hashlib.sha256((ROOT/'scripts'/'color.cpp').read_bytes()).hexdigest(),
                  method='exhaustive DSATUR with first-use color renaming',
                  cases=records, DRAT_certificate=False, G328_search_run=False)
    (ROOT/'results'/'g65_search.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
