// pruefe_lernseite_neu_1.0.js (07.11.2026) -- Knopfprobe der drei Neuerungen in Seite 1.7:
//   grosses Namensfeld (weil alle Lernbilder dasselbe Blickfeld zeigen), Bereit-Anzeige aus /stand,
//   Knopf "alles Gelernte zuruecksetzen" (mit zwei Rueckfragen) und der neue Knopf "zurueckstellen".
//   node pruefe_lernseite_neu_1.0.js ../lernen_1.7.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.7.html'; const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const stand = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const NAMEN = ['20261106_100110_b235', '20261106_100410_b164', '20261106_100410_b39', '20261106_100510_b133'];
const BILD = {}, BOX = {};
for (const n of NAMEN) { BILD[n] = M + n + '.jpg'; BOX[n] = fs.readFileSync(M + 'lernen_boxen_' + n + '.json', 'utf8'); }
const posts = []; let STAND = { yolo: { phase: 'laeuft', modell: 'best.pt', bilder_s: 28.8, tiere: 2, tiere_mittel_5s: 1.4 },
  training: { laeuft: false, gestartet: '2026-11-06 16:42:54', letzte_runde: { uhr: '2026-11-06 16:42:54' } } };

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const pg = await b.newPage({ viewport: { width: 1500, height: 1100 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  pg.on('console', m => { if (m.type() === 'error') fehler.push('console: ' + m.text()); });
  let fragen = 0; pg.on('dialog', d => { fragen++; d.accept(); });
  await pg.route('**/*', async r => {
    const u = r.request().url(), m = r.request().method();
    if (/\/stand/.test(u) && !/\/lernen/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STAND) });
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(stand) });
    if (/\/lernen\/zuruecksetzen/.test(u)) { posts.push({ art: 'zuruecksetzen' });
      stand.forEach(e => e.status = 'offen');
      return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"zurueckgesetzt":301,"gesamt":301,"sicherung":"sicherung_20261107_120000.json"}' }); }
    if (/\/lernen\/fertig/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"uhr":"12:00:00","training":true}' });
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { const n = mb[1];
      if (m === 'POST') { const d = JSON.parse(r.request().postData() || '{}'); posts.push({ art: 'boxen', name: n, status: d.status });
        const e = stand.find(x => x.name === n); if (e) e.status = d.status;
        return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, name: n, status: d.status, n_boxen: (d.boxen||[]).length }) }); }
      return r.fulfill({ status: 200, contentType: 'application/json', body: BOX[n] || '{"satz":"x","bild":0,"boxen":[]}' }); }
    const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/);
    if (mi) { const n = mi[1]; if (!BILD[n]) return r.fulfill({ status: 404, body: '' });
      return r.fulfill({ status: 200, contentType: 'image/jpeg', path: BILD[n] }); }
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html });
    return r.fulfill({ status: 404, body: '' }); });

  const txt = id => pg.evaluate(i => (document.getElementById(i) || {}).textContent || '', id);
  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil: 'load' }); await pg.waitForTimeout(1600);
  const P = [];

  const n1 = await txt('wername');
  P.push({ n: 'N1 grosses Namensfeld gefuellt', ok: /^\d{8}_\d{6}_b\d+$/.test(n1.trim()), txt: n1 });
  const pl = await txt('werplatz');
  P.push({ n: 'N2 Platznummer gross', ok: /von \d+/.test(pl), txt: pl });
  await pg.click('#weiter'); await pg.waitForTimeout(1300);
  const n2 = await txt('wername');
  P.push({ n: 'N3 Namensfeld wechselt beim Blaettern', ok: n2.trim() !== n1.trim(), txt: `${n1.trim()} -> ${n2.trim()}` });

  const ber = await txt('bereit');
  P.push({ n: 'N4 Bereit-Anzeige sagt den Zustand', ok: /Bereit|Training|Livedienst/.test(ber) && /best\.pt|Modell/.test(ber), txt: ber.slice(0, 95) });
  P.push({ n: 'N5 Bereit-Anzeige zeigt den Lernstand', ok: /geprüft/.test(ber) && /zurückgestellt/.test(ber), txt: ber.slice(95, 190) });

  STAND = { yolo: { phase: 'pausiert', modell: 'best.pt' }, training: { laeuft: true, gestartet: '2026-11-07 12:05:00', letzte_runde: { uhr: '2026-11-07 12:05:00' } } };
  await pg.waitForTimeout(5600);
  const ber2 = await txt('bereit');
  P.push({ n: 'N6 Bereit-Anzeige meldet laufendes Training', ok: /Training läuft/.test(ber2) && /vier Minuten/.test(ber2), txt: ber2.slice(0, 110) });
  STAND = { yolo: { phase: 'laeuft', modell: 'best.pt', bilder_s: 29.0, tiere: 1, tiere_mittel_5s: 0.6 }, training: { laeuft: false, gestartet: '2026-11-07 12:05:00', letzte_runde: { uhr: '2026-11-07 12:05:00' } } };
  await pg.waitForTimeout(5600);
  P.push({ n: 'N7 Bereit-Anzeige kehrt auf "bereit" zurueck', ok: /Bereit\./.test(await txt('bereit')), txt: (await txt('bereit')).slice(0, 80) });

  const vorZ = posts.length;
  await pg.click('#zurueckstellen'); await pg.waitForTimeout(1300);
  const letzter = posts[posts.length - 1] || {};
  P.push({ n: 'N8 "zurueckstellen" speichert den Stand', ok: posts.length > vorZ && letzter.status === 'zurueckgestellt',
    txt: posts.length > vorZ ? `gespeichert als ${letzter.status}` : 'kein Speichern ausgeloest' });

  fragen = 0; const vorR = posts.length;
  await pg.click('#zuruecksetzen'); await pg.waitForTimeout(1600);
  P.push({ n: 'N9 Zuruecksetzen fragt zweimal nach', ok: fragen === 2, txt: `${fragen} Rueckfragen` });
  P.push({ n: 'N10 Zuruecksetzen wird ausgefuehrt', ok: posts.slice(vorR).some(x => x.art === 'zuruecksetzen'),
    txt: (await txt('gespeichert')).slice(0, 80) });
  await pg.waitForTimeout(900);
  const ber3 = await txt('bereit');
  P.push({ n: 'N11 Lernstand danach neu geladen', ok: /301 .*offen|offen/.test(ber3), txt: ber3.slice(ber3.indexOf('Ihr Lernstand'), ber3.indexOf('Ihr Lernstand') + 80) });

  await pg.screenshot({ path: '../medien/lernseite_1_7.png', fullPage: false });
  const n_ok = P.filter(x => x.ok).length;
  console.log('\n===== NEUERUNGSPROBE ' + SEITE + '   ' + n_ok + ' von ' + P.length + ' bestanden');
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.n.padEnd(44)} ${String(x.txt).replace(/\s+/g, ' ').slice(0, 105)}`);
  console.log('  Seitenfehler: ' + (fehler.length ? fehler.join(' | ') : 'keine'));
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
