#!/usr/bin/env python3
"""Verified S4 symmetry breaking for the exact 328-point coloring instance.

Modes:
  anchor: invariant 5-clique only;
  color:  additionally first-use ordering of free colors;
  light:  additionally lex leaders for the 23 compensated coordinate actions;
  full:   normalize free colors AFTER every coordinate action, then compare.
Full mode with the complete vertex order retains exactly one coloring per joint
vertex/color orbit. Auxiliary permutation variables may still have symmetries
when some colors are unused. All vertex IDs in outputs remain original IDs.
Requires only Python 3.10+. --aut-check additionally requires NetworkX.
"""
from __future__ import annotations
import argparse
from collections import Counter
from itertools import permutations
from pathlib import Path
import hashlib
import json
import time
from typing import Union

Lit = Union[int, bool]
ROOT = Path(__file__).resolve().parent

def neg(x: Lit) -> Lit:
    return not x if isinstance(x, bool) else -x

class CNF:
    def __init__(self, witness: bool = False):
        self.nv = 0
        self.clauses: list[list[int]] = []
        self.values: list[bool] | None = [False] if witness else None

    def var(self, value: bool | None = None) -> int:
        self.nv += 1
        if self.values is not None:
            if value is None:
                raise ValueError('Every variable needs a value in witness mode')
            self.values.append(bool(value))
        return self.nv

    def val(self, x: Lit) -> bool:
        if isinstance(x, bool):
            return x
        if self.values is None:
            raise ValueError('No witness')
        return self.values[abs(x)] if x > 0 else not self.values[-x]

    def add(self, literals: list[Lit]) -> None:
        if any(x is True for x in literals):
            return
        clause = list(dict.fromkeys(x for x in literals if x is not False))
        if any(-x in clause for x in clause):
            return
        if self.values is not None and not any(self.val(x) for x in clause):
            raise AssertionError(f'Constructed witness violates clause {clause}')
        self.clauses.append(clause)

    def exactly_one(self, row: list[Lit]) -> None:
        self.add(row)
        for i, x in enumerate(row):
            for y in row[:i]:
                self.add([neg(x), neg(y)])

    def or_gate(self, a: Lit, b: Lit) -> Lit:
        if a is True or b is True:
            return True
        if a is False:
            return b
        if b is False or a == b:
            return a
        z = self.var(self.val(a) or self.val(b) if self.values is not None else None)
        self.add([neg(a), z])
        self.add([neg(b), z])
        self.add([neg(z), a, b])
        return z

    def write(self, path: Path, comments: list[str]) -> None:
        with path.open('w') as out:
            for comment in comments:
                out.write('c ' + comment + '\n')
            out.write(f'p cnf {self.nv} {len(self.clauses)}\n')
            for clause in self.clauses:
                out.write(' '.join(map(str, clause)) + ' 0\n')
        if self.values is not None:
            model = path.with_suffix('.model')
            with model.open('w') as out:
                out.write('s SATISFIABLE\nv ')
                out.write(' '.join(str(i if self.values[i] else -i)
                                   for i in range(1, self.nv + 1)))
                out.write(' 0\n')

def first_use(cnf: CNF, rows: list[list[Lit]], first: int = 5) -> None:
    """Color c+1 may occur only after color c has occurred; anchored colors ignored."""
    if not rows:
        return
    k = len(rows[0])
    seen: list[Lit] = [False] * max(0, k - first - 1)
    for pos, row in enumerate(rows):
        for j in range(len(seen)):
            cnf.add([neg(row[first + j + 1]), seen[j]])
            if pos + 1 < len(rows):
                seen[j] = cnf.or_gate(seen[j], row[first + j])

def lex_leq(cnf: CNF, xs: list[list[Lit]], ys: list[list[Lit]]) -> None:
    """Integer-color lex comparison of one-hot rows, using a forward prefix chain.

    A true prefix forces X <= Y at that position and propagates to the next
    position whenever colors agree. If they differ in the allowed direction,
    later prefix variables may be false. This is an existentially exact CNF.
    Syntactically identical rows can be skipped without changing the comparison.
    """
    pairs = [(a, b) for a, b in zip(xs, ys) if a != b]
    prefix: Lit = True
    for pos, (a, b) in enumerate(pairs):
        k = len(a)
        for c in range(1, k):
            cnf.add([neg(prefix), neg(a[c])] + b[c:])
        if pos + 1 < len(pairs):
            value = None
            if cnf.values is not None:
                equal = all(cnf.val(u) == cnf.val(v) for u, v in zip(a, b))
                value = cnf.val(prefix) and equal
            nxt = cnf.var(value)
            for u, v in zip(a, b):
                cnf.add([neg(prefix), neg(u), neg(v), nxt])
            prefix = nxt

def graph_data(path: Path):
    data = json.loads(path.read_text())
    vertices = [tuple(v) for v in data['vertices']]
    if len(set(vertices)) != len(vertices) or any(len(v) != 8 for v in vertices):
        raise ValueError('Expected distinct points with eight integral coefficients')
    if any(not isinstance(x, int) for v in vertices for x in v):
        raise ValueError('Coordinates must be integral coefficient pairs')
    n = len(vertices)
    edges = {tuple(sorted(e)) for e in data['edges']}
    if len(edges) != len(data['edges']):
        raise ValueError('Duplicate edges')
    adj = [set() for _ in vertices]
    for u, v in edges:
        if not (0 <= u < v < n):
            raise ValueError('Invalid edge')
        adj[u].add(v)
        adj[v].add(u)
    # Independently recompute every edge, including nonedges, exactly.
    actual = set()
    for i, v in enumerate(vertices):
        for j in range(i):
            t = [x-y for x,y in zip(v, vertices[j])]
            A = sum(t[z]**2 + 5*t[z+1]**2 for z in range(0,8,2))
            B = sum(t[z]*t[z+1] for z in range(0,8,2))
            if A == 32 and B == 0:
                actual.add((j,i))
    if actual != edges:
        raise ValueError('Saved graph differs from the exact distance graph')
    lookup = {v: i for i, v in enumerate(vertices)}
    positive, negative = [], []
    for j in range(4):
        v = [0]*8
        v[2*j] = 4
        positive.append(lookup[tuple(v)])
        v[2*j] = -4
        negative.append(lookup[tuple(v)])
    h = lookup[(1,1)*4]
    clique = positive + [h]
    if any(v not in adj[u] for i,u in enumerate(clique) for v in clique[:i]):
        raise ValueError('The required invariant 5-clique is absent')
    if any(v not in adj[u] for i,u in enumerate(negative) for v in negative[:i]):
        raise ValueError('Negative axis vertices must form a clique')
    if any(positive[j] not in adj[negative[i]] for i in range(4)
           for j in range(4) if i != j):
        raise ValueError('Missing cross-axis edge')
    group = []
    coordinate_actions = []
    for p in permutations(range(4)):
        images = [tuple(v[2*j+t] for j in p for t in range(2)) for v in vertices]
        if any(v not in lookup for v in images):
            raise ValueError('Graph is not closed under S4 coordinate permutations')
        action = [lookup[v] for v in images]
        if {tuple(sorted((action[u],action[v]))) for u,v in edges} != edges:
            raise ValueError('A claimed coordinate action is not an automorphism')
        group.append(action)
        coordinate_actions.append(list(p))
    if len({tuple(g) for g in group}) != 24:
        raise ValueError('The S4 action is not faithful')
    marked = set(); orbits = []
    for v in range(n):
        if v not in marked:
            orbit = sorted({g[v] for g in group})
            marked.update(orbit)
            orbits.append(orbit)
    order = clique + negative
    order += sorted(set(range(n))-set(order), key=lambda v:(-len(adj[v]),v))
    return data, vertices, edges, adj, clique, negative, group, coordinate_actions, orbits, order

def normalize_free(colors: list[int], order: list[int], k: int):
    mapping = {}
    for v in order:
        c = colors[v]
        if c >= 5 and c not in mapping:
            mapping[c] = 5 + len(mapping)
    for c in range(5, k):
        if c not in mapping:
            mapping[c] = 5 + len(mapping)
    return [mapping.get(c,c) for c in colors], mapping

def anchor_coloring(colors: list[int], clique: list[int], k: int) -> list[int]:
    mapping = {colors[v]: i for i, v in enumerate(clique)}
    if len(mapping) != 5:
        raise ValueError('Input coloring is not proper on the anchor clique')
    for c in colors:
        if c not in mapping:
            mapping[c] = len(mapping)
    if len(mapping)>k:
        raise ValueError('Input coloring uses too many colors')
    return [mapping[c] for c in colors]

def compensated_action(colors: list[int], g: list[int], clique: list[int]) -> list[int]:
    perm = [clique.index(g[v]) for v in clique]
    inverse = [perm.index(c) for c in range(5)]
    return [inverse[colors[g[v]]] if colors[g[v]]<5 else colors[g[v]]
            for v in range(len(colors))]

def canonical_coloring(colors, group, clique, order, k):
    colors = anchor_coloring(colors, clique, k)
    images = [normalize_free(compensated_action(colors,g,clique),order,k)[0]
              for g in group]
    return min(images, key=lambda c:tuple(c[v] for v in order))

def encode(data, edges, clique, negative, group, order, k, mode, roots, prefix,
           coloring=None):
    n = len(data['vertices'])
    if k < 5:
        raise ValueError('This encoder requires at least five colors')
    if coloring is not None:
        if len(coloring)!=n or any(coloring[u]==coloring[v] for u,v in edges):
            raise ValueError('Input witness is not a proper coloring')
        coloring=canonical_coloring(coloring,group,clique,order,k)
    cnf = CNF(coloring is not None)
    X = [[cnf.var(coloring[v]==c if coloring is not None else None)
          for c in range(k)] for v in range(n)]
    for row in X:
        cnf.exactly_one(row)
    for u,v in sorted(edges):
        for c in range(k):
            cnf.add([-X[u][c],-X[v][c]])
    for c,v in enumerate(clique):
        cnf.add([X[v][c]])
    rows = [[c==clique.index(v) for c in range(k)] if v in clique else X[v]
            for v in range(n)]
    cases=[]
    if roots:
        for a in range(5):
            for b in (0,1):
                r=4-a-b
                if r<0 or r>k-5:
                    continue
                pattern=list(range(a))+([4] if b else [])+list(range(5,5+r))
                match=(all(coloring[v]==c for v,c in zip(negative,pattern))
                       if coloring is not None else None)
                selector=cnf.var(match)
                for v,c in zip(negative,pattern):
                    cnf.add([-selector,X[v][c]])
                cases.append(dict(a=a,b=b,pattern=pattern,selector=selector))
        cnf.exactly_one([c['selector'] for c in cases])
    if mode in ('color','light','full'):
        first_use(cnf,[rows[v] for v in order])
    identity=list(range(n))
    compared=order if not prefix else order[:prefix]
    transformations=0
    if mode in ('light','full'):
        for g in group:
            if g==identity:
                continue
            transformations+=1
            perm=[clique.index(g[v]) for v in clique]
            Y=[]
            if mode=='light':
                for v in range(n):
                    Y.append([rows[g[v]][perm[c] if c<5 else c] for c in range(k)])
            else:
                transformed=None; mapping=None
                if coloring is not None:
                    transformed=compensated_action(coloring,g,clique)
                    transformed,mapping=normalize_free(transformed,order,k)
                f=k-5
                # R[new][old] is a permutation of the free color names.
                R=[[cnf.var(mapping[o+5]==d+5 if mapping is not None else None)
                    for o in range(f)] for d in range(f)]
                for row in R:
                    cnf.exactly_one(row)
                for o in range(f):
                    cnf.exactly_one([R[d][o] for d in range(f)])
                for v in range(n):
                    if v in clique:
                        Y.append(rows[v])
                        continue
                    row=[rows[g[v]][perm[c]] for c in range(5)]
                    row += [cnf.var(transformed[v]==c if transformed is not None else None)
                            for c in range(5,k)]
                    Y.append(row)
                    for d in range(f):
                        for o in range(f):
                            r=R[d][o]; x=rows[g[v]][5+o]; y=row[5+d]
                            cnf.add([-r,neg(x),y])
                            cnf.add([-r,x,neg(y)])
                first_use(cnf,[Y[v] for v in order])
            lex_leq(cnf,[rows[v] for v in compared],[Y[v] for v in compared])
    return cnf,cases,transformations,coloring

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph',type=Path,default=ROOT/'graphs/candidate328.json')
    parser.add_argument('--out',type=Path,default=ROOT/'cnf')
    parser.add_argument('--colors',type=int,default=9)
    parser.add_argument('--mode',choices=('anchor','color','light','full'),default='full')
    parser.add_argument('--prefix',type=int,default=0,help='0: complete order; positive: prefix only (partial breaking)')
    parser.add_argument('--no-root-cases',action='store_true')
    parser.add_argument('--aut-check',action='store_true',help='Independently enumerate all automorphisms with NetworkX')
    parser.add_argument('--witness',action='store_true',help='Normalize the saved coloring and check every generated clause')
    args=parser.parse_args()
    if args.prefix<0:
        parser.error('prefix must be nonnegative')
    args.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    data,V,E,adj,Q,N,group,coord,orbits,order=graph_data(args.graph)
    aut_order=None
    if args.aut_check:
        import networkx as nx
        G=nx.Graph();G.add_nodes_from(range(len(V)));G.add_edges_from(E)
        for v in G:
            G.nodes[v]['invariant']=(len(adj[v]),tuple(sorted(len(adj[u]) for u in adj[v])))
        matcher=nx.algorithms.isomorphism.GraphMatcher(
            G,G,node_match=lambda a,b:a['invariant']==b['invariant'])
        autos={tuple(m[v] for v in range(len(V))) for m in matcher.isomorphisms_iter()}
        if autos!={tuple(g) for g in group}:
            raise AssertionError('Full automorphism group differs from coordinate S4')
        aut_order=len(autos)
    cnf,cases,ng,witness=encode(data,E,Q,N,group,order,args.colors,args.mode,
                              not args.no_root_cases,args.prefix,
                              data['verified_coloring'] if args.witness else None)
    suffix=f'_prefix{args.prefix}' if args.prefix else ''
    if args.no_root_cases:suffix+='_noroot'
    name=f'candidate{len(V)}_{args.colors}_{args.mode}{suffix}'
    path=args.out/(name+'.cnf')
    cnf.write(path,[f'{len(V)} vertices; {len(E)} edges; k={args.colors}; mode={args.mode}',
                    'Original zero-based vertex IDs; color variable = k*v+c+1.',
                    'Full mode uses compensated coordinate actions followed by free-color normalization.',
                    'Do not combine with a different precolored clique or unrelated symmetry breakers.'])
    report=dict(graph=args.graph.name,vertices=len(V),edges=len(E),colors=args.colors,
                mode=args.mode,full_automorphism_order=aut_order,
                verified_coordinate_group_order=len(group),coordinate_actions=coord,
                vertex_permutations=group,vertex_orbits=orbits,
                orbit_size_histogram=dict(sorted(Counter(map(len,orbits)).items())),
                anchor_clique=Q,negative_axes=N,vertex_order=order,
                canonical_root_cases=cases,lex_comparisons=ng,lex_prefix=len(order) if not args.prefix else min(args.prefix,len(order)),
                variables=cnf.nv,clauses=len(cnf.clauses),cnf_filename=path.name,
                cnf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                every_clause_checked_on_witness=witness is not None,
                elapsed_seconds=time.monotonic()-start)
    path.with_suffix('.meta.json').write_text(json.dumps(report,indent=2)+'\n')
    if witness is not None:
        path.with_suffix('.coloring.json').write_text(json.dumps(witness)+'\n')
    print(json.dumps({key:report[key] for key in ('vertices','edges','colors','mode',
          'full_automorphism_order','orbit_size_histogram','anchor_clique','variables',
          'clauses','every_clause_checked_on_witness','elapsed_seconds')},indent=2))
    print(path)

if __name__=='__main__':
    main()
