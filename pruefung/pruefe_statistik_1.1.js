// pruefe_statistik_1.1.js (06.11.2026, 17:08) -- Seite 1.30 im echten Browser: YOLO-Livedienst (:8096) NICHT erreichbar, Jetson-Dienst meldet
// training.laeuft -> Reiter Statistik und Jetson-Block muessen "Training läuft seit 16:40:00" sagen, Lampe aus, kein Strombild; danach kommt
// :8096 zurueck -> Zustand "laeuft" und Lampe an. Aufruf: NODE_PATH=/tmp/node_modules CHROME=... node pruefe_statistik_1.1.js (stub8090.py laeuft).
const { chromium } = require('playwright');
const yolo = { fassung: '1.3', modell: 'best.pt', phase: 'laeuft', tiere: 2, tiere_mittel_5s: 1.8, bewegt: 1, ruhend: 1, koerner: 0, groesse_mm_median: 0.93, tempo_mm_s_median: 1.7, bilder_s: 29.0, verarbeitet_s: 24.5, laeuft_min: 0.4, fehler: null,
  zaehler: { stunden: [], laufend: { uhr: '2026-11-06T16:00', hoechstens: 3, summe: 1200, bilder: 1000 } } };
const stand = { fassung: '1.10', auftrag: 'wartet', letzter_rsync: '16:40:00', neue_saetze: 1, letzter_fehler: null, saetze: 1700, cpu: 10, gpu: 90, ram: '5.0/7.4 GB', temp: 52, platte_frei_gb: 20, laeuft_min: 7,
  statistik: { bahnen: 1900, laenge_um_median: 950, tempo_mm_s_median: 1.9, tiere_je_bild: 0.48, stand: '06.11.2026 16:35' }, live: { verbunden: true, bilder_je_s: 30, mbit_je_s: 11, letztes_bild_vor_s: 0.1, abgeschnitten: 0 },
  training: { angefordert: '2026-11-06 16:39:50', gestartet: '2026-11-06 16:40:00', laeuft: true, letzte_runde: null }, yolo: { phase: 'pausiert: Training laeuft', fehler: null, uhr: '16:41:00' } };
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(e.message)); pg.on('console', m => { if (m.type() === 'error') fehler.push(m.text()); });
  let ausfall = true;
  await pg.route('**/<IP-des-Jetson>:8095/**', r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(stand) }));
  await pg.route('**/<IP-des-Jetson>:8096/**', r => ausfall ? r.abort('connectionrefused') : r.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(yolo) }));
  await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.click('nav button[data-r=statistik]'); await pg.waitForTimeout(9000);
  const lese = () => pg.evaluate(() => ({ lampe: document.getElementById('ylampe').className, zustand: document.getElementById('yzustand').textContent, strom: document.getElementById('ystrom').getAttribute('src') || '', jyolo: document.getElementById('jyolo').textContent, seite: (document.querySelector('header small').textContent.match(/Seite (1\.\d+)/) || [])[1] }));
  const pause = await lese(); await pg.screenshot({ path: 'statistik_pause.png' });
  ausfall = false; stand.training.laeuft = false; stand.yolo = yolo; await pg.waitForTimeout(5000); const danach = await lese(); await pg.screenshot({ path: 'statistik_danach.png' });
  const urteil = { seite130: pause.seite === '1.30', pauseText: /Training läuft seit 16:40:00/.test(pause.zustand), pauseLampeAus: !/\ban\b/.test(pause.lampe), pauseKeinStrom: pause.strom === '', pauseJetsonBlock: /Training läuft seit 16:40:00/.test(pause.jyolo),
    danachLaeuft: /Dienst 1\.3 .*laeuft/.test(danach.zustand), danachLampeAn: /\ban\b/.test(danach.lampe), danachStrom: /8096\/strom/.test(danach.strom), keineFehler: fehler.length === 0 };
  console.log('STATJSON ' + JSON.stringify({ pause, danach, urteil, fehler, bestanden: Object.values(urteil).every(Boolean) }));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
