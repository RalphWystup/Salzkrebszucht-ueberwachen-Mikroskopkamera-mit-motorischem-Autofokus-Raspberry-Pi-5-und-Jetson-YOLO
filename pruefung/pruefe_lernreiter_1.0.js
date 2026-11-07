// pruefe_lernreiter_1.0.js (06.11.2026, 17:50) -- Seite 1.31 im echten Browser: Reiter "Lernen" laedt die Lernseite des Jetson (:8095/lernen)
// im Rahmen, aber erst beim Oeffnen und nur, wenn der Jetson antwortet. Zwei Faelle: Jetson da (Rahmen laedt lernen_1.5.html, Liste, Bild)
// und Jetson weg (Hinweis, kein src). Aufruf: NODE_PATH=/tmp/node_modules CHROME=... node pruefe_lernreiter_1.0.js (stub8090.py laeuft, index.html = Seite 1.31)
const { chromium } = require('playwright'); const fs = require('fs');
const lern = fs.readFileSync('../lernen_1.5.html', 'utf8');
const stand = { fassung: '1.10', laeuft_min: 5, platte_frei_gb: 16, training: { laeuft: false }, yolo: { phase: 'laeuft', fassung: '1.3', modell: 'best.pt', tiere_mittel_5s: 0.2, bewegt: 0, ruhend: 0, groesse_mm_median: 1.0, tempo_mm_s_median: 0.5, verarbeitet_s: 28 }, live: { verbunden: true, bilder_je_s: 29, mbit_je_s: 10, letztes_bild_vor_s: 0.1, abgeschnitten: 0 } };
const liste = [{ name: '20261106_150000_017', status: 'offen', n_boxen: 3 }, { name: '20261106_150000_060', status: 'geprueft', n_boxen: 2 }];
const boxen = { satz: '20261106_150000', bild: 17, status: 'offen', boxen: [{ x0: 100, y0: 100, x1: 160, y1: 140, quelle: 'farbe', klasse: 'tier' }] };
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(e.message));
  let da = true; const json = (o) => ({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(o) });
  await pg.route('**/<IP-des-Jetson>:8095/**', r => { const u = r.request().url();
    if (!da) return r.abort('connectionrefused');
    if (/\/lernen\/liste/.test(u)) return r.fulfill(json(liste));
    if (/\/lernen\/boxen\//.test(u)) return r.fulfill(json(boxen));
    if (/\/lernen\/bild\//.test(u)) return r.fulfill({ status: 200, contentType: 'image/jpeg', path: 'yolo_probe.jpg' });
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: lern });
    return r.fulfill(json(stand)); });
  await pg.route('**/<IP-des-Jetson>:8096/**', r => r.fulfill(json(stand.yolo)));
  await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.waitForTimeout(1500);
  const vorher = await pg.evaluate(() => document.getElementById('lrahmen').getAttribute('src') || '');
  await pg.click('nav button[data-r=lernen]'); await pg.waitForTimeout(4000);
  const f = pg.frames().find(x => /8095\/lernen/.test(x.url()));
  const innen = f ? await f.evaluate(() => ({ titel: document.title, bilder: document.querySelectorAll('#liste div').length, info: (document.getElementById('info') || {}).textContent || '' })) : null;
  const da1 = await pg.evaluate(() => ({ src: document.getElementById('lrahmen').getAttribute('src') || '', stand: document.getElementById('lstand').textContent, lampe: document.getElementById('llampe').className, seite: (document.querySelector('header small').textContent.match(/Seite (1\.\d+)/) || [])[1] }));
  await pg.screenshot({ path: 'lernreiter_da.png' });
  // Fall 2: Jetson weg, neue Seite
  da = false; await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.click('nav button[data-r=lernen]'); await pg.waitForTimeout(4500);
  const weg = await pg.evaluate(() => ({ src: document.getElementById('lrahmen').getAttribute('src') || '', stand: document.getElementById('lstand').textContent, lampe: document.getElementById('llampe').className }));
  await pg.screenshot({ path: 'lernreiter_weg.png' });
  const urteil = { seite131: da1.seite === '1.31', vorherLeer: vorher === '', srcGesetzt: /8095\/lernen$/.test(da1.src), rahmenGeladen: !!innen && /Lernbilder bewerten 1\.5/.test(innen.titel), listeDrin: !!innen && innen.bilder === 1 /* Filter "offen": von zwei Eintraegen ist einer offen */, lampeAn: /\ban\b/.test(da1.lampe),
    wegKeinSrc: weg.src === '', wegHinweis: /nicht erreichbar/.test(weg.stand), wegLampeAus: !/\ban\b/.test(weg.lampe), keineSeitenfehler: fehler.length === 0 };
  console.log('LERNJSON ' + JSON.stringify({ da1, innen, weg, urteil, fehler, bestanden: Object.values(urteil).every(Boolean) }));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
