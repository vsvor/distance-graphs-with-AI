#!/usr/bin/env python3
"""Reconstruct G328 exactly from ten seed orbits and the support >=8 rule."""
import argparse
from collections import Counter
import json
from pathlib import Path
from exact import directions, edges, published_vertices, in_module

ROOT = Path(__file__).resolve().parents[1]


def construct():
    seed = published_vertices()
    vectors = directions()
    support = Counter(tuple(a+b for a, b in zip(v, d))
                      for v in seed for d in vectors)
    points = set(seed) | {p for p, count in support.items() if count >= 8}
    return seed, vectors, support, points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'build'/'graphs')
    parser.add_argument('--canonical-order', action='store_true',
                        help='Sort all points and write an original-ID mapping')
    args = parser.parse_args()
    seed, vectors, support, points = construct()
    original = json.loads((ROOT/'data'/'candidate328.json').read_text())
    saved = [tuple(p) for p in original['vertices']]
    if len(saved) != len(set(saved)) or set(saved) != points:
        raise ValueError('Constructed vertex set differs from saved original IDs')
    vertices = sorted(points) if args.canonical_order else saved
    edge_list = sorted(tuple(sorted(e)) for e in edges(vertices))
    if (len(seed), len(vectors), len(vertices), len(edge_list)) != (65, 2008, 328, 5066):
        raise ValueError('Unexpected construction counts')
    args.out.mkdir(parents=True, exist_ok=True)
    graph = dict(name='G328', dimension=4, forbidden_squared_distance=32,
                 coefficient_encoding='[a0,b0,...,a3,b3] means ai+bi*sqrt(5)',
                 vertex_order='canonical' if args.canonical_order else 'historical',
                 vertices=vertices, edges=edge_list)
    (args.out/'candidate328.json').write_text(json.dumps(graph, indent=2)+'\n')
    with (args.out/'candidate328.txt').open('w') as f:
        f.write(f'{len(vertices)} {len(edge_list)}\n')
        for u, v in edge_list:
            f.write(f'{u} {v}\n')
    lookup = {p: i for i, p in enumerate(saved)}
    (args.out/'original_vertex_ids.json').write_text(
        json.dumps([lookup[p] for p in vertices])+'\n')
    report = dict(seed_vertices=len(seed), seed_edges=len(edges(seed)),
                  directions=len(vectors), support_threshold=8,
                  vertices=len(vertices), edges=len(edge_list),
                  outside_module=sum(not in_module(p) for p in vertices),
                  original_vertex_set_matches=True)
    (args.out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
