#!/usr/bin/env python3
"""Exact checks for the dyadic certificates; no third-party dependencies.

Usage: python3 scripts/verify_dyadic16.py [article.tex]
"""

import argparse
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def color_table(article):
    block = article.split("% BEGIN C16 TABLE")[1].split("% END C16 TABLE")[0]
    rows = []
    for line in block.splitlines():
        if not re.match(r"\d+ &", line):
            continue
        cells = [int(v.replace("\\", "").strip()) for v in line.split("&")]
        assert cells[0] == len(rows)
        assert len(cells) == 17
        assert all(0 <= c < 6 for c in cells[1:])
        rows.append(cells[1:])
    assert len(rows) == 16
    return rows


def check_coloring(rows):
    target = set()
    # Preserve insertion order for deterministic residue diagnostics.
    shifts = []

    def add(a, b):
        if (a, b) not in target:
            target.add((a, b))
            shifts.append((a, b))

    for a in range(1, 16, 2):
        add(a, 0)
        add(0, a)
    for a in range(2, 16, 4):
        add(a, 8)
        add(8, a)
    for a in [4, 8, 12]:
        add(a, a)
    assert len(target) == 27
    assert (0, 0) not in target
    for a, b in shifts:
        assert (-a % 16, -b % 16) in target
    comparisons = 0
    for y in range(16):
        for x in range(16):
            for a, b in shifts:
                assert rows[y][x] != rows[(y + b) % 16][(x + a) % 16]
                comparisons += 1
    sizes = [sum(row.count(c) for row in rows) for c in range(6)]
    assert sizes == [47, 45, 44, 39, 38, 43]
    print(f"C16: {comparisons} directed checks pass; 256 vertices, 3456 edges; classes {','.join(map(str, sizes))}.")
    return target, shifts


def check_transfer(target):
    roots = {}
    for r in range(1, 256, 2):
        roots.setdefault(r * r % 256, r)
    assert sorted(roots) == [8 * i + 1 for i in range(32)]
    observed = set()
    by_class = {"ordinary": 0, "class3": 0, "split": 0}
    residue_checks = 0
    for M in range(256):
        if M % 4 == 0:
            continue
        if M % 4 != 3:
            alpha = beta = M % 2
            type_ = "ordinary"
        elif M % 8 == 3:
            r = roots[M * 171 % 256]  # 171 is the inverse of 3 modulo 256.
            assert (3 * r * r - M) % 256 == 0
            alpha = beta = 3 * r
            type_ = "class3"
        else:
            r = roots[-M % 256]
            assert (r * r + M) % 256 == 0
            alpha, beta = r, -r
            type_ = "split"
        for a in range(128):
            for b in range(128):
                if (a * a + M * b * b) % 256 != 64:
                    continue
                f, g = a + alpha * b, a + beta * b
                assert f % 2 == 0 and g % 2 == 0
                step = (f // 2 % 16, g // 2 % 16)
                assert step in target, f"Bad image for {M},{a},{b}: {step[0]},{step[1]}"
                observed.add(step)
                by_class[type_] += 1
                residue_checks += 1
    assert residue_checks == 28672
    assert observed == target
    for delta in range(-64, 65, 2):
        for start in range(-64, 65):
            assert (start + delta) // 2 - start // 2 == delta // 2
    for q in range(-15, 16, 2):
        assert (4 * q % 16, 4 * q % 16) in target
    classes = json.dumps(by_class, separators=(",", ":"))
    print(f"Transfer: {residue_checks} residue triples pass ({classes}), including negative half-increments.")


def check_cnf(rows, shifts):
    # Check the conventional exactly-one-color CNF encoding independently.
    clauses = 0
    for v in range(256):
        bits = [rows[v // 16][v % 16] == c for c in range(6)]
        assert any(bits)
        clauses += 1
        for c in range(6):
            for d in range(c + 1, 6):
                assert not bits[c] or not bits[d]
                clauses += 1
        for a, b in shifts:
            w = 16 * ((v // 16 + b) % 16) + (v % 16 + a) % 16
            if w <= v:
                continue
            for c in range(6):
                assert not bits[c] or rows[w // 16][w % 16] != c
                clauses += 1
    assert clauses == 24832
    print(f"CNF encoding: 1536 variables, all {clauses} clauses satisfied.")


def inverse(u, n):
    for v in range(1, n, 2):
        if u * v % n == 1:
            return v
    raise ValueError("Not a unit")


def dyadic_target(s, m):
    n = 2 ** m
    target = set()
    for u in range(1, n, 2):
        inv = inverse(u, n)
        for j in range(2 * s - 1):
            target.add((2 ** j * u % n, 2 ** (2 * s - 2 - j) * inv % n))
        for j in [s - 1, s]:
            target.add((2 ** j * u % n, 2 ** j * u % n))
    assert (0, 0) not in target
    return target


def check_spectrum(article, target):
    assert dyadic_target(3, 4) == target
    weighted = {}

    def put(a, b, weight):
        assert (a, b) not in weighted
        weighted[a, b] = weight

    for a in range(1, 32, 2):
        put(a, 0, 5)
        put(0, a, 5)
    for a in range(2, 32, 4):
        put(a, 0, 5)
        put(0, a, 5)
    for a in range(4, 32, 8):
        put(a, 16, 2)
        put(16, a, 2)
    put(8, 8, 8)
    put(24, 24, 8)
    put(16, 16, 0)
    assert set(weighted) == dyadic_target(4, 5)
    assert len(weighted) == 59
    assert sum(weighted.values()) == 272

    # All Fourier eigenvalues in Z[zeta_32], using zeta_32^16 = -1.
    # This checks the printed spectrum without floating-point trigonometry.
    spectrum = {}

    def R(j, r):
        if r % (32 >> j) == 0:
            return 16 >> j
        if r % (16 >> j) == 0:
            return -(16 >> j)
        return 0

    for r in range(32):
        for t in range(32):
            coeff = [0] * 16
            for (a, b), weight in weighted.items():
                e = (r * a + t * b) % 32
                coeff[e % 16] += weight if e < 16 else -weight
            assert all(c == 0 for c in coeff[1:])
            eigenvalue = coeff[0]
            formula = (5 * (R(0, r) + R(0, t)) + 5 * (R(1, r) + R(1, t))
                       + 2 * ((-1) ** t * R(2, r) + (-1) ** r * R(2, t))
                       + 16 * [1, 0, -1, 0][(r + t) % 4])
            assert eigenvalue == formula
            spectrum[eigenvalue] = spectrum.get(eigenvalue, 0) + 1
    expected = [[-48, 153], [-24, 88], [-16, 128], [0, 272], [8, 128],
                [16, 192], [112, 54], [136, 8], [272, 1]]
    assert [list(pair) for pair in sorted(spectrum.items())] == expected

    def spectrum_row(label):
        line = next((s for s in article.splitlines() if s.startswith(r"\text{" + label + "}&")), None)
        assert line is not None, "Missing printed spectrum row: " + label
        return [int(re.sub(r"\.$", "", re.sub(r"\\.*$", "", s)).strip())
                for s in line.split("&")[1:]]

    assert spectrum_row("Eigenvalue") == [value for value, _ in expected]
    assert spectrum_row("Multiplicity") == [count for _, count in expected]
    printed = json.dumps(expected, separators=(",", ":"))
    print(f"H_4,5: exact spectrum {printed}; weighted degree 272, minimum -48, chromatic bound 20/3.")
    assert len(dyadic_target(4, 6)) * 4096 // 2 == 241664
    assert math.prod([16, 3, 5, 7, 11, 13, 17, 19]) == 77597520
    assert r"77\,597\,520=16\cdot3" in article
    assert r"38\,798\,760" not in article


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", nargs="?", default="article.tex")
    args = parser.parse_args()
    if not __debug__:
        parser.error("checks require assertions; run Python without -O or PYTHONOPTIMIZE")
    article = (ROOT / args.article).read_text(encoding="utf-8")
    print(f"Checking dyadic certificates in {args.article}.")
    rows = color_table(article)
    target, shifts = check_coloring(rows)
    check_transfer(target)
    check_cnf(rows, shifts)
    check_spectrum(article, target)
    print("All dyadic certificate checks passed. The external Borel bound is not checked by this script.")


if __name__ == "__main__":
    main()
