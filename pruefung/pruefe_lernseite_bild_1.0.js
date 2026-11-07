// pruefe_lernseite_bild_1.0.js (07.11.2026) -- Seine Meldung: "es wird immer das selbe bild angezeigt".
// Die bisherige Knopfprobe konnte das NICHT sehen, weil der Stellvertreter fuer jeden Namen dasselbe Bild
// lieferte. Diese Probe gibt jedem Namen SEIN eigenes echtes Lernbild und prueft nach jedem Blaettern den
// Inhalt der Leinwand (Pruefsumme der Bildpunkte). Aendert er sich nicht, ist der Fehler da.
//   node pruefe_lernseite_bild_1.0.js ../lernen_1.6.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.6.html'; const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const stand = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const NAMEN = ['20261106_100110_b235', '20261106_100410_b164', '20261106_100410_b39', '20261106_100510_b133'];
const BILD = {}, BOX = {};
for (const n of NAMEN) { BILD[n] = M + n + '.jpg'; BOX[n] = fs.readFileSync(M + 'lernen_boxen_' + n + '.json', 'utf8'); }
const geholt = [];

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const pg = await b.newPage({ viewport: { width: 1500, height: 1050 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  pg.on('console', m => { if (m.type() === 'error') fehler.push('console: ' + m.text()); });
  await pg.route('**/*', async r => {
    const u = r.request().url(), m = r.request().method();
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(stand) });
    if (/\/lernen\/fertig/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"uhr":"12:00:00","training":true}' });
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { const n = mb[1];
      if (m === 'POST') { const d = JSON.parse(r.request().postData() || '{}'); const e = stand.find(x => x.name === n); if (e) e.status = d.status;
        return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, name: n, status: d.status, n_boxen: (d.boxen||[]).length }) }); }
      if (!BOX[n]) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"satz":"x","bild":0,"boxen":[]}' });
      return r.fulfill({ status: 200, contentType: 'application/json', body: BOX[n] }); }
    const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/);
    if (mi) { const n = mi[1]; geholt.push(n);
      if (!BILD[n]) return r.fulfill({ status: 404, body: '' });
      return r.fulfill({ status: 200, contentType: 'image/jpeg', path: BILD[n] }); }
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html });
    return r.fulfill({ status: 404, body: '' }); });

  // Pruefsumme der Leinwand: Summe ueber jeden 997. Bildpunkt, damit Rahmenfarben nicht dominieren
  const leinwand = () => pg.evaluate(() => { const c = document.getElementById('leinwand');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0;
    for (let i = 0; i < d.length; i += 997) h = (h * 31 + d[i]) >>> 0; return h; });
  const info = () => pg.evaluate(() => (document.getElementById('info') || {}).textContent || '');
  const aktiv = () => pg.evaluate(() => (document.querySelector('#liste div.aktiv') || {}).textContent || '');

  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil: 'load' }); await pg.waitForTimeout(1500);
  const P = []; let vorH = await leinwand(); let vorI = await info();
  P.push({ n: 'B0 Start zeigt ein Bild', ok: vorH !== 0, txt: `Leinwand ${vorH}, ${vorI.slice(0, 40)}` });

  for (let s = 1; s <= 3; s++) {
    await pg.click('#weiter'); await pg.waitForTimeout(1400);
    const h = await leinwand(), i = await info(), a = await aktiv();
    const name = (i.match(/^(\S+)/) || [])[1] || '';
    P.push({ n: `B${s} blaettern: Leinwand aendert sich`, ok: h !== vorH,
      txt: h !== vorH ? `neues Bild (${name})` : `GLEICHES BILD -- Leinwand ${h} unveraendert, Infozeile sagt ${name}` });
    P.push({ n: `B${s} Name, Liste und Bild passen`, ok: !!name && a.includes(name) && geholt[geholt.length - 1] === name,
      txt: `Infozeile ${name}, Liste ${a.trim().split(' ')[0]}, zuletzt geholtes Bild ${geholt[geholt.length - 1]}` });
    vorH = h; vorI = i;
  }
  await pg.click('#zurueck'); await pg.waitForTimeout(1400);
  const hz = await leinwand();
  P.push({ n: 'B4 zurueck: Leinwand aendert sich', ok: hz !== vorH, txt: hz !== vorH ? 'anderes Bild' : 'GLEICHES BILD' });

  await pg.screenshot({ path: '../medien/bildprobe.png' });
  const n_ok = P.filter(x => x.ok).length;
  console.log('\n===== BILDPROBE ' + SEITE + '   ' + n_ok + ' von ' + P.length + ' bestanden');
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.n.padEnd(40)} ${x.txt}`);
  console.log('  geholte Bilder in Reihenfolge: ' + geholt.join(', '));
  console.log('  Seitenfehler: ' + (fehler.length ? fehler.join(' | ') : 'keine'));
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
