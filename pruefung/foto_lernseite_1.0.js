// foto_lernseite_1.0.js (06.11.2026) -- Bildschirmfoto der echten Lernseite (lernen_1.5.html) mit echten Daten vom Jetson (Liste, Rahmen-JSON und
// Lernbild aus medien/), ohne Jetson-Verbindung: alle Abrufe werden aus den geholten Dateien beantwortet. Zeigt das Bild 20261106_111540_b55 (7 Rahmen).
const { chromium } = require('playwright'); const fs = require('fs');
const M = '../medien/'; const lern = fs.readFileSync('../lernen_1.5.html', 'utf8');
const liste = JSON.parse(fs.readFileSync(M + 'lernen_liste.json', 'utf8')); const boxen = fs.readFileSync(M + 'lernen_boxen_20261106_111540_b55.json', 'utf8');
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage({ viewport: { width: 1500, height: 1120 }, deviceScaleFactor: 1 });
  const fehler = []; pg.on('pageerror', e => fehler.push(e.message));
  await pg.route('**/*', r => { const u = r.request().url();
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(liste) });
    if (/\/lernen\/boxen\//.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: boxen });
    if (/\/lernen\/bild\//.test(u)) return r.fulfill({ status: 200, contentType: 'image/jpeg', path: M + '20261106_111540_b55.jpg' });
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: lern });
    return r.fulfill({ status: 404, body: '' }); });
  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil: 'load' }); await pg.waitForTimeout(1500);
  await pg.selectOption('#filter', 'geprueft').catch(() => {}); await pg.waitForTimeout(500);
  const ok = await pg.evaluate(() => { const d = [...document.querySelectorAll('#liste div')].find(x => /111540_b55/.test(x.textContent)); if (d) { d.click(); return true; } return false; });
  await pg.waitForTimeout(1500);
  const info = await pg.evaluate(() => ({ titel: document.title, info: (document.getElementById('info') || {}).textContent || '', stand: (document.getElementById('stand') || {}).textContent || '' }));
  await pg.screenshot({ path: '../medien/lernseite_foto.png' });
  console.log('FOTOJSON ' + JSON.stringify({ geklickt: ok, info, fehler }));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
