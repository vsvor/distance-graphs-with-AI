#!/usr/bin/env python3
"""Rebuild historical light/full CNFs; audit primitives and positive witnesses."""
import gc
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'legacy'))
from prepare import graph_data, encode
from primitives import primitive_tests
from check_model import check


def require(ok, message):
    if not ok:
        raise ValueError(message)


def make(graph, k, mode, path, witness=False):
    data, vertices, edges, adj, clique, negative, group, coord, orbits, order = graph_data(graph)
    cnf, _, _, _ = encode(data, edges, clique, negative, group, order, k,
                          mode, True, 0, data['verified_coloring'] if witness else None)
    cnf.write(path, [f'{len(vertices)} vertices; {len(edges)} edges; k={k}; mode={mode}',
                     'Original zero-based vertex IDs; color variable = k*v+c+1.',
                     'Full mode uses compensated coordinate actions followed by free-color normalization.',
                     'Do not combine with a different precolored clique or unrelated symmetry breakers.'])
    return cnf.nv, len(cnf.clauses)


def main():
    prov = json.loads((ROOT/'data'/'provenance.json').read_text())
    require(hashlib.sha256((ROOT/'legacy'/'prepare.py').read_bytes()).hexdigest() ==
            prov['legacy_prepare_py_sha256'], 'Historical generator bytes changed')
    report = dict(primitive_tests=primitive_tests(), rebuilt={}, positive_controls=[])
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        for mode in ('light', 'full'):
            path = folder/f'candidate328_9_{mode}.cnf'
            nv, nc = make(ROOT/'data'/'candidate328.json', 9, mode, path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            require(sha == prov[f'historical_{mode}_sha256'], mode+' CNF hash changed')
            if mode == 'light':
                original = gzip.decompress((ROOT/'legacy'/'reference'/
                                            'candidate328_9_light.cnf.gz').read_bytes())
                require(original == path.read_bytes(), 'Bundled light CNF differs')
            report['rebuilt'][mode] = dict(variables=nv, clauses=nc, sha256=sha)
            gc.collect()
        for graph, k in [('candidate328.json', 10), ('eil65_corrected.json', 9)]:
            for mode in ('light', 'full'):
                path = folder/f'{graph}_{k}_{mode}.cnf'
                nv, nc = make(ROOT/'data'/graph, k, mode, path, witness=True)
                coloring, checked = check(ROOT/'data'/graph, k, path.with_suffix('.model'), path)
                report['positive_controls'].append(dict(graph=graph, colors=k, mode=mode,
                                                         variables=nv, clauses_checked=checked))
                gc.collect()
    report.update(status='PASS', G328_9_color_SAT_solver_run=False, UNSAT_proof_checked=False)
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results'/'legacy_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
