#!/usr/bin/env node
// Compare ref probe vs site probe. Usage: node compare.mjs REF.json SITE.json [--hpct 3] [--px 2]
// Matches elements by text key (H:/T:). Reports height delta, missing keys, bbox(w,h)/typography deltas. Exit 1 if outside thresholds.
import fs from 'fs';
const [a, b, ...rest] = process.argv.slice(2); const o = { hpct: 3, px: 2 }; for (let i = 0; i < rest.length; i += 2) o[rest[i].slice(2)] = +rest[i + 1];
const R = JSON.parse(fs.readFileSync(a)), S = JSON.parse(fs.readFileSync(b)); let fail = 0;
const hd = (S.H - R.H) / R.H * 100; console.log(`HEIGHT ref=${R.H} site=${S.H} delta=${hd.toFixed(1)}% ${Math.abs(hd) <= o.hpct ? 'OK' : 'FAIL'}`); if (Math.abs(hd) > o.hpct) fail++;
console.log(`IMGS ref=${R.imgs.length} site=${S.imgs.length}  SVGS ref=${R.svgs} site=${S.svgs}`);
const miss = [], bad = []; let ok = 0;
for (const [k, r] of Object.entries(R.els)) { if (k.startsWith('F:')) continue; const s = S.els[k]; if (!s) { miss.push(k); continue; }
  const d = []; for (const f of ['w', 'h']) if (Math.abs(r[f] - s[f]) > o.px) d.push(`${f} ${r[f]}→${s[f]}`);
  for (const f of ['fs', 'fw', 'lh', 'ff']) if (r[f] !== s[f]) d.push(`${f} ${r[f]}→${s[f]}`);
  if (Math.abs(r.y - s.y) > Math.max(8, R.H * 0.01)) d.push(`y ${r.y}→${s.y}`);
  d.length ? bad.push(`${k}: ${d.join(', ')}`) : ok++; }
console.log(`ELEMENTS matched-ok=${ok} deviating=${bad.length} missing=${miss.length}`);
if (miss.length) console.log('MISSING:\n  ' + miss.join('\n  '));
if (bad.length) console.log('DEVIATING:\n  ' + bad.join('\n  '));
if (miss.length || bad.length) fail++;
process.exit(fail ? 1 : 0);
