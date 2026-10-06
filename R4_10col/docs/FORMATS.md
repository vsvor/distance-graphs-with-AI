# Formats and indexing

`data/candidate328.json` and `data/eil65_corrected.json` preserve the original
graph JSON bytes. Vertices are indexed by their position in `vertices`, starting
at zero. Each is an eight-integer list representing four coordinates
`ai+bi*sqrt(5)`. Edges are pairs of zero-based vertex IDs. The squared forbidden
distance is 32, and the unit-distance scale is `1/(4*sqrt(2))`.

The original `verified_coloring` arrays use their historical labels (0-based).
Only equality of labels matters when checking edges. The new CNF documentation
and case assignments use colors 1 through 9, with variable `9*v+c`.

The `precolored_clique` field of the original G328 JSON belongs to its older
plain CNF. The main generator explicitly uses `[64,39,36,34,51]` instead, which
is the historical light encoding's invariant clique.

The `.txt` graph format starts with `n m`, followed by exactly m lines `u v` of
zero-based endpoints. It is an edge-list format, not a KaMIS/METIS adjacency
format, and is the input to `scripts/color.cpp`.

`cnf/manifest.json` records every file's SHA-256, DIMACS counts, and fixed
assignments. CNF paths are relative to `cnf/`; the graph path is relative to the
repository root. `scripts/generate_cnf.py --out DIRECTORY` writes the same
CNFs and manifest to another directory; its source graph remains the repository
data file.

The graph builder's `original_vertex_ids.json` maps output vertex IDs to the
historical IDs, including when `--canonical-order` is used. Rebuilt graph JSON
contains geometry but does not copy the source's coloring or precolored-clique
metadata. This prevents an old coloring from being silently applied to new IDs.
