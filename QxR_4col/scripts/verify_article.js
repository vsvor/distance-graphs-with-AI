// Exact, dependency-free checks for the local article and its certificates.
// Usage: node scripts/verify_article.js [article.tex]
const fs = require('fs');
const assert = require('assert');
const path = require('path');
const repoRoot = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.resolve(repoRoot, name), 'utf8');
const mod = (a, p) => ((a % p) + p) % p;
const key = (a, b) => `${a},${b}`;
const articleFile = process.argv[2] || 'article.tex';

function finiteColorings(file) {
  const tex = read(file);
  const targetBlock = tex.split('% BEGIN TARGET PARAMETERS')[1].split('% END TARGET PARAMETERS')[0];
  const targets = targetBlock.trim().split('\n').map(line =>
    line.split('&').map(cell => {
      const value = cell.replace(/[$\\\s]/g, '');
      return value.startsWith('(') ? value.slice(1, -1).split(',').map(Number) : Number(value);
    }));
  assert.deepStrictEqual(targets, [
    [3,2,[1,0],[1,0],[0,0],3], [5,2,[1,0],[1,0],[0,0],5],
    [7,3,[3,0],[2,0],[0,0],4], [11,2,[2,0],[2,0],[0,0],6],
    [13,2,[1,0],[0,1],[2,2],6], [17,3,[6,0],[3,0],[0,0],6],
    [19,2,[1,0],[7,0],[0,1],6]
  ], 'Printed target parameters differ from the verified parameters');
  for (const p of [13, 19]) {
    const block = tex.split(`% BEGIN C${p} TABLE`)[1].split(`% END C${p} TABLE`)[0];
    const rows = block.split('\n').filter(s => /^\d+ &/.test(s)).map(s =>
      s.split('&').map(v => Number(v.replace(/\\/g, '').trim())));
    assert.strictEqual(rows.length, p);
    const C = rows.map((r, y) => {
      assert.strictEqual(r[0], y);
      assert.strictEqual(r.length, p + 1);
      assert(r.slice(1).every(c => Number.isInteger(c) && c >= 0 && c < 6));
      return r.slice(1);
    });
    const first = new Set(), second = new Set();
    for (let a = 0; a < p; a++) for (let b = 0; b < p; b++) {
      if (mod(a*a + b*b, p) === 1)
        first.add(p === 13 ? key(a, b) : key(mod(a + 7*b, p), 0));
      if (p === 13 ? mod((a-b)**2 + 7*b*b, p) === 1 : mod(a*a + 2*b*b, p) === 1)
        second.add(key(a, b));
    }
    const T = new Set([...first, ...second]);
    const [,nu,h,u,w] = targets.find(row => row[0] === p);
    const printedTarget = new Set();
    for (let a=0;a<p;a++) for (let b=0;b<p;b++) {
      if (mod(a*a+b*b,p)===1)
        printedTarget.add(key(mod(a*h[0]+b*u[0],p),mod(a*h[1]+b*u[1],p)));
      if (mod(a*a+nu*b*b,p)===1)
        printedTarget.add(key(mod(a*h[0]+b*w[0],p),mod(a*h[1]+b*w[1],p)));
    }
    assert.deepStrictEqual([...printedTarget].sort(), [...T].sort());
    assert(!T.has('0,0'));
    assert.strictEqual(T.size, p === 13 ? 22 : 26);
    if (p === 13) {
      assert.strictEqual(first.size, 12);
      assert.strictEqual(second.size, 14);
      assert.deepStrictEqual([...first].filter(v => second.has(v)).sort(),
        ['1,0', '12,0', '7,2', '6,11'].sort());
    } else {
      const explicit = new Set([1,5,7,8,9].flatMap(a => [key(a,0),key(p-a,0)]));
      assert.deepStrictEqual([...first].sort(), [...explicit].sort());
      for (const [a,b] of [[8,4],[9,6],[6,7],[5,8]])
        for (const s of [-1,1]) for (const t of [-1,1]) explicit.add(key(mod(s*a,p),mod(t*b,p)));
      assert.deepStrictEqual([...T].sort(), [...explicit].sort());
    }
    let checks = 0;
    for (const z of T) {
      const [a,b] = z.split(',').map(Number);
      assert(T.has(key(mod(-a,p),mod(-b,p))));
      for (let y=0;y<p;y++) for (let x=0;x<p;x++) {
        assert.notStrictEqual(C[y][x],C[mod(y+b,p)][mod(x+a,p)],`${file}: p=${p}, (${x},${y}) + (${a},${b})`);
        checks++;
      }
    }
    const sizes = Array(6).fill(0);
    C.forEach(row => row.forEach(c => sizes[c]++));
    assert.deepStrictEqual(sizes,p===13?[30,29,25,28,28,29]:[65,60,65,65,64,42]);
    console.log(`${file}: p=${p}, ${checks} directed comparisons pass; classes ${sizes}.`);
  }
  const params = tex.split('% BEGIN SCALAR PARAMETERS')[1].split('% END SCALAR PARAMETERS')[0]
    .trim().split('\n').map(row => row.split('&').map(s => Number(s.replace(/[$\\]/g,'').trim())));
  assert.deepStrictEqual(params.map(row => row[0]), [3,5,7,11,17]);
  for (const [p,nu,t,r,g,count] of params) {
    assert.deepStrictEqual(targets.find(row => row[0]===p), [p,nu,[t,0],[r,0],[0,0],count]);
    assert.strictEqual(count,Math.ceil(p/g));
    const squares=new Set(Array.from({length:p-1},(_,i)=>mod((i+1)**2,p)));
    assert(!squares.has(nu));
    for(let j=0;j<g;j++) {
      assert(squares.has(mod(t*t-j*j,p)));
      assert(!squares.has(mod(t*t+r*r-j*j,p)) && mod(t*t+r*r-j*j,p)!==0);
    }
    const increments=new Set();
    for(let a=0;a<p;a++)for(let b=0;b<p;b++) {
      if(mod(a*a+b*b,p)===1)increments.add(mod(t*a+r*b,p));
      if(mod(a*a+nu*b*b,p)===1)increments.add(mod(t*a,p));
    }
    assert(!increments.has(0));
    for(const z of increments)for(let x=0;x<p;x++)
      assert.notStrictEqual(Math.floor(x/g),Math.floor(mod(x+z,p)/g));
    console.log(`${file}: scalar p=${p}, ${count} colors, all increments verified.`);
  }
}

finiteColorings(articleFile);
assert.strictEqual([16,3,5,7,11,13,17,19].reduce((a,b)=>a*b),77597520);

// Exhaust all residue classes needed by the dyadic argument. For square-free
// M, divisibility by 4 is impossible. D^2 is 1 mod 2, 4 mod 16, or 16 mod 64.
for(const [s,m,target] of [[0,2,1],[1,16,4],[2,64,16]]) {
  let checks=0;
  for(let M=0;M<m;M++) {
    if(s>0 && M%4===0)continue;
    for(let a=0;a<m;a++)for(let b=0;b<m;b++) {
      if(mod(a*a+M*b*b,m)!==target)continue;
      if(s===0) assert.strictEqual(mod(a+M*b,2),1);
      if(s===1) assert.notStrictEqual(mod(a+(M%4===3?0:M%2)*b,4),0);
      if(s===2) {
        const k=M%4!==3?M%2:M%8===3?0:M%16===7?1:3;
        assert([2,4,6].includes(mod(a+k*b,8)));
      }
      checks++;
    }
  }
  console.log(`Dyadic s=${s}: all ${checks} admissible residue triples pass.`);
}

const graph=JSON.parse(read('data/qr23.json'));
const {vertices,radicands,denominator}=graph;
const gcd=(a,b)=>b?gcd(b,a%b):a;
const edges=[];
assert.deepStrictEqual(radicands, [2,3,5,35]);
assert.strictEqual(denominator, 6);
assert.strictEqual(vertices.length,23);
assert(vertices.every(v => v.length === 5 && v.every(Number.isSafeInteger)));
assert.strictEqual(graph.colors_0_to_3.length, 23);
assert(graph.colors_0_to_3.every(c => Number.isInteger(c) && c >= 0 && c < 4));
assert.strictEqual(new Set(vertices.map(v=>v.join(','))).size,23);
for(let i=0;i<vertices.length;i++)for(let j=i+1;j<vertices.length;j++) {
  const d=vertices[i].map((v,k)=>v-vertices[j][k]);
  const squared=new Map([[1,d[0]*d[0]]]);
  for(let k=0;k<radicands.length;k++)for(let l=0;l<radicands.length;l++) {
    const g=gcd(radicands[k],radicands[l]);
    const sf=radicands[k]*radicands[l]/(g*g);
    squared.set(sf,(squared.get(sf)||0)+d[k+1]*d[l+1]*g);
  }
  if(squared.get(1)===denominator**2 && [...squared].every(([r,c])=>r===1||c===0))edges.push([i+1,j+1]);
}
assert.strictEqual(edges.length,45);
assert.deepStrictEqual(edges,graph.edges_1based);
for(const [a,b] of edges)assert.notStrictEqual(graph.colors_0_to_3[a-1],graph.colors_0_to_3[b-1]);
console.log('Exact radical arithmetic: 23 distinct vertices, 45 edges, proper four-coloring.');

// Relabel as in the figure and article; independently check the printed proof.
const newToOld=[12,13,14,15,23,16,1,2,3,4,5,6,7,17,18,19,21,22,8,9,10,11,20];
const oldToNew=new Map(newToOld.map((old,i)=>[old,i+1]));
const fixedEdges=edges.map(([a,b])=>[oldToNew.get(a),oldToNew.get(b)]);
const adjacent=(a,b)=>fixedEdges.some(([u,v])=>(a===u&&b===v)||(a===v&&b===u));
const tex=read(articleFile);
// Parse the actual parameter definitions and coordinate table, including signs.
const radicalParameters = new Map();
const construction = tex.split('\\section{A 4-chromatic')[1].split('\\begin{proposition}')[0];
for (const match of construction.matchAll(/p_(\d)=(\d*)\\sqrt(?:\{(\d+)\}|(\d))/g)) {
  const [,index,coefficient,braced,single] = match;
  const vector = radicands.map(r => r === +(braced || single) ? +(coefficient || 1) : 0);
  assert(vector.some(Boolean), 'Unknown printed radical');
  assert(!radicalParameters.has(+index));
  radicalParameters.set(+index, vector);
}
assert.strictEqual(radicalParameters.size,4);
const coordinateRows = construction.split('\\midrule')[1].split('\\bottomrule')[0]
  .trim().split('\n');
const printedVertices = [];
for (const row of coordinateRows) {
  const cells = row.replace(/\\\\\s*$/, '').split('&').map(c => c.replace(/[$\s]/g,''));
  assert.strictEqual(cells.length,3);
  let ids = [...cells[0].matchAll(/v_(?:\{(\d+)\}|(\d+))/g)].map(m => +(m[1] || m[2]));
  if(cells[0].includes('\\ldots')) ids=Array.from({length:ids[1]-ids[0]+1},(_,j)=>ids[0]+j);
  const xs=cells[1].split(',').map(Number);
  assert.strictEqual(xs.length,ids.length);
  assert(xs.every(Number.isInteger));
  const y=Array(radicands.length).fill(0);
  if(cells[2]!=='0') {
    const terms=[...cells[2].matchAll(/([+-]?)(p_\d)/g)];
    assert.strictEqual(terms.map(m=>m[0]).join(''),cells[2], 'Unsupported coordinate expression');
    for(const [,sign,param] of terms) {
      const vector=radicalParameters.get(+param.slice(2));
      assert(vector);
      vector.forEach((c,j)=>y[j]+=(sign==='-'?-1:1)*c);
    }
  }
  ids.forEach((id,j)=>{
    assert.strictEqual(id,printedVertices.length+1);
    printedVertices.push([xs[j],...y]);
  });
}
assert.deepStrictEqual(printedVertices,newToOld.map(i=>vertices[i-1]),
  'Printed coordinates or radical parameters differ from the exact data');
assert(construction.includes('v_i=(x_i/6,y_i/6)'));
assert.strictEqual(denominator,6);
console.log('Printed coordinates, radical definitions, scaling, and target parameters agree with the exact data.');

// The figures carry the forcing sequences. Check the data used to draw them,
// including every witness, assumption, final color, and contradictory edge.
const certificate=JSON.parse(read('data/qr23_proof_certificate.json'));
const expectedBranches=[[[8,0],[9,0]],[[8,0],[9,1],[11,1]],[[8,0],[9,1],[11,2]],
  [[8,0],[9,2]],[[8,1]],[[8,2],[11,0]],[[8,2],[11,1]]];
assert.strictEqual(certificate.leaves.length,7);
const root=Object.entries(certificate.root_colors).map(([v,c])=>[oldToNew.get(+v),c]);
assert.deepStrictEqual(root,[[10,0],[17,1],[18,2]]);
assert(adjacent(10,17)&&adjacent(10,18)&&adjacent(17,18));
for(const [index,leaf] of certificate.leaves.entries()) {
  assert.deepStrictEqual(leaf.assumptions.map(([v,c])=>[oldToNew.get(v),c]),expectedBranches[index]);
  const assigned=new Map(Object.entries(certificate.root_colors).map(([v,c])=>[+v,c]));
  const assumptions=[];
  for(const line of leaf.trace) {
    let match=line.match(/^ASSUME V(\d+)=(\d)\.$/);
    if(match) {
      const [v,c]=match.slice(1).map(Number);
      assert(!assigned.has(v));assigned.set(v,c);assumptions.push([v,c]);continue;
    }
    match=line.match(/^V(\d+)=(\d) forced by V(\d+)=(\d), V(\d+)=(\d)\.$/);
    if(match) {
      const [v,c,a,ca,b,cb]=match.slice(1).map(Number);
      assert(!assigned.has(v));
      assert.strictEqual(assigned.get(a),ca);assert.strictEqual(assigned.get(b),cb);
      assert(adjacent(oldToNew.get(v),oldToNew.get(a))&&adjacent(oldToNew.get(v),oldToNew.get(b)));
      assert.strictEqual(new Set([c,ca,cb]).size,3);assigned.set(v,c);
    } else assert(line.startsWith('Normalize the triangle:')||line.startsWith('CONTRADICTION:'),line);
  }
  assert.deepStrictEqual(assumptions,leaf.assumptions);
  assert.deepStrictEqual(vertices.map((_,i)=>assigned.has(i+1)?assigned.get(i+1):-1),leaf.colors);
  const [a,b,c]=leaf.conflict;
  assert(adjacent(oldToNew.get(a),oldToNew.get(b)));
  assert.strictEqual(assigned.get(a),c);assert.strictEqual(assigned.get(b),c);
  console.log('Figure case '+(index+1)+': every forcing step and final conflict verified.');
}

// Independent backtracking, with only color permutation symmetry fixed.
const neighbors=Array.from({length:24},()=>[]);
fixedEdges.forEach(([a,b])=>{neighbors[a].push(b);neighbors[b].push(a);});
const colors=Array(24).fill(-1);
colors[10]=0;colors[17]=1;colors[18]=2;
let calls=0;
function colorable() {
  calls++;
  let best=0,available=[];
  for(let v=1;v<=23;v++)if(colors[v]===-1) {
    const choices=[0,1,2].filter(c=>neighbors[v].every(w=>colors[w]!==c));
    if(!best||choices.length<available.length){best=v;available=choices;}
  }
  if(!best)return true;
  for(const c of available){colors[best]=c;if(colorable())return true;}
  colors[best]=-1;
  return false;
}
assert(!colorable());
console.log(`Independent exhaustive search: no three-coloring (${calls} recursive calls).`);
console.log('All article certificate checks passed.');
