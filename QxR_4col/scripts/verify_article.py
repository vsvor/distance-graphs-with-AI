#!/usr/bin/env python3
"""Exact, dependency-free checks for the local article and its certificates.

Usage: python3 scripts/verify_article.py [article.tex]
"""

import argparse
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def marked_block(tex, name):
    return tex.split(f"% BEGIN {name}")[1].split(f"% END {name}")[0]


def finite_colorings(file):
    tex = read(file)
    targets = []
    for line in marked_block(tex, "TARGET PARAMETERS").strip().splitlines():
        row = []
        for cell in line.split("&"):
            value = re.sub(r"[$\\\s]", "", cell)
            row.append(list(map(int, value[1:-1].split(",")))
                       if value.startswith("(") else int(value))
        targets.append(row)
    assert targets == [
        [3, 2, [1, 0], [1, 0], [0, 0], 3], [5, 2, [1, 0], [1, 0], [0, 0], 5],
        [7, 3, [3, 0], [2, 0], [0, 0], 4], [11, 2, [2, 0], [2, 0], [0, 0], 6],
        [13, 2, [1, 0], [0, 1], [2, 2], 6], [17, 3, [6, 0], [3, 0], [0, 0], 6],
        [19, 2, [1, 0], [7, 0], [0, 1], 6],
    ], "Printed target parameters differ from the verified parameters"
    for p in [13, 19]:
        rows = [[int(v.replace("\\", "").strip()) for v in line.split("&")]
                for line in marked_block(tex, f"C{p} TABLE").splitlines()
                if re.match(r"\d+ &", line)]
        assert len(rows) == p
        coloring = []
        for y, row in enumerate(rows):
            assert row[0] == y
            assert len(row) == p + 1
            assert all(0 <= c < 6 for c in row[1:])
            coloring.append(row[1:])
        first, second = set(), set()
        for a in range(p):
            for b in range(p):
                if (a * a + b * b) % p == 1:
                    first.add((a, b) if p == 13 else ((a + 7 * b) % p, 0))
                norm = (a - b) ** 2 + 7 * b * b if p == 13 else a * a + 2 * b * b
                if norm % p == 1:
                    second.add((a, b))
        target = first | second
        _, nu, h, u, w, _ = next(row for row in targets if row[0] == p)
        printed_target = set()
        for a in range(p):
            for b in range(p):
                if (a * a + b * b) % p == 1:
                    printed_target.add(((a * h[0] + b * u[0]) % p,
                                        (a * h[1] + b * u[1]) % p))
                if (a * a + nu * b * b) % p == 1:
                    printed_target.add(((a * h[0] + b * w[0]) % p,
                                        (a * h[1] + b * w[1]) % p))
        assert printed_target == target
        assert (0, 0) not in target
        assert len(target) == (22 if p == 13 else 26)
        if p == 13:
            assert len(first) == 12
            assert len(second) == 14
            assert first & second == {(1, 0), (12, 0), (7, 2), (6, 11)}
        else:
            explicit = {(x, 0) for a in [1, 5, 7, 8, 9] for x in [a, p - a]}
            assert first == explicit
            for a, b in [[8, 4], [9, 6], [6, 7], [5, 8]]:
                for s in [-1, 1]:
                    for t in [-1, 1]:
                        explicit.add((s * a % p, t * b % p))
            assert target == explicit
        checks = 0
        for a, b in sorted(target):
            assert (-a % p, -b % p) in target
            for y in range(p):
                for x in range(p):
                    assert coloring[y][x] != coloring[(y + b) % p][(x + a) % p], (
                        f"{file}: p={p}, ({x},{y}) + ({a},{b})")
                    checks += 1
        sizes = [sum(row.count(c) for row in coloring) for c in range(6)]
        assert sizes == ([30, 29, 25, 28, 28, 29] if p == 13
                         else [65, 60, 65, 65, 64, 42])
        print(f"{file}: p={p}, {checks} directed comparisons pass; classes {','.join(map(str, sizes))}.")

    params = [[int(re.sub(r"[$\\]", "", cell).strip()) for cell in row.split("&")]
              for row in marked_block(tex, "SCALAR PARAMETERS").strip().splitlines()]
    assert [row[0] for row in params] == [3, 5, 7, 11, 17]
    for p, nu, t, r, g, count in params:
        assert next(row for row in targets if row[0] == p) == [p, nu, [t, 0], [r, 0], [0, 0], count]
        assert count == (p + g - 1) // g
        squares = {i * i % p for i in range(1, p)}
        assert nu not in squares
        for j in range(g):
            assert (t * t - j * j) % p in squares
            value = (t * t + r * r - j * j) % p
            assert value not in squares and value != 0
        increments = set()
        for a in range(p):
            for b in range(p):
                if (a * a + b * b) % p == 1:
                    increments.add((t * a + r * b) % p)
                if (a * a + nu * b * b) % p == 1:
                    increments.add(t * a % p)
        assert 0 not in increments
        for z in increments:
            for x in range(p):
                assert x // g != ((x + z) % p) // g
        print(f"{file}: scalar p={p}, {count} colors, all increments verified.")


def dyadic_residues():
    # For square-free M, divisibility by 4 is impossible.
    # D^2 is 1 mod 2, 4 mod 16, or 16 mod 64.
    for s, m, target in [[0, 2, 1], [1, 16, 4], [2, 64, 16]]:
        checks = 0
        for M in range(m):
            if s > 0 and M % 4 == 0:
                continue
            for a in range(m):
                for b in range(m):
                    if (a * a + M * b * b) % m != target:
                        continue
                    if s == 0:
                        assert (a + M * b) % 2 == 1
                    if s == 1:
                        assert (a + (0 if M % 4 == 3 else M % 2) * b) % 4 != 0
                    if s == 2:
                        k = M % 2 if M % 4 != 3 else 0 if M % 8 == 3 else 1 if M % 16 == 7 else 3
                        assert (a + k * b) % 8 in [2, 4, 6]
                    checks += 1
        print(f"Dyadic s={s}: all {checks} admissible residue triples pass.")


def exact_graph(graph):
    vertices, radicands, denominator = (graph[name] for name in ["vertices", "radicands", "denominator"])
    assert radicands == [2, 3, 5, 35]
    assert denominator == 6
    assert len(vertices) == 23
    # Match Number.isSafeInteger, excluding JSON booleans.
    assert all(len(v) == 5 and all(type(c) is int and abs(c) <= 2 ** 53 - 1 for c in v)
               for v in vertices)
    colors = graph["colors_0_to_3"]
    assert len(colors) == 23
    assert all(type(c) is int and 0 <= c < 4 for c in colors)
    assert len({tuple(v) for v in vertices}) == 23
    edges = []
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            d = [a - b for a, b in zip(vertices[i], vertices[j])]
            squared = {1: d[0] ** 2}
            for k, r in enumerate(radicands):
                for l, s in enumerate(radicands):
                    g = math.gcd(r, s)
                    sf = r * s // (g * g)
                    squared[sf] = squared.get(sf, 0) + d[k + 1] * d[l + 1] * g
            if (squared[1] == denominator ** 2
                    and all(r == 1 or c == 0 for r, c in squared.items())):
                edges.append([i + 1, j + 1])
    assert len(edges) == 45
    assert edges == graph["edges_1based"]
    assert all(colors[a - 1] != colors[b - 1] for a, b in edges)
    print("Exact radical arithmetic: 23 distinct vertices, 45 edges, proper four-coloring.")
    return edges


def printed_coordinates(tex, graph, new_to_old):
    vertices, radicands = graph["vertices"], graph["radicands"]
    parameters = {}
    construction = tex.split(r"\section{A 4-chromatic")[1].split(r"\begin{proposition}")[0]
    for match in re.finditer(r"p_(\d)=(\d*)\\sqrt(?:\{(\d+)\}|(\d))", construction):
        index, coefficient, braced, single = match.groups()
        vector = [int(coefficient or 1) if r == int(braced or single) else 0 for r in radicands]
        assert any(vector), "Unknown printed radical"
        assert int(index) not in parameters
        parameters[int(index)] = vector
    assert len(parameters) == 4
    rows = construction.split(r"\midrule")[1].split(r"\bottomrule")[0].strip().splitlines()
    printed_vertices = []
    for row in rows:
        cells = [re.sub(r"[$\s]", "", cell)
                 for cell in re.sub(r"\\\\\s*$", "", row).split("&")]
        assert len(cells) == 3
        ids = [int(m[1] or m[2]) for m in re.finditer(r"v_(?:\{(\d+)\}|(\d+))", cells[0])]
        if r"\ldots" in cells[0]:
            ids = list(range(ids[0], ids[1] + 1))
        xs = list(map(int, cells[1].split(",")))
        assert len(xs) == len(ids)
        y = [0] * len(radicands)
        if cells[2] != "0":
            terms = list(re.finditer(r"([+-]?)(p_\d)", cells[2]))
            assert "".join(m[0] for m in terms) == cells[2], "Unsupported coordinate expression"
            for match in terms:
                sign, param = match.groups()
                vector = parameters[int(param[2:])]
                for j, c in enumerate(vector):
                    y[j] += (-1 if sign == "-" else 1) * c
        for id_, x in zip(ids, xs):
            assert id_ == len(printed_vertices) + 1
            printed_vertices.append([x] + y)
    assert printed_vertices == [vertices[i - 1] for i in new_to_old], (
        "Printed coordinates or radical parameters differ from the exact data")
    assert "v_i=(x_i/6,y_i/6)" in construction
    assert graph["denominator"] == 6
    print("Printed coordinates, radical definitions, scaling, and target parameters agree with the exact data.")


def forcing_certificate(vertices, old_to_new, adjacent):
    certificate = json.loads(read("data/qr23_proof_certificate.json"))
    expected_branches = [
        [[8, 0], [9, 0]], [[8, 0], [9, 1], [11, 1]], [[8, 0], [9, 1], [11, 2]],
        [[8, 0], [9, 2]], [[8, 1]], [[8, 2], [11, 0]], [[8, 2], [11, 1]],
    ]
    assert len(certificate["leaves"]) == 7
    # JavaScript enumerates integer object keys in numeric order.
    root = sorted((int(v), c) for v, c in certificate["root_colors"].items())
    assert [[old_to_new[v], c] for v, c in root] == [[10, 0], [17, 1], [18, 2]]
    assert adjacent(10, 17) and adjacent(10, 18) and adjacent(17, 18)
    for index, leaf in enumerate(certificate["leaves"]):
        assert [[old_to_new[v], c] for v, c in leaf["assumptions"]] == expected_branches[index]
        assigned = dict(root)
        assumptions = []
        for line in leaf["trace"]:
            match = re.fullmatch(r"ASSUME V(\d+)=(\d)\.", line)
            if match:
                v, c = map(int, match.groups())
                assert v not in assigned
                assigned[v] = c
                assumptions.append([v, c])
                continue
            match = re.fullmatch(r"V(\d+)=(\d) forced by V(\d+)=(\d), V(\d+)=(\d)\.", line)
            if match:
                v, c, a, ca, b, cb = map(int, match.groups())
                assert v not in assigned
                assert assigned.get(a) == ca and assigned.get(b) == cb
                assert adjacent(old_to_new[v], old_to_new[a]) and adjacent(old_to_new[v], old_to_new[b])
                assert len({c, ca, cb}) == 3
                assigned[v] = c
            else:
                assert line.startswith(("Normalize the triangle:", "CONTRADICTION:")), line
        assert assumptions == leaf["assumptions"]
        assert [assigned.get(i + 1, -1) for i in range(len(vertices))] == leaf["colors"]
        a, b, c = leaf["conflict"]
        assert adjacent(old_to_new[a], old_to_new[b])
        assert assigned.get(a) == c and assigned.get(b) == c
        print(f"Figure case {index + 1}: every forcing step and final conflict verified.")


def exhaustive_coloring(fixed_edges):
    # Independent backtracking, with only color permutation symmetry fixed.
    neighbors = [[] for _ in range(24)]
    for a, b in fixed_edges:
        neighbors[a].append(b)
        neighbors[b].append(a)
    colors = [-1] * 24
    colors[10], colors[17], colors[18] = 0, 1, 2
    calls = 0

    def colorable():
        nonlocal calls
        calls += 1
        best, available = 0, []
        for v in range(1, 24):
            if colors[v] == -1:
                choices = [c for c in range(3) if all(colors[w] != c for w in neighbors[v])]
                if not best or len(choices) < len(available):
                    best, available = v, choices
        if not best:
            return True
        for c in available:
            colors[best] = c
            if colorable():
                return True
        colors[best] = -1
        return False

    assert not colorable()
    print(f"Independent exhaustive search: no three-coloring ({calls} recursive calls).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", nargs="?", default="article.tex")
    args = parser.parse_args()
    if not __debug__:
        parser.error("checks require assertions; run Python without -O or PYTHONOPTIMIZE")
    finite_colorings(args.article)
    assert math.prod([16, 3, 5, 7, 11, 13, 17, 19]) == 77597520
    dyadic_residues()
    graph = json.loads(read("data/qr23.json"))
    edges = exact_graph(graph)
    new_to_old = [12, 13, 14, 15, 23, 16, 1, 2, 3, 4, 5, 6, 7, 17, 18, 19, 21, 22, 8, 9, 10, 11, 20]
    old_to_new = {old: i for i, old in enumerate(new_to_old, start=1)}
    fixed_edges = [(old_to_new[a], old_to_new[b]) for a, b in edges]
    edge_set = {frozenset(edge) for edge in fixed_edges}

    def adjacent(a, b):
        return frozenset((a, b)) in edge_set

    printed_coordinates(read(args.article), graph, new_to_old)
    forcing_certificate(graph["vertices"], old_to_new, adjacent)
    exhaustive_coloring(fixed_edges)
    print("All article certificate checks passed.")


if __name__ == "__main__":
    main()
