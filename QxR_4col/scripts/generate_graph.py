#!/usr/bin/env python3
"""Regenerate the graph and exhaustive forcing certificate exactly.

Usage: python3 scripts/generate_graph.py [--check]
"""

import argparse
import json
from pathlib import Path


OUTPUT = Path(__file__).resolve().parents[1] / "data"
RADICANDS = [2, 3, 5, 35]
DENOMINATOR = 6
# (X,a2,a3,a5,a35) represents (X, sum ar sqrt(r))/6.
VERTICES = [
    [-6, 0, 0, 0, 0], [-4, 0, 0, 0, 0], [-2, 0, 0, 0, 0],
    [0, 0, 0, 0, 0], [2, 0, 0, 0, 0], [4, 0, 0, 0, 0], [6, 0, 0, 0, 0],
    [-4, 4, 0, 0, 0], [-2, 4, 0, 0, 0], [0, 4, 0, 0, 0], [4, 4, 0, 0, 0],
    [-3, 0, 0, 0, -1], [1, 0, 0, 0, -1], [3, 0, 0, 0, -1], [5, 0, 0, 0, -1],
    [-1, 4, 0, 0, -1], [-2, 0, 0, 2, 0], [0, 0, 0, 2, 0], [2, 0, 0, 2, 0],
    [0, 4, 0, 2, 0], [-3, 0, 3, 0, 0], [3, 0, 3, 0, 0], [1, 0, 0, 2, -1],
]


def radical_product(r, s):
    n = r * s
    factor = 1
    candidate = 2
    while candidate * candidate <= n:
        if n % (candidate * candidate) == 0:
            factor = candidate
        candidate += 1
    return factor, n // (factor * factor)


def generate():
    assert len({tuple(v) for v in VERTICES}) == 23
    # All operations affecting adjacency are on exact integers.
    edges = []
    for u in range(23):
        for v in range(u + 1, 23):
            d = [a - b for a, b in zip(VERTICES[u], VERTICES[v])]
            squared = {1: d[0] ** 2}
            for i, r in enumerate(RADICANDS):
                for j, s in enumerate(RADICANDS):
                    factor, radicand = radical_product(r, s)
                    squared[radicand] = (squared.get(radicand, 0)
                                         + factor * d[i + 1] * d[j + 1])
            if (squared[1] == DENOMINATOR ** 2
                    and all(r == 1 or c == 0 for r, c in squared.items())):
                edges.append([u + 1, v + 1])
    assert len(edges) == 45
    assert all(p[3] % 2 == 0 for p in VERTICES)
    colors = [2 * (p[0] % 2) + (p[0] // 2 + p[3] // 2) % 2
              for p in VERTICES]
    neighbors = [[] for _ in VERTICES]
    for u, v in edges:
        assert colors[u - 1] != colors[v - 1]
        neighbors[u - 1].append(v - 1)
        neighbors[v - 1].append(u - 1)
    for adjacent in neighbors:
        adjacent.sort()

    # Stored labels; each branch contains every available color.
    # String keys preserve the JSON representation of the JavaScript version.
    root_colors = {"4": 0, "21": 1, "22": 2}
    tree = [2, {"0": [3, {"0": None, "1": [5, {"1": None, "2": None}],
                         "2": None}],
                "1": None, "2": [5, {"0": None, "1": None}]}]
    initial = [-1] * 23
    for v, c in root_colors.items():
        initial[int(v) - 1] = c
    for u, v in [[4, 21], [4, 22], [21, 22]]:
        assert v - 1 in neighbors[u - 1]
    leaves = []
    nodes = 0

    def saturate(state, trace):
        while True:
            for u, v in edges:
                if state[u - 1] >= 0 and state[u - 1] == state[v - 1]:
                    return [u, v, state[u - 1]]
            for v in range(23):
                if state[v] >= 0:
                    continue
                witnesses = {}
                for w in neighbors[v]:
                    if state[w] >= 0:
                        witnesses.setdefault(state[w], w)
                if len(witnesses) < 2:
                    continue
                c1, c2 = sorted(witnesses)[:2]
                c = 3 - c1 - c2
                u, w = witnesses[c1], witnesses[c2]
                state[v] = c
                trace.append(f"V{v + 1}={c} forced by V{u + 1}={c1}, V{w + 1}={c2}.")
                break
            else:
                return None

    def walk(branch, previous, assumptions, history):
        nonlocal nodes
        nodes += 1
        state, trace = previous.copy(), history.copy()
        conflict = saturate(state, trace)
        if conflict:
            assert branch is None, "Conflict before the declared leaf"
            u, v, c = conflict
            trace.append(f"CONTRADICTION: the edge V{u}--V{v} has color {c} at both endpoints.")
            leaves.append({"assumptions": assumptions, "conflict": conflict,
                           "trace": trace, "colors": state})
            return
        assert branch is not None, "A leaf has no conflict"
        label, children = branch
        v = label - 1
        assert state[v] == -1
        allowed = [c for c in range(3) if all(state[w] != c for w in neighbors[v])]
        assert list(map(int, children)) == allowed, "Incomplete branch"
        for c in allowed:
            child = state.copy()
            child[v] = c
            walk(children[str(c)], child, assumptions + [[label, c]],
                 trace + [f"ASSUME V{label}={c}."])

    walk(tree, initial, [], ["Normalize the triangle: V4=0, V21=1, V22=2."])
    assert nodes == 11
    assert len(leaves) == 7
    graph = {
        "description": "23-vertex 4-chromatic unit-distance graph in Q x R",
        "denominator": DENOMINATOR,
        "radicands": RADICANDS,
        "coordinate_convention": "(X,a2,a3,a5,a35) -> (X/6,(a2 sqrt2+a3 sqrt3+a5 sqrt5+a35 sqrt35)/6)",
        "vertices": VERTICES,
        "edges_1based": edges,
        "colors_0_to_3": colors,
    }
    return graph, {"root_colors": root_colors, "tree": tree, "leaves": leaves}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="compare with committed JSON without writing files")
    args = parser.parse_args()
    if not __debug__:
        parser.error("checks require assertions; run Python without -O or PYTHONOPTIMIZE")
    graph, certificate = generate()
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, data in [("qr23.json", graph), ("qr23_proof_certificate.json", certificate)]:
        file = OUTPUT / name
        if args.check:
            assert json.loads(file.read_text(encoding="utf-8")) == data, name + " is stale"
        else:
            # Match JSON.stringify(data, null, 2), including the trailing newline.
            file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    action = "Checked" if args.check else "Generated"
    print(f"{action} exact graph and certificate: 23 vertices, 45 edges, seven exhaustive cases.")


if __name__ == "__main__":
    main()
