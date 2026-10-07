#!/usr/bin/env node
// Headless-Chrome renderer + probe. Node >=22 (built-in WebSocket/fetch). No deps.
// Usage:
//  node render.mjs --url URL --out DIR --name NAME [--widths 1440,390] [--click "Text"]... [--serve DIR] [--wait 5000] [--timeout 120000]
//  --serve DIR: starts `python3 -m http.server` on a free port for DIR; use {SERVE} in --url.
//  --click: clicks the smallest visible element whose trimmed text starts with Text (repeatable, in order) -> state render.
// Outputs: NAME_<w>.png (full page) and NAME_<w>.json (probe).
import fs from 'fs'; import os from 'os'; import path from 'path'; import net from 'net'; import { spawn } from 'child_process';
const argv = process.argv.slice(2); const opt = { widths: '1440,390', wait: '5000', timeout: '120000', click: [] };
for (let i = 0; i < argv.length; i++) { const k = argv[i].replace(/^--/, ''); const v = argv[++i]; if (k === 'click') opt.click.push(v); else opt[k] = v; }
if (!opt.url || !opt.out || !opt.name) { console.error('need --url --out --name'); process.exit(2); }
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const freePort = () => new Promise(r => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => r(p)); }); });
const kids = []; let profile;
const cleanup = () => { for (const k of kids) { try { process.kill(-k.pid, 'SIGKILL'); } catch { try { k.kill('SIGKILL'); } catch {} } } if (profile) try { fs.rmSync(profile, { recursive: true, force: true }); } catch {} };
process.on('exit', cleanup); for (const s of ['SIGINT', 'SIGTERM']) process.on(s, () => process.exit(130));
const hard = setTimeout(() => { console.error('TIMEOUT'); process.exit(124); }, +opt.timeout); hard.unref();
const PROBE = `(()=>{const vis=e=>{const b=e.getBoundingClientRect();return b.width>0&&b.height>0};
const info=e=>{const c=getComputedStyle(e),b=e.getBoundingClientRect();return {x:Math.round(b.left),y:Math.round(b.top+scrollY),w:Math.round(b.width),h:Math.round(b.height),ff:c.fontFamily.split(',')[0].replace(/"/g,''),fs:c.fontSize,fw:c.fontWeight,lh:c.lineHeight,color:c.color,bg:c.backgroundColor,r:c.borderRadius,shadow:c.boxShadow}};
const out={H:document.documentElement.scrollHeight,W:innerWidth,imgs:[...document.images].filter(i=>i.naturalWidth&&vis(i)).map(i=>decodeURI(i.src.split('/').pop())),svgs:[...document.querySelectorAll('svg')].filter(vis).length,els:{}};
const add=(k,e)=>{if(!(k in out.els))out.els[k]=info(e)};
document.querySelectorAll('h1,h2,h3,h4,button,a,label,th,td,dt,dd,summary,[role=button]').forEach(e=>{if(!vis(e))return;const t=(e.innerText||e.getAttribute('aria-label')||'').trim().replace(/\\s+/g,' ').slice(0,40);if(t)add(e.tagName.match(/^H\\d$/)?'H:'+t:'T:'+t,e)});
document.querySelectorAll('input,textarea,select').forEach((e,i)=>{if(vis(e))add('F:'+(e.name||e.placeholder||e.type)+'#'+i,e)});
return out})()`;
async function main() {
  fs.mkdirSync(opt.out, { recursive: true });
  let url = opt.url;
  if (opt.serve) { const p = await freePort(); const s = spawn('python3', ['-m', 'http.server', String(p), '--bind', '127.0.0.1'], { cwd: opt.serve, stdio: 'ignore', detached: true }); kids.push(s); url = url.replace('{SERVE}', `http://127.0.0.1:${p}`); await sleep(800); }
  const port = await freePort(); profile = fs.mkdtempSync(path.join(os.tmpdir(), 'dd-chrome-'));
  const ch = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--hide-scrollbars', '--no-first-run', '--no-default-browser-check', '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore', detached: true }); kids.push(ch);
  let ver; for (let i = 0; i < 50 && !ver; i++) { try { ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); } catch { await sleep(200); } }
  if (!ver) throw new Error('chrome did not start');
  const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = {}; ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
  const send = (method, params = {}) => new Promise((r, j) => { const i = ++id; const to = setTimeout(() => j(new Error('CDP timeout ' + method)), 30000); pend[i] = m => { clearTimeout(to); m.error ? j(new Error(method + ': ' + m.error.message)) : r(m.result); }; ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.value;
  await send('Page.enable'); await send('Runtime.enable');
  for (const w of opt.widths.split(',').map(Number)) {
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: 900, deviceScaleFactor: 1, mobile: w < 600 });
    await send('Page.navigate', { url }); await sleep(+opt.wait);
    for (const txt of opt.click) {
      const ok = await ev(`(()=>{const T=${JSON.stringify(txt)};
if(T.startsWith('css:')){const e=document.querySelector(T.slice(4));if(!e)return false;e.click();return 'css'}
const C=[];document.querySelectorAll('body *').forEach(e=>{const b=e.getBoundingClientRect();if(!b.width||!b.height)return;const t=(e.innerText||'').trim();const lab=e.getAttribute('aria-label')||e.getAttribute('title')||'';if(t.startsWith(T)||lab===T)C.push({e,t})});
if(!C.length)return false;
const score=c=>{const btn=c.e.closest('button,[role=button],summary,label,[data-action]');const link=c.e.closest('a[href]');const inChrome=c.e.closest('header,footer,nav,dc-import');return (btn?0:1000)+(link?500:0)+(inChrome?2000:0)+c.t.length};
C.sort((a,b)=>score(a)-score(b));const best=C[0].e;const el=best.closest('button,[role=button],summary,label,a,[data-action]')||best;el.click();return el.tagName+':'+(el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,30)})()`);
      console.log(`click "${txt}": ${ok}`); await sleep(900);
    }
    const H = Math.min(await ev('document.documentElement.scrollHeight'), 16000);
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: H, deviceScaleFactor: 1, mobile: w < 600 }); await sleep(1200);
    const probe = await ev(PROBE); probe.url = url; probe.clicks = opt.click;
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: H, scale: 1 } });
    fs.writeFileSync(path.join(opt.out, `${opt.name}_${w}.png`), Buffer.from(shot.data, 'base64'));
    fs.writeFileSync(path.join(opt.out, `${opt.name}_${w}.json`), JSON.stringify(probe, null, 1));
    console.log(`${opt.name}_${w}: H=${probe.H} els=${Object.keys(probe.els).length} imgs=${probe.imgs.length} svgs=${probe.svgs}`);
  }
  ws.close();
}
main().then(() => process.exit(0), e => { console.error('ERROR', e.message); process.exit(1); });
