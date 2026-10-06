from collections import Counter
from itertools import permutations, product
from prepare import CNF, first_use, lex_leq

def require(condition,message):
    if not condition:raise AssertionError(message)

def refinement(adj,positive):
    colors=[4]*len(adj)
    for i,v in enumerate(positive):colors[v]=i
    counts=[len(set(colors))]
    while True:
        signatures=[(colors[v],tuple(sorted(Counter(colors[u] for u in adj[v]).items())))
                    for v in range(len(adj))]
        ids={s:i for i,s in enumerate(sorted(set(signatures)))}
        new=[ids[s] for s in signatures]
        if len(ids)==len(set(colors)):
            return counts,colors
        counts.append(len(ids));colors=new

def canonical_root(row):
    images=[]
    for p in permutations(range(4)):
        inverse=[p.index(i) for i in range(4)]
        raw=[inverse[row[p[i]]] if row[p[i]]<4 else row[p[i]] for i in range(4)]
        ren={};image=[]
        for c in raw:
            if c>=5:
                if c not in ren:ren[c]=5+len(ren)
                c=ren[c]
            image.append(c)
        images.append(tuple(image))
    return min(images)

def satisfies(clauses,assignment):
    return all(any(assignment[abs(x)]==(x>0) for x in clause) for clause in clauses)

def primitive_tests():
    # Exhaustively existentially quantify every prefix variable, not just the
    # particular intended auxiliary assignment. This checks both directions.
    comparisons=0
    for length in range(1,4):
        k=3;cnf=CNF()
        X=[[cnf.var() for _ in range(k)] for _ in range(length)]
        Y=[[cnf.var() for _ in range(k)] for _ in range(length)]
        first_aux=cnf.nv+1
        lex_leq(cnf,X,Y)
        for xs in product(range(k),repeat=length):
            for ys in product(range(k),repeat=length):
                A={X[v][c]:xs[v]==c for v in range(length) for c in range(k)}
                A.update({Y[v][c]:ys[v]==c for v in range(length) for c in range(k)})
                possible=False
                for bits in product((False,True),repeat=cnf.nv-first_aux+1):
                    A.update({first_aux+i:value for i,value in enumerate(bits)})
                    if satisfies(cnf.clauses,A):possible=True;break
                require(possible==(xs<=ys),'Lex-leader encoding is not equivalent')
                comparisons+=1
    precedence_tests=0
    for length in range(1,5):
        k=3;cnf=CNF();X=[[cnf.var() for _ in range(k)] for _ in range(length)]
        first_aux=cnf.nv+1;first_use(cnf,X,first=0)
        for xs in product(range(k),repeat=length):
            A={X[v][c]:xs[v]==c for v in range(length) for c in range(k)}
            expected=all(c<=1+max(xs[:i],default=-1) for i,c in enumerate(xs))
            possible=False
            for bits in product((False,True),repeat=cnf.nv-first_aux+1):
                A.update({first_aux+i:value for i,value in enumerate(bits)})
                if satisfies(cnf.clauses,A):possible=True;break
            require(possible==expected,'First-use encoding is not equivalent')
            precedence_tests+=1
    return comparisons,precedence_tests

