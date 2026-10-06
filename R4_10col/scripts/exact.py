"""Exact Q(sqrt(5)) coordinates for forbidden squared distance 32.
Each point is (a0,b0,a1,b1,a2,b2,a3,b3), denoting ai+bi*sqrt(5).
No floating-point arithmetic is used.
"""
from itertools import permutations, product
from pathlib import Path
import json

SEEDS = [
    (1,1,1,1,1,1,1,1),
    (-4,0,0,0,0,0,0,0),
    (4,0,0,0,0,0,0,0),
    (0,2,-2,0,-2,0,-2,0),
    (1,-1,-1,1,-1,1,-1,1),  # corrected first entry, 1-sqrt(5)
    (-1,-1,-1,-1,1,1,1,1),
    (1,1,1,1,-3,1,-3,1),
    (-2,0,2,0,2,0,0,2),
    (0,0,-2,2,2,2,0,0),
    (-1,1,-3,-1,-1,1,3,1),
]

def norm2(v):
    """Return (A,B) for squared norm A+B*sqrt(5)."""
    return (sum(v[i]**2+5*v[i+1]**2 for i in range(0,8,2)),
            2*sum(v[i]*v[i+1] for i in range(0,8,2)))

def subtract(u,v):
    return tuple(x-y for x,y in zip(u,v))

def edges(vertices):
    return [(i,j) for i,u in enumerate(vertices) for j in range(i)
            if norm2(subtract(u,vertices[j])) == (32,0)]

def color9(v):
    """A proper coloring on M only, not on the full coefficient ring."""
    s=[(v[2*i]+v[2*i+1])%3 for i in range(4)]
    return 3*((s[1]+s[2]+s[3])%3)+(s[0]+s[2]-s[3])%3

def in_module(v):
    return len({v[i]%2 for i in range(1,8,2)}) == 1

def orbit(v,signed=False):
    coords=[v[i:i+2] for i in range(0,8,2)]
    out=set()
    for p in set(permutations(coords)):
        for signs in product((-1,1),repeat=4) if signed else [(1,)*4]:
            out.add(tuple(t*s for pair,s in zip(p,signs) for t in pair))
    return out

def published_vertices(literal=False,signed=False):
    seeds=SEEDS.copy()
    if literal:
        seeds[4]=(1,1,-1,1,-1,1,-1,1)
    return sorted(set().union(*(orbit(v,signed) for v in seeds)))

def directions():
    """All 2008 length-squared-32 vectors in Z[sqrt(5)]^4."""
    pairs=[(a,b,a*a+5*b*b,a*b) for a in range(-5,6) for b in range(-2,3)
           if a*a+5*b*b<=32]
    ans=[]
    def rec(coords,used,dot):
        if len(coords)==8:
            if used==32 and dot==0: ans.append(tuple(coords))
            return
        for a,b,q,t in pairs:
            if used+q<=32: rec(coords+[a,b],used+q,dot+t)
    rec([],0,0)
    return sorted(ans)

def write_graph(path,V,E):
    with Path(path).open('w') as f:
        f.write(f'{len(V)} {len(E)}\n')
        for i,j in E: f.write(f'{i} {j}\n')

def maximal_independent_sets(n,E):
    """Bron--Kerbosch enumeration on the complement graph, with pivoting."""
    full=(1<<n)-1
    adj=[full^(1<<i) for i in range(n)]
    for i,j in E:
        adj[i]&=~(1<<j);adj[j]&=~(1<<i)
    def bits(x):
        while x:
            b=x&-x;x-=b;yield b.bit_length()-1
    def visit(R,P,X):
        if not (P|X):
            yield list(bits(R));return
        u=max(bits(P|X),key=lambda u:(P&adj[u]).bit_count())
        todo=P&~adj[u]
        for v in bits(todo):
            b=1<<v
            yield from visit(R|b,P&adj[v],X&adj[v])
            P&=~b;X|=b
    yield from visit(0,full,0)
