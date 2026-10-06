# Chromatic numbers of Q × R

Supplement to Vsevolod Voronov's *A construction of a 4-chromatic
unit-distance graph in Q × R*. The repository contains one manuscript source,
exact graph data, a generator, independent verifiers, and a figure script.

## Verify

From the repository root, run:

```sh
make verify
```

Verification requires Python 3.8 or later, with no third-party packages. Without
`make`, run these commands directly:

```sh
python3 scripts/generate_graph.py --check
python3 scripts/verify_article.py
python3 scripts/verify_dyadic16.py
```

The checks reconstruct all 45 unit-distance edges using exact radical
arithmetic, compare the printed coordinates and parameters with the data,
check the four-coloring and each step of the seven-case forcing proof, and
independently exhaust all possible three-colorings. They also check the
scalar targets, the six-color tables modulo 13, 19, and 16, the dyadic
transfer residues, and the exact weighted spectrum of the target on
`(Z/32Z)²`. Any failed check exits with a nonzero status.

These are finite certificate checks, not a formal verification of all
general proofs or of cited external theorems. No claim of minimum order for
the 23-vertex graph is made.

## Regenerate

Regenerate the graph data and exhaustive forcing certificate:

```sh
python3 scripts/generate_graph.py
```

The generator starts from integer coordinate coefficients and the branching
tree, computes the edges and four-coloring, and derives every forced
assignment. `--check` compares its result with the committed JSON files
without writing them. The finite coloring tables are supplied in
`article.tex`; verification checks them directly rather than searching for
new tables.

To draw all eight panels, install Python 3 and Matplotlib:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make figures PYTHON=.venv/bin/python
```

The script writes PDF panels and PNG previews into `figures/`. Black labels
identify article vertices; white numbers in the contradiction panels give
the coloring order. The four-coloring panel uses colored fills without
white numbers. Floating-point arithmetic is used only for drawing.

`make generate PYTHON=.venv/bin/python` regenerates both the data and figures.
With a LaTeX installation providing the packages used in `article.tex`,
BibTeX, and `latexmk`, build the article with:

```sh
make article PYTHON=.venv/bin/python
```

Generated figures, PDFs, and build caches are ignored by Git. Verification
needs neither Matplotlib nor LaTeX. Scripts resolve their data paths relative
to the repository and can also be invoked from another working directory.
The original JavaScript scripts remain available for comparison and require
Node.js 12 or later.

## Data convention and files

A vertex record `[X,a2,a3,a5,a35]` represents

```text
(X/6, (a2√2 + a3√3 + a5√5 + a35√35)/6).
```

JSON edges and proof labels are 1-based indices into the stored vertex list.
The article and figures relabel the vertices by increasing vertical
coordinate, then increasing horizontal coordinate. Article labels 1–23
correspond to the following stored labels:

```text
12 13 14 15 23 16 1 2 3 4 5 6 7 17 18 19 21 22 8 9 10 11 20
```

| File | Content |
| --- | --- |
| `article.tex`, `references.bib` | Manuscript and cited bibliography entries |
| `data/qr23.json` | Exact coordinates, induced edges, four-coloring |
| `data/qr23_proof_certificate.json` | Branch tree, assumptions, forcing witnesses, contradictions |
| `scripts/generate_graph.py` | Deterministic graph and proof generation |
| `scripts/verify_article.py` | Geometry, printed tables, proof steps, independent coloring search |
| `scripts/verify_dyadic16.py` | Dyadic color table, transfer, CNF encoding, weighted spectrum |
| `scripts/draw_figures.py` | Eight article panels, as PDF and PNG |
