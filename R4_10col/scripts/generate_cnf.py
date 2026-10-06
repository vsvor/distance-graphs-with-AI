#!/usr/bin/env python3
"""Build nine assignment-only 9-coloring cases; Python 3.10+, stdlib only."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CLIQUE = [64, 39, 36, 34, 51]
ROOTS = [0, 28, 31, 33]
K = 9


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'cnf')
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    source = HERE / 'data' / 'candidate328.json'
    graph = json.loads(source.read_text())
    n = len(graph['vertices'])
    edges = sorted({tuple(sorted(e)) for e in graph['edges']})
    assert (n, len(edges)) == (328, 5066)
    assert all(tuple(sorted(e)) in edges for e in combinations(CLIQUE, 2))
    def x(v, c):
        return K*v+c
    base = []
    for v in range(n):
        base.append(tuple(x(v, c) for c in range(1, K+1)))
        base.extend((-x(v, c), -x(v, d))
                    for c, d in combinations(range(1, K+1), 2))
    base.extend((-x(u, c), -x(v, c)) for u, v in edges
                for c in range(1, K+1))
    assert len(base) == 57730
    common = list(zip(CLIQUE, range(1, 6)))

    def write(relative, assignments, label):
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        clauses = base + [(x(v, c),) for v, c in assignments]
        comments = [
            'G328: 328 vertices, 5066 edges, 9 colors; '+label,
            'Original zero-based vertex IDs 0..327; colors 1..9.',
            'Variable x(v,c)=9*v+c. No auxiliary variables.',
            'Only graph-coloring clauses and positive unit assignments.',
            'Fixed assignments: '+', '.join(f'{v}:{c}' for v, c in assignments),
            'All nine root cases must be excluded to rule out a 9-coloring.',
        ]
        with path.open('w', encoding='ascii', newline='\n') as f:
            for line in comments:
                f.write('c '+line+'\n')
            f.write(f'p cnf {K*n} {len(clauses)}\n')
            for clause in clauses:
                f.write(' '.join(map(str, clause))+' 0\n')
        return dict(file=relative, sha256=sha256(path), variables=K*n,
                    clauses=len(clauses), assignments=[list(t) for t in assignments])

    baseline = write('baseline/G328_9_clique_only.cnf', common, 'clique only')
    cases = []
    for a in range(5):
        for b in range(2):
            if a+b > 4:
                continue
            colors = list(range(1, a+1)) + [5]*b + list(range(6, 10-a-b))
            assert len(colors) == 4
            item = write(f'cases/G328_9_case_a{a}_b{b}.cnf',
                         common+list(zip(ROOTS, colors)), f'case a={a}, b={b}')
            item.update(a=a, b=b, root_colors=colors)
            cases.append(item)
    manifest = dict(graph='data/candidate328.json', graph_sha256=sha256(source),
                    vertex_count=n, edge_count=len(edges), colors=K,
                    vertex_ids='original, zero-based',
                    variable_formula='x(v,c)=9*v+c; colors 1..9',
                    clique=CLIQUE, roots=ROOTS, base_clauses=len(base),
                    baseline=baseline, cases=cases,
                    solver_status='Not run on these new CNFs')
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Wrote {len(cases)} cases: 2952 variables, 57739 clauses each.')


if __name__ == '__main__':
    main()
