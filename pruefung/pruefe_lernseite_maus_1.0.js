// pruefe_lernseite_maus_1.0.js (07.11.2026) -- Die Leinwand wird seit 1.8 auf die Fenstergroesse skaliert.
// Damit haengt die Umrechnung Mausort -> Bildpunkt an lage(): (clientX - rect.left) * 640 / rect.width.
// Stimmt sie nicht, landen SEINE gezeichneten Rahmen an der falschen Stelle im Bild -- und das faellt auf
// dem Bildschirm nicht auf, weil der Rahmen ja dort gezeichnet wird, wo man zieht. Diese Probe zieht einen
// Rahmen, speichert und vergleicht die GESPEICHERTEN Bildpunkte mit der Rechnung aus dem Leinwandrahmen.
//   node pruefe_lernseite_maus_1.0.js ../lernen_1.8.html [breite] [hoehe]
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.8.html';
const W = +(process.argv[3] || 1920), H = +(process.argv[4] || 1080);
const M = '../medien/'; const html = fs.readFileSync(SEITE, 'utf8');
const stand = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const N = ['20261106_100110_b235','20261106_100410_b164','20261106_100410_b39','20261106_100510_b133'];
const BILD = {}, BOX = {}; for (const n of N) { BILD[n] = M + n + '.jpg'; BOX[n] = fs.readFileSync(M + 'lernen_boxen_' + n + '.json','utf8'); }
const STAND = { yolo:{phase:'laeuft',modell:'best.pt',bilder_s:28.8,tiere:2,tiere_mittel_5s:1.4},
  training:{laeuft:false,gestartet:'2026-11-06 16:42:54',letzte_runde:{uhr:'2026-11-06 16:42:54'}} };
const posts = [];

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const pg = await b.newPage({ viewport: { width: W, height: H } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  await pg.route('**/*', async r => { const u = r.request().url(), m = r.request().method();
    if (/\/stand/.test(u) && !/\/lernen/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(STAND) });
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(stand) });
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { if (m === 'POST') { const d = JSON.parse(r.request().postData() || '{}'); posts.push(d);
        return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify({ ok:true, name:mb[1], status:d.status, n_boxen:(d.boxen||[]).length }) }); }
      return r.fulfill({ status:200, contentType:'application/json', body: BOX[mb[1]] || BOX[N[0]] }); }
    const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/);
    if (mi) return r.fulfill({ status:200, contentType:'image/jpeg', path: BILD[mi[1]] || BILD[N[0]] });
    if (/\/lernen$/.test(u)) return r.fulfill({ status:200, contentType:'text/html; charset=utf-8', body: html });
    return r.fulfill({ status:404, body:'' }); });

  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil:'load' }); await pg.waitForTimeout(1500);
  const P = [];
  const rect = await pg.evaluate(() => { const b = document.getElementById('leinwand').getBoundingClientRect();
    return { x: b.x, y: b.y, w: b.width, h: b.height }; });
  const vh = rect.w / rect.h, soll_vh = 640 / 480;
  P.push({ n: 'M0b Seitenverhaeltnis 4:3 (Bild nicht gequetscht)', ok: Math.abs(vh - soll_vh) / soll_vh < 0.01,
    txt: `${Math.round(rect.w)} x ${Math.round(rect.h)} = ${vh.toFixed(3)}, soll ${soll_vh.toFixed(3)}` });
  P.push({ n: 'M0 Leinwand hat eine Groesse', ok: rect.w > 100 && rect.h > 100,
    txt: `${Math.round(rect.w)} x ${Math.round(rect.h)} Bildschirmpunkte fuer 640 x 480 Bildpunkte (Faktor ${(rect.w/640).toFixed(2)})` });

  // Rahmen ziehen: von 30 % / 30 % bis 55 % / 60 % der Leinwand
  const p1 = { x: rect.x + rect.w * 0.30, y: rect.y + rect.h * 0.30 };
  const p2 = { x: rect.x + rect.w * 0.55, y: rect.y + rect.h * 0.60 };
  const vorher = await pg.evaluate(() => document.querySelectorAll('#liste div').length) && (await pg.evaluate(() => 0));
  await pg.mouse.move(p1.x, p1.y); await pg.mouse.down();
  await pg.mouse.move((p1.x + p2.x) / 2, (p1.y + p2.y) / 2, { steps: 5 });
  await pg.mouse.move(p2.x, p2.y, { steps: 5 }); await pg.mouse.up(); await pg.waitForTimeout(300);

  const soll = { x0: Math.round((p1.x - rect.x) * 640 / rect.w), y0: Math.round((p1.y - rect.y) * 480 / rect.h),
                 x1: Math.round((p2.x - rect.x) * 640 / rect.w), y1: Math.round((p2.y - rect.y) * 480 / rect.h) };
  const n0 = posts.length;
  await pg.click('#richtig'); await pg.waitForTimeout(900);
  const gesendet = posts[posts.length - 1];
  const neu = gesendet && (gesendet.boxen || []).filter(b => b.quelle === 'hand');
  const ok = neu && neu.length === 1 &&
    Math.abs(neu[0].x0 - soll.x0) <= 2 && Math.abs(neu[0].y0 - soll.y0) <= 2 &&
    Math.abs(neu[0].x1 - soll.x1) <= 2 && Math.abs(neu[0].y1 - soll.y1) <= 2;
  P.push({ n: 'M1 gezogener Rahmen wird gespeichert', ok: !!(neu && neu.length === 1),
    txt: neu ? `${neu.length} Rahmen mit Quelle "hand"` : 'nichts gesendet' });
  P.push({ n: 'M2 Rahmen liegt an der gezogenen Stelle', ok: !!ok,
    txt: neu && neu.length ? `gespeichert ${neu[0].x0},${neu[0].y0}..${neu[0].x1},${neu[0].y1}  erwartet ${soll.x0},${soll.y0}..${soll.x1},${soll.y1}` : '-' });
  P.push({ n: 'M3 Rahmen liegt im Bild (0..640 / 0..480)', ok: !!(neu && neu.length && neu[0].x1 <= 640 && neu[0].y1 <= 480 && neu[0].x0 >= 0 && neu[0].y0 >= 0),
    txt: neu && neu.length ? `${neu[0].x0},${neu[0].y0}..${neu[0].x1},${neu[0].y1}` : '-' });

  const n_ok = P.filter(x => x.ok).length;
  console.log(`\n===== MAUSPROBE ${SEITE} bei ${W}x${H}   ${n_ok} von ${P.length} bestanden`);
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.n.padEnd(42)} ${x.txt}`);
  if (fehler.length) console.log('  Seitenfehler: ' + fehler.join(' | '));
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
