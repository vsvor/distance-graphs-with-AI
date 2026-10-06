#!/usr/bin/env python3
"""Validate a complete DIMACS SAT model against graph edges and the exact CNF."""
import argparse
import json
from pathlib import Path
from verify import parse, require


def check(graph, colors, model, cnf):
    require(colors > 0, 'Color count must be positive')
    data = json.loads(Path(graph).read_text())
    assignment = {}
    for line in Path(model).read_text().splitlines():
        fields = line.split()
        if not fields or fields[0] != 'v':
            continue
        for lit in map(int, fields[1:]):
            if not lit:
                continue
            require(abs(lit) not in assignment or assignment[abs(lit)] == (lit > 0),
                    'Contradictory model literals')
            assignment[abs(lit)] = lit > 0
    header, clauses = parse(Path(cnf))
    require(all(v in assignment for v in range(1, header[0]+1)), 'Incomplete model')
    require(all(1 <= v <= header[0] for v in assignment), 'Out-of-range model variable')
    require(all(any(assignment[abs(x)] == (x > 0) for x in clause)
                for clause in clauses), 'Model violates a CNF clause')
    require(header[0] >= colors*len(data['vertices']), 'Missing graph variables')
    coloring = []
    for v in range(len(data['vertices'])):
        active = [c for c in range(1, colors+1) if assignment[colors*v+c]]
        require(len(active) == 1, f'Vertex {v} does not have exactly one color')
        coloring.append(active[0])
    require(all(coloring[u] != coloring[v] for u, v in data['edges']),
            'Monochromatic edge')
    return coloring, len(clauses)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('graph', type=Path)
    p.add_argument('colors', type=int)
    p.add_argument('model', type=Path)
    p.add_argument('--cnf', required=True, type=Path)
    p.add_argument('--save', type=Path)
    a = p.parse_args()
    coloring, count = check(a.graph, a.colors, a.model, a.cnf)
    if a.save:
        a.save.write_text(json.dumps(dict(vertex_ids='zero-based', colors='one-based',
                                         coloring=coloring), indent=2)+'\n')
    print(f'VALID: {len(coloring)} vertices, {len(set(coloring))} colors, {count} clauses')


if __name__ == '__main__':
    main()
