# Evidence and verification scope

The status below is deliberately tied to specific files and checks.

| Statement | Evidence in this repository |
|---|---|
| G328 has 328 vertices and 5066 edges | Full exact reconstruction and all 53628 pair checks |
| Every edge is a unit distance after scaling | Exact coefficient arithmetic; scale 1/(4√2) |
| G65 is an induced subgraph | Seed-prefix and exact-edge checks |
| χ(G65)=9 | Included 9-coloring plus complete 8-color DSATUR run |
| χ(G328)≤10 | Included proper 10-coloring, checked edge by edge |
| Aut(G328)=S4 | 24 verified actions plus maximum-degree/refinement certificate |
| Nine cases cover all 9-colorings up to symmetry | Written proof plus exhaustive 501-assignment check |
| Case CNFs contain only graph clauses and assignment units | Independent complete clause-multiset comparison |
| Historical light/full CNFs are reproduced exactly | SHA-256 comparison with original values |
| Historical encoders pass positive controls | Complete CNF models for G65/9 colors and G328/10 colors |
| Historical light G328/9 instance was reported UNSAT | Project-owner report; no proof certificate included |
| New nine cases are all certified UNSAT | **Not established here** |

The G65 eight-color search completed with 1,095,823 recursive nodes in the
preparation run. `results/g65_8color.log` records its output. This is an
exhaustive algorithm computation, not a DRAT proof. Its source is short and
included; the stored output alone is not a substitute for rerunning/reviewing it.

## What the main verifier checks

`scripts/verify.py` reconstructs the vertex set from the ten seed orbits and
complete direction enumeration; checks the literal/corrected seed discrepancy;
checks all graph edges and nonedges; validates the supplied G65 nine-coloring
and G328 ten-coloring; checks the text edge lists; verifies the complete
automorphism-group certificate; checks root-case coverage; and compares every
CNF clause against the mathematical coloring encoding plus intended units.

The geometric verifier and the clause comparator do not import the CNF
generator. They do share the short construction module used for seed and
direction enumeration. The exact pair-distance check is written separately.

`scripts/verify_legacy.py` checks 819 small lex-comparison input pairs and 120
first-use input sequences by enumerating all auxiliary assignments. It rebuilds
the nine-color light and full instances byte for byte and checks all clauses in
four positive-control models, including 703,003 clauses in G328/10/full.

These tests support implementation correctness. The mathematical symmetry
argument in `SYMMETRY.md` explains why the encodings preserve colorability.

## What remains for a checked ten-chromatic result

One route is a checked UNSAT certificate for the clique-only baseline. Another
is checked UNSAT certificates for all nine assignment cases, combined with the
case-completeness argument. The historical light encoding offers a third route,
using its soundness argument and a certificate for that exact CNF.

Record solver and checker versions, command arguments, input/proof hashes, full
logs, and checker outcomes. A timeout, interrupted checker, or missing case is
not a completed proof. Since a ten-coloring is included, a successful complete
non-nine-colorability proof establishes χ(G328)=10 and hence χ(R⁴)≥10.


