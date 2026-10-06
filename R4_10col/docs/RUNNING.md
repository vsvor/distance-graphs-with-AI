# Construction, solving, and proof checks

## Preparation

```sh
make verify
make verify-legacy
make check-g65
```

The first command needs Python 3.10+ only. The last command also needs a C++17
compiler. External SAT solvers and proof checkers are not installed or bundled
by these commands.

Generated scratch outputs go in `build/`. The committed CNFs are reproducible:

```sh
python3 scripts/generate_cnf.py
git diff --exit-code -- cnf
```

Rebuild the graph in historical order:

```sh
python3 scripts/build_graph.py --out build/graphs
```

For a sorted alternative, with a mapping back to original IDs:

```sh
python3 scripts/build_graph.py --canonical-order --out build/canonical
```

Do not use original fixed vertex IDs with a canonically reindexed graph.

## One assignment case

With [Kissat](https://github.com/arminbiere/kissat) and
[DRAT-trim](https://github.com/marijnheule/drat-trim) installed, a typical run is:

```sh
mkdir -p runs/a0_b0
kissat --version > runs/a0_b0/solver-version.txt
kissat cnf/cases/G328_9_case_a0_b0.cnf runs/a0_b0/proof.drat > runs/a0_b0/solver.log
status=$?
printf '%s\n' "$status" > runs/a0_b0/solver-exit.txt
```

Kissat conventionally exits 10 for SAT, 20 for UNSAT, and 0 for UNKNOWN. Its
nonzero success status means that `solver && checker` is not the right shell
pattern. Run the following after an UNSAT report, using the exact input:

```sh
drat-trim cnf/cases/G328_9_case_a0_b0.cnf runs/a0_b0/proof.drat > runs/a0_b0/checker.log
sha256sum cnf/cases/G328_9_case_a0_b0.cnf runs/a0_b0/proof.drat > runs/a0_b0/SHA256SUMS
```

Inspect the checker's completed verification outcome. Save its version or source
commit too. This repository has not run those external commands on G328; use
the options supported by your installed versions.

The nine cases are independent jobs. Their runtimes need not be balanced.
All nine must be excluded unless a case is separately excluded by a checked
argument. No case is omitted on the strength of an old unchecked report.

## A SAT result

Check a solver's complete model, including all CNF variables:

```sh
python3 scripts/check_model.py data/candidate328.json 9 runs/a0_b0/solver.log \
  --cnf cnf/cases/G328_9_case_a0_b0.cnf --save runs/a0_b0/coloring.json
```

The checker requires DIMACS `v` lines, exactly one true color variable at every
vertex, a proper coloring on all edges, and satisfaction of every input clause.
It rejects missing or contradictory variable assignments. Output colors in the
saved JSON are numbered 1 through k.

## Historical light and full encodings

Use explicit input/output paths, because the preserved script's defaults refer
to its original archive layout:

```sh
python3 legacy/prepare.py --graph data/candidate328.json --colors 9 --mode light --out build/legacy
python3 legacy/prepare.py --graph data/candidate328.json --colors 9 --mode full --out build/legacy
```

`make verify-legacy` compares these encodings with the historical hashes and
checks the compressed original light input. There is no need to mix constraints
from these formulas into the simpler assignment-only CNFs.

To generate and check a positive control:

```sh
python3 legacy/prepare.py --graph data/candidate328.json --colors 10 --mode full --witness --out build/witness
python3 scripts/check_model.py data/candidate328.json 10 build/witness/candidate328_10_full.model \
  --cnf build/witness/candidate328_10_full.cnf
```

## Results records

Copy `results/experiment.template.json` into a new run directory and fill it
with actual measurements. Keep `reported_status` and `certificate_status`
separate. Record both wall time and CPU time when benchmarking parallel runs.
Large proofs and logs belong in release assets or other durable storage, with
their hashes in the repository; `runs/` is ignored by Git by default.
