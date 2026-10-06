// Exact checks for the dyadic certificates; no third-party dependencies.
// Usage: node scripts/verify_dyadic16.js [article.tex]
const fs = require('fs');
const assert = require('assert');
const mod = (a, n) => ((a % n) + n) % n;
const key = (a, b) => `${a},${b}`;
const path = require('path');
const repoRoot = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.resolve(repoRoot, name), 'utf8');
const articleFile = process.argv[2] || 'article.tex';
const article = read(articleFile);
console.log(`Checking dyadic certificates in ${articleFile}.`);
const block = article.split('% BEGIN C16 TABLE')[1].split('% END C16 TABLE')[0];
const rows = block.split('\n').filter(s => /^\d+ &/.test(s)).map((s, y) => {
  const cells = s.split('&').map(v => Number(v.replace(/\\/g, '').trim()));
  assert.strictEqual(cells[0], y);
  assert.strictEqual(cells.length, 17);
  assert(cells.slice(1).every(c => Number.isInteger(c) && c >= 0 && c < 6));
  return cells.slice(1).join('');
});
assert.strictEqual(rows.length, 16);
assert([...rows.join('')].every(c => /^[0-5]$/.test(c)));

const T = new Set();
for (let a = 1; a < 16; a += 2) { T.add(key(a, 0)); T.add(key(0, a)); }
for (let a = 2; a < 16; a += 4) { T.add(key(a, 8)); T.add(key(8, a)); }
for (const a of [4, 8, 12]) T.add(key(a, a));
assert.strictEqual(T.size, 27);
assert(!T.has('0,0'));
const shifts = [...T].map(v => v.split(',').map(Number));
for (const [a,b] of shifts) assert(T.has(key(mod(-a,16),mod(-b,16))));
let comparisons = 0;
for (let y=0;y<16;y++) for (let x=0;x<16;x++) for (const [a,b] of shifts) {
  assert.notStrictEqual(rows[y][x], rows[(y+b)%16][(x+a)%16]);
  comparisons++;
}
const sizes = Array.from({length:6},(_,c) => [...rows.join('')].filter(z=>+z===c).length);
assert.deepStrictEqual(sizes,[47,45,44,39,38,43]);
console.log(`C16: ${comparisons} directed checks pass; 256 vertices, 3456 edges; classes ${sizes}.`);

const roots = new Map();
for(let r=1;r<256;r+=2) if(!roots.has(r*r%256)) roots.set(r*r%256,r);
assert.deepStrictEqual([...roots.keys()].sort((a,b)=>a-b),Array.from({length:32},(_,i)=>8*i+1));
const observed=new Set(), byClass={ordinary:0,class3:0,split:0};
let residueChecks=0;
for(let M=0;M<256;M++) {
  if(M%4===0)continue;
  let alpha,beta,type;
  if(M%4!==3) { alpha=beta=M%2; type='ordinary'; }
  else if(M%8===3) {
    const r=roots.get(M*171%256); // 171 is the inverse of 3 modulo 256.
    assert.strictEqual(mod(3*r*r-M,256),0);
    alpha=beta=3*r;type='class3';
  } else {
    const r=roots.get(mod(-M,256));
    assert.strictEqual(mod(r*r+M,256),0);
    alpha=r;beta=-r;type='split';
  }
  for(let a=0;a<128;a++)for(let b=0;b<128;b++) {
    if((a*a+M*b*b)%256!==64)continue;
    const f=a+alpha*b,g=a+beta*b;
    assert(f%2===0&&g%2===0);
    const step=key(mod(f/2,16),mod(g/2,16));
    assert(T.has(step),`Bad image for ${M},${a},${b}: ${step}`);
    observed.add(step);byClass[type]++;residueChecks++;
  }
}
assert.strictEqual(residueChecks,28672);
assert.deepStrictEqual([...observed].sort(),[...T].sort());
for(let delta=-64;delta<=64;delta+=2)for(let start=-64;start<=64;start++)
  assert.strictEqual(Math.floor((start+delta)/2)-Math.floor(start/2),delta/2);
for(let q=-15;q<=15;q+=2)assert(T.has(key(mod(4*q,16),mod(4*q,16))));
console.log(`Transfer: ${residueChecks} residue triples pass (${JSON.stringify(byClass)}), including negative half-increments.`);

// Check the conventional exactly-one-color CNF encoding independently.
let clauses=0;
for(let v=0;v<256;v++) {
  const bits=Array.from({length:6},(_,c)=>+rows[Math.floor(v/16)][v%16]===c);
  assert(bits.some(Boolean));clauses++;
  for(let c=0;c<6;c++)for(let d=c+1;d<6;d++){assert(!bits[c]||!bits[d]);clauses++;}
  for(const [a,b] of shifts) {
    const w=16*((Math.floor(v/16)+b)%16)+(v%16+a)%16;
    if(w<=v)continue;
    for(let c=0;c<6;c++) {
      assert(!bits[c]||+rows[Math.floor(w/16)][w%16]!==c);clauses++;
    }
  }
}
assert.strictEqual(clauses,24832);
console.log(`CNF encoding: 1536 variables, all ${clauses} clauses satisfied.`);

const inverse=(u,n)=>{for(let v=1;v<n;v+=2)if(u*v%n===1)return v;throw Error('Not a unit');};
function target(s,m) {
  const n=2**m,S=new Set();
  for(let u=1;u<n;u+=2) {
    const inv=inverse(u,n);
    for(let j=0;j<=2*s-2;j++)S.add(key(2**j*u%n,2**(2*s-2-j)*inv%n));
    for(const j of [s-1,s])S.add(key(2**j*u%n,2**j*u%n));
  }
  assert(!S.has('0,0'));
  return S;
}
assert.deepStrictEqual([...target(3,4)].sort(),[...T].sort());
const weighted=new Map();
const put=(a,b,w)=>{assert(!weighted.has(key(a,b)));weighted.set(key(a,b),w);};
for(let a=1;a<32;a+=2){put(a,0,5);put(0,a,5);}
for(let a=2;a<32;a+=4){put(a,0,5);put(0,a,5);}
for(let a=4;a<32;a+=8){put(a,16,2);put(16,a,2);}
put(8,8,8);put(24,24,8);put(16,16,0);
assert.deepStrictEqual([...weighted.keys()].sort(),[...target(4,5)].sort());
assert.strictEqual(weighted.size,59);
assert.strictEqual([...weighted.values()].reduce((a,b)=>a+b),272);

// Compute all Fourier eigenvalues in Z[zeta_32] using zeta_32^16=-1.
// This checks the printed spectrum without floating-point trigonometry.
const spectrum=new Map();
const R=(j,r)=>r%(32>>j)===0?16>>j:r%(16>>j)===0?-(16>>j):0;
for(let r=0;r<32;r++)for(let t=0;t<32;t++) {
  const coeff=Array(16).fill(0);
  for(const [z,w] of weighted) {
    const [a,b]=z.split(',').map(Number),e=(r*a+t*b)%32;
    coeff[e%16]+=e<16?w:-w;
  }
  assert(coeff.slice(1).every(c=>c===0));
  const lambda=coeff[0];
  const formula=5*(R(0,r)+R(0,t))+5*(R(1,r)+R(1,t))
    +2*((-1)**t*R(2,r)+(-1)**r*R(2,t))+16*[1,0,-1,0][(r+t)%4];
  assert.strictEqual(lambda,formula);
  spectrum.set(lambda,(spectrum.get(lambda)||0)+1);
}
const expected=[[-48,153],[-24,88],[-16,128],[0,272],[8,128],[16,192],[112,54],[136,8],[272,1]];
assert.deepStrictEqual([...spectrum].sort((a,b)=>a[0]-b[0]),expected);
function spectrumRow(label) {
  const line = article.split('\n').find(s => s.startsWith(`\\text{${label}}&`));
  assert(line, 'Missing printed spectrum row: '+label);
  const cells = line.split('&').slice(1).map(s => Number(s.replace(/\\.*$/, '').replace(/\.$/, '').trim()));
  assert(cells.every(Number.isInteger));
  return cells;
}
assert.deepStrictEqual(spectrumRow('Eigenvalue'), expected.map(([value]) => value));
assert.deepStrictEqual(spectrumRow('Multiplicity'), expected.map(([,count]) => count));
console.log(`H_4,5: exact spectrum ${JSON.stringify(expected)}; weighted degree 272, minimum -48, chromatic bound 20/3.`);
assert.strictEqual(target(4,6).size*4096/2,241664);
assert.strictEqual([16,3,5,7,11,13,17,19].reduce((a,b)=>a*b),77597520);
assert(article.includes('77\\,597\\,520=16\\cdot3'));
assert(!article.includes('38\\,798\\,760'));
console.log('All dyadic certificate checks passed. The external Borel bound is not checked by this script.');
