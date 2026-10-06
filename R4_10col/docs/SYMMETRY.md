# Symmetry and the complete nine-case split

## Automorphisms

All 24 coordinate permutations preserve G328, since they preserve the seed,
the direction set, and the support condition. Every permutation is also checked
directly on the saved vertices and the complete edge set.

These are all graph automorphisms. The vertices `64,39,36,34`, representing
`p_i=4e_i`, are exactly the four vertices of maximum degree 77. Any automorphism
must permute them. Individualize them with four different labels, give all other
vertices a fifth label, and repeatedly refine each label by its multiset of
neighbor labels. The numbers of classes are

    5 -> 91 -> 320 -> 328.

An automorphism fixing those four vertices pointwise preserves every refinement
class and therefore fixes every vertex. Its pointwise stabilizer is trivial;
the restriction of Aut(G328) to the four vertices is injective into S4. The 24
verified coordinate maps give equality: Aut(G328)=S4. This certificate requires
no graph-isomorphism library.

## Anchor clique

Let `h=(1+√5)(1,1,1,1)`, vertex 51. The five points
`Q=(p_1,p_2,p_3,p_4,h)` form K5. Assign colors `(1,2,3,4,5)` to IDs
`(64,39,36,34,51)` without loss of generality by global color renaming.

Coordinate permutations move the four positive axes. They must be accompanied
by the corresponding permutation of colors 1 through 4 to retain the anchor.
Color 5 remains fixed. Colors 6 through 9 may be permuted independently.
The resulting action on anchored colorings has group order `24*24=576`.

This is an action on colorings, not an identification of vertices in the same
orbit. Requiring all vertices in an automorphism orbit to share a color would
be an invalid additional restriction in general.

## Four roots

The negative axes `r_i=-4e_i`, with IDs `(0,28,31,33)`, form K4.
Each `r_i` is adjacent to `p_j` exactly when `j!=i`, and is not adjacent to h.
Thus `color(r_i)` belongs to `{i,5,6,7,8,9}`, and all four root colors differ.

Let a count the roots using their corresponding positive-axis color i. Let b
indicate whether a root uses color 5. Then `0<=a<=4`, `b in {0,1}` and `a+b<=4`.
Permute coordinates to put the a matching roots first and the root colored 5
next when it exists. Compensate the positive-axis color labels. Finally relabel
the distinct free colors in root order as `6,7,...`.

The resulting pattern is `(1,...,a)`, followed by `5` if b=1, followed by
successive colors starting with 6. There are exactly nine possibilities:

| (a,b) | Root colors in order (0,28,31,33) | Orbit size |
|---|---|---:|
| (0,0) | (6,7,8,9) | 24 |
| (0,1) | (5,6,7,8) | 96 |
| (1,0) | (1,6,7,8) | 96 |
| (1,1) | (1,5,6,7) | 144 |
| (2,0) | (1,2,6,7) | 72 |
| (2,1) | (1,2,5,6) | 48 |
| (3,0) | (1,2,3,6) | 16 |
| (3,1) | (1,2,3,5) | 4 |
| (4,0) | (1,2,3,4) | 1 |

The orbit sizes sum to 501. The verifier independently enumerates every legal
root assignment and applies every compensated coordinate/free-color action to
each representative, checking exact coverage and disjointness.

Applying the symmetry to the **whole coloring** proves completeness: every
9-coloring maps into one of the nine cases. Conversely, a satisfying assignment
of any case is immediately a proper 9-coloring of the original graph.

## Main CNF encodings

Variables `x(v,c)=9*v+c` indicate colors c=1,...,9 on zero-based vertices v.
For each vertex include an at-least-one clause and all 36 negative binary
at-most-one clauses. For every edge and color include the negative binary
clause prohibiting that color on both endpoints.

This gives `328+328*36+5066*9=57730` graph clauses. The baseline adds five
positive unit clauses for Q. Each case adds four further positive unit clauses
for its roots, for 57,739 total. There are no other clauses or auxiliaries.

## Historical light and full encodings

The preserved `legacy/prepare.py` uses the same invariant clique and the order:
Q first, the four negative axes next, then remaining vertices in decreasing
degree, breaking ties by original ID. It adds nine root selectors with an
exactly-one condition, free-color first-use ordering, and lexicographic
comparisons with the 23 nonidentity compensated coordinate actions.

In **light** mode, comparisons use the compensated coloring directly. In
**full** mode, each transformed coloring first renames its free colors in
first-occurrence order. The latter needs additional permutation and indicator
variables. The counts for nine colors are:

| Encoding | Variables | Clauses |
|---|---:|---:|
| Clique only | 2952 | 57735 |
| One assignment-only case | 2952 | 57739 |
| Historical light | 11330 | 184888 |
| Historical full | 63563 | 514322 |

For soundness, take a lexicographically least anchored coloring in its entire
joint coordinate/free-color orbit. It satisfies first-use order. Its root
prefix has one of the nine canonical patterns, and it is no greater than every
compensated image, or every normalized image. Hence it extends to a model of
the light and full auxiliary circuits. Conversely, both retain all original
graph clauses. This proves existence of a model is preserved.

The repository checks the lex and first-use primitives exhaustively on small
inputs and validates complete generated models for two known positive inputs.
It also reproduces both historical nine-color CNFs byte for byte. These are
encoding checks, not an UNSAT certificate for G328. More symmetry breaking
does not itself guarantee faster solving.

The original plain CNF used another precolored clique, recorded in the original
graph JSON. Do not append these coordinate constraints to a formula with that
different anchor. The supplied generators use the invariant anchor explicitly.
