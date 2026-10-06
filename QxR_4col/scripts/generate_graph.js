#!/usr/bin/env node
// Regenerate the graph and exhaustive forcing certificate from exact coordinates.
// Usage: node scripts/generate_graph.js [--check]
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const output = path.resolve(__dirname, '../data');
assert(process.argv.slice(2).every(arg => arg === '--check'), 'Only --check is supported');
const check = process.argv.includes('--check');
const radicands = [2, 3, 5, 35];
const denominator = 6;
// (X,a2,a3,a5,a35) represents (X, sum ar sqrt(r))/6.
const vertices = [
  [-6,0,0,0,0], [-4,0,0,0,0], [-2,0,0,0,0],
  [0,0,0,0,0], [2,0,0,0,0], [4,0,0,0,0], [6,0,0,0,0],
  [-4,4,0,0,0], [-2,4,0,0,0], [0,4,0,0,0], [4,4,0,0,0],
  [-3,0,0,0,-1], [1,0,0,0,-1], [3,0,0,0,-1], [5,0,0,0,-1],
  [-1,4,0,0,-1], [-2,0,0,2,0], [0,0,0,2,0], [2,0,0,2,0],
  [0,4,0,2,0], [-3,0,3,0,0], [3,0,3,0,0], [1,0,0,2,-1]
];
assert.strictEqual(new Set(vertices.map(v => v.join(','))).size, 23);

// All operations affecting adjacency are on small exact integers.
function radicalProduct(r, s) {
  const n = r*s;
  let factor = 1;
  for (let candidate = 2; candidate*candidate <= n; candidate++)
    if (n % (candidate*candidate) === 0) factor = candidate;
  return [factor, n/(factor*factor)];
}
const edges = [];
for (let u=0; u<23; u++) for (let v=u+1; v<23; v++) {
  const d = vertices[u].map((a,i) => a-vertices[v][i]);
  const squared = new Map([[1, d[0]**2]]);
  for (let i=0; i<4; i++) for (let j=0; j<4; j++) {
    const [factor, r] = radicalProduct(radicands[i], radicands[j]);
    squared.set(r, (squared.get(r)||0)+factor*d[i+1]*d[j+1]);
  }
  if (squared.get(1) === denominator**2 && [...squared].every(([r,c]) => r===1 || c===0))
    edges.push([u+1, v+1]);
}
assert.strictEqual(edges.length, 45);
const mod = (a,n) => ((a%n)+n)%n;
const colors = vertices.map(p => 2*mod(p[0],2)+mod(Math.floor(p[0]/2)+p[3]/2,2));
for (const [u,v] of edges) assert.notStrictEqual(colors[u-1], colors[v-1]);
const neighbors = Array.from({length:23}, () => []);
for (const [u,v] of edges) { neighbors[u-1].push(v-1); neighbors[v-1].push(u-1); }
neighbors.forEach(list => list.sort((a,b) => a-b));

// Labels here match the stored coordinates; the article uses the permutation
// documented in README.md. Each branch contains every available color.
const root_colors = {4:0, 21:1, 22:2};
const tree = [2, {0:[3, {0:null, 1:[5, {1:null, 2:null}], 2:null}],
                 1:null, 2:[5, {0:null, 1:null}]}];
const initial = Array(23).fill(-1);
for (const [v,c] of Object.entries(root_colors)) initial[+v-1] = c;
for (const [u,v] of [[4,21],[4,22],[21,22]]) assert(neighbors[u-1].includes(v-1));
const leaves = [];
let nodes = 0;
function saturate(state, trace) {
  while (true) {
    for (const [u,v] of edges)
      if (state[u-1]>=0 && state[u-1]===state[v-1]) return [u,v,state[u-1]];
    let forced = false;
    for (let v=0; v<23; v++) {
      if (state[v]>=0) continue;
      const witnesses = new Map();
      for (const w of neighbors[v])
        if (state[w]>=0 && !witnesses.has(state[w])) witnesses.set(state[w],w);
      if (witnesses.size<2) continue;
      const [c1,c2] = [...witnesses.keys()].sort((a,b) => a-b);
      const c = 3-c1-c2, u = witnesses.get(c1), w = witnesses.get(c2);
      state[v] = c;
      trace.push(`V${v+1}=${c} forced by V${u+1}=${c1}, V${w+1}=${c2}.`);
      forced = true;
      break;
    }
    if (!forced) return null;
  }
}
function walk(branch, previous, assumptions, history) {
  nodes++;
  const state = previous.slice(), trace = history.slice();
  const conflict = saturate(state, trace);
  if (conflict) {
    assert.strictEqual(branch, null, 'Conflict before the declared leaf');
    const [u,v,c] = conflict;
    trace.push(`CONTRADICTION: the edge V${u}--V${v} has color ${c} at both endpoints.`);
    leaves.push({assumptions, conflict, trace, colors:state});
    return;
  }
  assert(branch, 'A leaf has no conflict');
  const [label,children] = branch, v = label-1;
  assert.strictEqual(state[v], -1);
  const allowed = [0,1,2].filter(c => neighbors[v].every(w => state[w]!==c));
  assert.deepStrictEqual(Object.keys(children).map(Number), allowed, 'Incomplete branch');
  for (const c of allowed) {
    const child = state.slice(); child[v] = c;
    walk(children[c], child, [...assumptions,[label,c]], [...trace,`ASSUME V${label}=${c}.`]);
  }
}
walk(tree, initial, [], ['Normalize the triangle: V4=0, V21=1, V22=2.']);
assert.strictEqual(nodes, 11);
assert.strictEqual(leaves.length, 7);
const graph = {
  description:'23-vertex 4-chromatic unit-distance graph in Q x R',
  denominator, radicands,
  coordinate_convention:'(X,a2,a3,a5,a35) -> (X/6,(a2 sqrt2+a3 sqrt3+a5 sqrt5+a35 sqrt35)/6)',
  vertices, edges_1based:edges, colors_0_to_3:colors
};
if (!check) fs.mkdirSync(output, {recursive:true});
for (const [name,data] of [['qr23.json',graph], ['qr23_proof_certificate.json',{root_colors,tree,leaves}]]) {
  const file = path.join(output,name);
  if (check) assert.deepStrictEqual(JSON.parse(fs.readFileSync(file,'utf8')), data, name+' is stale');
  else fs.writeFileSync(file, JSON.stringify(data,null,2)+'\n');
}
console.log(`${check ? 'Checked' : 'Generated'} exact graph and certificate: 23 vertices, 45 edges, seven exhaustive cases.`);
