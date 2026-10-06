#!/usr/bin/env python3
"""Independent geometry, CNF, and exhaustive finite case-coverage checks."""
import argparse
from collections import Counter
from itertools import combinations, permutations, product
import hashlib
import json
from pathlib import Path
from build_graph import construct
from exact import published_vertices, edges as exact_edges, in_module, color9


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse(path):
    header = None
    clauses = []
    pending = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p'):
            require(header is None, 'Duplicate DIMACS header')
            p, kind, nv, nc = line.split()
            require(kind == 'cnf', 'Not CNF')
            header = int(nv), int(nc)
            continue
        for literal in map(int, line.split()):
            if literal:
                pending.append(literal)
            else:
                clauses.append(tuple(sorted(pending)))
                pending = []
    require(not pending and header is not None, 'Incomplete DIMACS')
    require(header[1] == len(clauses), 'Clause count mismatch')
    require(all(0 < abs(x) <= header[0] for c in clauses for x in c), 'Bad literal')
    return header, clauses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument('--reference-light', type=Path)
    parser.add_argument('--reference-plain', type=Path)
    args = parser.parse_args()
    root = args.directory
    manifest = json.loads((root/'cnf'/'manifest.json').read_text())
    graph_path = root/'data'/'candidate328.json'
    require(digest(graph_path) == manifest['graph_sha256'], 'Graph hash mismatch')
    provenance = json.loads((root/'data'/'provenance.json').read_text())
    require(digest(graph_path) == provenance['source_graph_sha256'], 'Historical graph changed')
    graph = json.loads(graph_path.read_text())
    vertices = [tuple(v) for v in graph['vertices']]
    n = len(vertices)
    require(all(len(v) == 8 and all(type(t) is int for t in v) for v in vertices), 'Invalid coefficient format')
    require(n == 328 and len(set(vertices)) == n, 'Wrong vertices')
    edges = {tuple(sorted(e)) for e in graph['edges']}
    require(len(edges) == len(graph['edges']) == 5066, 'Wrong/duplicate edges')
    exact = set()
    for u, v in combinations(range(n), 2):
        d = [a-b for a, b in zip(vertices[u], vertices[v])]
        rational = sum(d[i]**2+5*d[i+1]**2 for i in range(0, 8, 2))
        irrational = 2*sum(d[i]*d[i+1] for i in range(0, 8, 2))
        if (rational, irrational) == (32, 0):
            exact.add((u, v))
    require(edges == exact, 'Edges differ from exact squared-distance-32 graph')
    clique, negative = [64, 39, 36, 34, 51], [0, 28, 31, 33]
    require(manifest['clique'] == clique and manifest['roots'] == negative, 'Wrong anchors')
    def adjacent(u, v):
        return tuple(sorted((u, v))) in edges
    require(all(adjacent(u, v) for u, v in combinations(clique, 2)), 'Not K5')
    require(all(adjacent(u, v) for u, v in combinations(negative, 2)), 'Not K4')
    for i in range(4):
        positive_point = [0]*8
        negative_point = [0]*8
        positive_point[2*i], negative_point[2*i] = 4, -4
        require(vertices[clique[i]] == tuple(positive_point), 'Wrong positive axis')
        require(vertices[negative[i]] == tuple(negative_point), 'Wrong negative axis')
        require([adjacent(negative[i], v) for v in clique] ==
                [j != i for j in range(4)]+[False], 'Wrong root-clique adjacency')
    require(vertices[51] == (1, 1)*4, 'Wrong diagonal anchor')
    index = {p: i for i, p in enumerate(vertices)}
    coordinate_actions = []
    for order in permutations(range(4)):
        action = [index[tuple(z for i in order for z in p[2*i:2*i+2])]
                  for p in vertices]
        require(len(set(action)) == n, 'Not a vertex permutation')
        require({tuple(sorted((action[u], action[v]))) for u, v in edges} == edges,
                'Coordinate permutation is not a graph automorphism')
        coordinate_actions.append(order)

    # Construct from the seed and the full direction set, not just the saved edges.
    seed, vectors, support, points = construct()
    require(set(vertices) == points, 'Constructed vertex set differs')
    require(vertices[:65] == seed, 'Historical seed prefix differs')
    require(len(vectors) == 2008, 'Incorrect direction set')
    require(sum(not in_module(v) for v in vertices) == 152, 'Wrong module count')
    seed_data = json.loads((root/'data'/'eil65_corrected.json').read_text())
    require(seed_data['vertices'] == [list(v) for v in seed], 'Seed data differs')
    seed_edges = {tuple(sorted(e)) for e in exact_edges(seed)}
    require(len(seed_edges) == 588 and seed_edges == {tuple(e) for e in seed_data['edges']}, 'Seed edge set')
    c9 = seed_data['verified_coloring']
    require(len(c9) == 65 and len(set(c9)) == 9 and all(c9[u] != c9[v] for u, v in seed_edges), 'Seed 9-coloring')
    literal = published_vertices(literal=True)
    literal_edges = exact_edges(literal)
    literal_degree = Counter(v for e in literal_edges for v in e)
    require(len(literal) == 65 and len(literal_edges) == 472 and
            sum(literal_degree[v] == 0 for v in range(65)) == 4, 'Literal-table comparison')
    module_directions = [v for v in vectors if in_module(v)]
    require(len(module_directions) == 216 and all(color9(v) != 0 for v in module_directions), 'Module coloring check')
    # Completeness of Aut(G)=S4: max-degree vertices form an invariant 4-set,
    # and individualizing them makes color refinement discrete.
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    degrees = list(map(len, adj))
    require(max(degrees) == 77 and {v for v in range(n) if degrees[v] == 77} == set(clique[:4]), 'Maximum-degree anchor')
    labels = [4]*n
    for i, v in enumerate(clique[:4]):
        labels[v] = i
    refinement = [5]
    while len(set(labels)) < n:
        signatures = [(labels[v], tuple(sorted(Counter(labels[u] for u in adj[v]).items()))) for v in range(n)]
        mapping = {sig: i for i, sig in enumerate(sorted(set(signatures)))}
        require(len(mapping) > refinement[-1], 'Pointwise stabilizer not certified trivial')
        labels = [mapping[sig] for sig in signatures]
        refinement.append(len(mapping))
    require(refinement == [5, 91, 320, 328], 'Refinement trace differs')
    # Verify the graph text files used by the standalone C++ program.
    for name, expected_edges, count in [('candidate328', edges, n), ('eil65_corrected', seed_edges, 65)]:
        rows = [list(map(int, line.split())) for line in (root/'data'/(name+'.txt')).read_text().splitlines()]
        require(rows[0] == [count, len(expected_edges)] and len(rows[1:]) == len(expected_edges) and
                {tuple(sorted(row)) for row in rows[1:]} == expected_edges, 'Text graph differs: '+name)

    # Independently list every proper coloring of the four roots after K5 is fixed.
    raw = {c for c in product(range(1, 10), repeat=4)
           if len(set(c)) == 4 and all(c[i] == i+1 or c[i] >= 5 for i in range(4))}
    expected_reps = {
        (6, 7, 8, 9), (5, 6, 7, 8), (1, 6, 7, 8),
        (1, 5, 6, 7), (1, 2, 6, 7), (1, 2, 5, 6),
        (1, 2, 3, 6), (1, 2, 3, 5), (1, 2, 3, 4),
    }
    reps = {tuple(case['root_colors']) for case in manifest['cases']}
    require(reps == expected_reps and len(manifest['cases']) == 9, 'Wrong representatives')
    orbit_sizes = {}
    covered = set()
    for colors in sorted(reps):
        orbit = set()
        for order in coordinate_actions:
            # New coordinate i is old coordinate order[i]. Compensate the four
            # positive-axis colors so that the precolored clique stays fixed.
            compensation = {order[i]+1: i+1 for i in range(4)}
            for free in permutations(range(6, 10)):
                renaming = {**compensation, 5: 5,
                            **dict(zip(range(6, 10), free))}
                orbit.add(tuple(renaming[colors[order[i]]] for i in range(4)))
        require(not (covered & orbit), 'Root representatives have overlapping orbits')
        covered.update(orbit)
        orbit_sizes[','.join(map(str, colors))] = len(orbit)
    require(covered == raw, 'Root case split is not exhaustive')

    # Independent expected clause multiset built from mathematical constraints.
    expected = Counter()
    for v in range(n):
        variables = list(range(9*v+1, 9*v+10))
        expected[tuple(variables)] += 1
        for x, y in combinations(variables, 2):
            expected[tuple(sorted((-x, -y)))] += 1
    for u, v in exact:
        for c in range(1, 10):
            expected[tuple(sorted((-9*u-c, -9*v-c)))] += 1
    require(sum(expected.values()) == 57730, 'Base count incorrect')
    checked_files = []
    for entry in [manifest['baseline']]+manifest['cases']:
        path = root/'cnf'/entry['file']
        require(digest(path) == entry['sha256'], 'CNF hash mismatch: '+entry['file'])
        if entry in manifest['cases']:
            require(digest(path) == provenance['original_assignment_case_hashes'][path.name], 'Original assignment CNF bytes changed')
        header, clauses = parse(path)
        assignments = list(zip(clique, range(1, 6)))
        if entry in manifest['cases']:
            assignments += list(zip(negative, entry['root_colors']))
        require(entry['assignments'] == [list(t) for t in assignments], 'Wrong assignments')
        units = Counter((9*v+c,) for v, c in assignments)
        require(Counter(clauses) == expected+units, 'Unexpected/missing CNF clauses')
        require(header == (2952, 57730+len(assignments)), 'Wrong CNF header')
        require(sum(len(c) == 1 for c in clauses) == len(assignments), 'Wrong units')
        checked_files.append(dict(file=entry['file'], variables=header[0],
                                  clauses=header[1], unit_clauses=len(assignments)))

    # Positive control: validate the source's supplied 10-coloring geometrically.
    known = graph['verified_coloring']
    require(len(known) == n and len(set(known)) == 10, 'Bad positive-control coloring')
    require(all(known[u] != known[v] for u, v in exact), '10-coloring fails')

    references = {}
    for label, path in [('light', args.reference_light), ('plain', args.reference_plain)]:
        if path is None:
            continue
        header, clauses = parse(path)
        require(Counter(clauses[:57730]) == expected, 'Original base differs')
        references[label] = dict(filename=path.name, sha256=digest(path),
                                 variables=header[0], clauses=header[1],
                                 original_first_57730_clauses_match=True)
        if label == 'light':
            require(set(clauses[57730:57735]) ==
                    {(9*v+c,) for v, c in zip(clique, range(1, 6))},
                    'Original light clique differs')
    report = dict(status='PASS', vertices=n, edges=len(exact),
                  construction_rebuilt=True, seed_vertices=65, seed_edges=588,
                  directions=len(vectors), outside_module=152,
                  literal_table_edges=472, literal_table_isolates=4,
                  full_automorphism_group='S4', refinement_cell_counts=refinement,
                  exact_vertex_pairs_checked=n*(n-1)//2,
                  coordinate_automorphisms_verified=len(coordinate_actions),
                  legal_root_assignments=len(raw), root_orbits=orbit_sizes,
                  coverage='All 501 legal root assignments covered; orbits disjoint',
                  files=checked_files, source_comparisons=references,
                  source_10_coloring_checked=True, SAT_solver_run=False,
                  UNSAT_proof_checked=False)
    (root/'results').mkdir(exist_ok=True)
    (root/'results'/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
