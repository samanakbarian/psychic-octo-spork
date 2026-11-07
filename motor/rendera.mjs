/**
 * Renderar en film ur ett manus. Upplägget är detsamma som för matchfilmerna
 * i loven-stats-backend: sidan har window.render(t), Playwright stegar ruta
 * för ruta och ffmpeg sätter ihop bild och ljud. Två skillnader för fart:
 * flera flikar renderar var sin del parallellt, och rutorna går som JPEG rakt
 * in i ffmpeg i stället för att sparas som PNG-filer.
 *
 *   node motor/rendera.mjs films/02-sandladan/manus.json
 *   node motor/rendera.mjs films/02-sandladan/manus.json --stillbild 2,10,30
 *   node motor/rendera.mjs films/02-sandladan/manus.json --forhandsvisa
 */
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const flagga = n => { const i = args.indexOf(n); return i < 0 ? null : (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true); };
const manusFil = path.resolve(args.find(a => a.endsWith('.json')) || '');
if (!fs.existsSync(manusFil)) { console.error('Ange ett manus: node motor/rendera.mjs films/<film>/manus.json'); process.exit(1); }
const filmMapp = path.dirname(manusFil);
const ut = path.join(filmMapp, 'output');
fs.mkdirSync(ut, { recursive: true });
const namn = path.basename(filmMapp).replace(/^\d+-/, '');
const ARBETARE = Number(flagga('--arbetare') || Math.min(4, os.cpus().length));

// ---------------------------------------------------------------- liten webbserver
const TYPER = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.ttf': 'font/ttf', '.otf': 'font/otf', '.png': 'image/png', '.jpg': 'image/jpeg' };
const server = http.createServer((req, res) => {
  const p = path.join(ROT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': TYPER[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(ok => server.listen(Number(flagga('--port') || 0), '127.0.0.1', ok));
const bas = `http://127.0.0.1:${server.address().port}/motor/motor.html?manus=/${path.relative(ROT, manusFil)}`;


function process_(cmd, argv, stdin = 'ignore') {
  const p = spawn(cmd, argv, { stdio: [stdin, 'ignore', 'pipe'] });
  let err = '';
  p.stderr.on('data', d => { err += d; });
  p.klar = new Promise((ok, fel) => p.on('close', k => (k === 0 ? ok() : fel(new Error(`${cmd}: ${err.slice(-500)}`)))));
  return p;
}

async function oppna(browser) {
  const sida = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  sida.on('pageerror', e => console.error('Sidfel:', e.message));
  await sida.goto(bas + '&rendera=1');
  await sida.waitForFunction(() => window.KLAR === true, null, { timeout: 30000 });
  return sida;
}

const bild = (sida, t) => sida.evaluate(t => { window.render(t); return document.getElementById('duk').toDataURL('image/jpeg', 0.93); }, t)
  .then(u => Buffer.from(u.slice(u.indexOf(',') + 1), 'base64'));

async function kor() {
  const t0 = Date.now();
  const browser = await chromium.launch();
  try {
    const forsta = await oppna(browser);
    const { TIDER, HANDELSER } = await forsta.evaluate(() => ({ TIDER: window.TIDER, HANDELSER: window.HANDELSER }));

    const still = flagga('--stillbild');
    if (still) {
      for (const t of String(still).split(',').map(Number)) {
        const fil = path.join(ut, `stillbild_${t}.jpg`);
        fs.writeFileSync(fil, await bild(forsta, t));
        console.log(fil);
      }
      return;
    }

    // Ljudet görs parallellt med bilden.
    const hFil = path.join(ut, 'handelser.json');
    fs.writeFileSync(hFil, JSON.stringify({ tider: TIDER, handelser: HANDELSER }, null, 1));
    const wav = path.join(ut, 'ljud.wav');
    const ljud = process_('python3', [path.join(ROT, 'motor', 'ljud.py'), manusFil, hFil, wav]);

    const fps = TIDER.fps || 30;
    const antal = Math.round(TIDER.total * fps);
    const del = Math.ceil(antal / ARBETARE);
    const sidor = [forsta, ...(await Promise.all(Array.from({ length: ARBETARE - 1 }, () => oppna(browser))))];
    let klara = 0;
    const segment = await Promise.all(sidor.map(async (sida, a) => {
      const fran = a * del, till = Math.min(antal, fran + del);
      const seg = path.join(ut, `del_${a}.mp4`);
      const ff = process_('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', String(fps), seg], 'pipe');
      for (let i = fran; i < till; i++) {
        const buf = await bild(sida, i / fps);
        if (!ff.stdin.write(buf)) await new Promise(ok => ff.stdin.once('drain', ok));
        if (++klara % 150 === 0) console.log(`  ${klara}/${antal} rutor`);
      }
      ff.stdin.end();
      await ff.klar;
      return seg;
    }));
    await ljud.klar;

    const lista = path.join(ut, 'delar.txt');
    fs.writeFileSync(lista, segment.map(s => `file '${s}'`).join('\n'));
    const mp4 = path.join(ut, `${namn}_tiktok.mp4`);
    await process_('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lista, '-i', wav,
      '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4]).klar;
    for (const s of [...segment, lista]) fs.rmSync(s);
    console.log(`Klar: ${path.relative(process.cwd(), mp4)}  (${TIDER.total.toFixed(1)} s film, ${((Date.now() - t0) / 1000).toFixed(0)} s rendering)`);
  } finally {
    await browser.close();
  }
}

if (flagga('--forhandsvisa')) {
  console.log(`Öppna i webbläsaren:\n  ${bas}\n(mellanslag spelar/pausar, Ctrl+C avslutar)`);
} else {
  await kor();
  server.close();
}
