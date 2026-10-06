# Construction and relation to Exoo–Ismailescu–Lim

## Source and explicit correction

The reference is Exoo, Ismailescu and Lim, *On the Chromatic Number of R⁴*,
Discrete & Computational Geometry 52 (2014), 416–423,
[DOI](https://doi.org/10.1007/s00454-014-9612-7).
Section 5 uses S4 coordinate orbits and forbidden distance 4√2.

In the inspected published Table 2 (p. 422), the fifth seed starts with
`1+sqrt(5)`. This repository instead uses `1-sqrt(5)`, which agrees with the
corresponding row of Table 1 (p. 421). This is an explicit reconstruction
correction; no author-confirmed erratum or comparison with the authors' original
adjacency file is claimed. The historical authors' data URL could not be
retrieved during this preparation.

Our exact computation from the literal Table 2 yields 65 vertices, 472 edges,
and four isolated vertices. The corrected version yields 65 vertices and 588
edges, matching the paper's stated size. The included 9-coloring and rerunnable
complete 8-color search establish the corrected graph's chromatic number
independently of this identification.

## Ten corrected seed orbits

Put s=√5. Take every distinct coordinate permutation of each row below and
form their union. The orbit sizes sum to 65.

| Row | Seed | Orbit size |
|---:|---|---:|
| 1 | (1+s, 1+s, 1+s, 1+s) | 1 |
| 2 | (-4, 0, 0, 0) | 4 |
| 3 | (4, 0, 0, 0) | 4 |
| 4 | (2s, -2, -2, -2) | 4 |
| 5 | (1-s, -1+s, -1+s, -1+s) | 4 |
| 6 | (-1-s, -1-s, 1+s, 1+s) | 6 |
| 7 | (1+s, 1+s, -3+s, -3+s) | 6 |
| 8 | (-2, 2, 2, 2s) | 12 |
| 9 | (0, -2+2s, 2+2s, 0) | 12 |
| 10 | (-1+s, -3-s, -1+s, 3+s) | 12 |

The source code stores a point as eight integers `[a0,b0,...,a3,b3]`, denoting
the four coordinates `ai+bi*sqrt(5)`. Coefficients have no implicit denominator.

For a coordinate difference `(a_i+b_i√5)_i`,

\[
\|a+b\sqrt5\|^2=\sum_i(a_i^2+5b_i^2)+2\sqrt5\sum_i a_i b_i.
\]

It equals 32 exactly when the rational coefficient is 32 and the irrational
coefficient is zero. No numeric tolerance is involved.

## From 65 to 328 vertices

Enumerate

\[
D=\{a+b\sqrt5\in\mathbb Z[\sqrt5]^4:
\sum_i(a_i^2+5b_i^2)=32,\quad \sum_i a_i b_i=0\}.
\]

Every summand is nonnegative, so `|ai|<=5` and `|bi|<=2` suffice for exhaustive
enumeration. The recursion in `scripts/exact.py` visits every allowed coordinate
tuple and retains exactly 2,008 vectors.

For `x` in `V65+D`, count its distinct distance-4√2 neighbors in `V65`. Counting
the pairs `(v,d)` with `x=v+d` counts those neighbors exactly: for fixed `v,x`,
the difference `d` is unique. Retain all original vertices and every candidate
with count at least eight:

\[
V_{328}=V_{65}\cup\{x\in V_{65}+D:
|\{v\in V_{65}:\|x-v\|^2=32\}|\ge8\}.
\]

This gives 328 distinct points and 5,066 edges. The 65-vertex graph is an
induced subgraph, because both graphs include every pair at squared distance 32.
The vertex support rule and all edge decisions are verified by the scripts.
The support-eight extension is a construction of this project, not a statement
of the 2014 paper.

## Why the extension leaves the old additive module

Let M be the set of points `a+b√5` for which the four integer coefficients
`b_i` have a common parity. The seed lies in M. There is a proper nine-coloring
of the entire distance-4√2 graph on M: put `s_i=a_i+b_i (mod 3)` and use

\[
(s_1+s_2+s_3,\ s_0+s_2-s_3)\in\mathbb F_3^2.
\]

For an edge difference in M, common parity and `sum(b_i^2)<=6` imply
`sum(b_i^2)` is 0 or 4. Also `sum(a_i*b_i)=0`. Therefore

\[
\sum_i s_i^2\equiv32-4\sum_i b_i^2\in\{1,2\}\pmod3.
\]

A vector in the kernel of the displayed color map has the form
`(v-u,-u-v,u,v)`, whose squared-coordinate sum is `3u^2+3v^2`, hence zero
modulo 3. An edge difference cannot lie in that kernel. This proves properness.

Thus extensions contained in M cannot need ten colors at this distance.
Only 216 of the 2,008 directions lie in M, and G328 has 152 vertices outside M.
For example `(1+√5,-1+√5,2,4)` is a squared-length-32 direction outside M
that the displayed formula assigns the same color as zero. This explains why
the old formula fails on the full coefficient ring; it does not prove G328
non-9-colorable.

## Vertex order

The first 65 historical IDs are the lexicographically sorted seed. The remaining
IDs follow the saved original construction order, not a global sort. The builder
reconstructs the entire set independently and only then uses the saved ordering
to assign historical IDs. It rejects any membership difference.

`--canonical-order` produces a fully sorted copy plus `original_vertex_ids.json`,
mapping each new ID to its original ID. The supplied CNFs always refer to the
historical order.
