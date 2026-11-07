// pruefe_jetsonblock.js 1.2 (YOLO-Zeile) -- Knopfprobe der Seite mit ANWESENDEM Jetson: Antworten von <IP-des-Jetson>:8095 werden im Browser
// durch einen Stellvertreter (Dienst 1.4 mit Livestrom) ersetzt; geprueft werden Lampe gruen, Verbindungszeile, Livestrom-Zeile.
const { chromium } = require('playwright');
const stand = { fassung: '1.4', auftrag: 'Statistik (Vermessung)', letzter_rsync: '12:11:00', neue_saetze: 3, letzter_fehler: null, saetze: 650, cpu: 17, gpu: 0,
  ram: '3.7/7.4 GB', temp: 51.9, platte_frei_gb: 27, laeuft_min: 3.2, statistik: { bahnen: 1102, laenge_um_median: 946, tempo_mm_s_median: 1.84, tiere_je_bild: 0.48 },
  verfolgung: { getroffen_prozent: 93, wechsel_prozent: 0.1 }, live: { verbunden: true, pi: 'mikroskop', bilder_je_s: 29.0, mbit_je_s: 10.61, letztes_bild_vor_s: 0.1, abgeschnitten: 0, fehler: null },
  pi_live: { fassung: '1.4', bilder_s: 28.9, kaputt: 0 }, yolo: { fassung: '1.1', modell: 'best.pt', phase: 'laeuft', tiere: 2, tiere_mittel_5s: 1.8, bewegt: 1, ruhend: 1, koerner: 0, groesse_mm_median: 0.93, tempo_mm_s_median: 1.7, bilder_s: 29.0, verarbeitet_s: 24.5 } };
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage();
  await pg.route('**/<IP-des-Jetson>:8095/**', route => route.fulfill({ status: 200, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(stand) }));
  await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.waitForTimeout(6000);
  await pg.locator('#jetsonblock').screenshot({ path: 'jetsonblock.png' });   // 1.1: Bildschirmfoto des Blocks zum Ansehen
  console.log('P15JSON ' + JSON.stringify(await pg.evaluate(() => ({ lampe: document.getElementById('jlampe').className, verb: document.getElementById('jverb').textContent,
    live: document.getElementById('jlive').textContent, yolo: document.getElementById('jyolo').textContent, stat: document.getElementById('jstat').textContent, bild: document.getElementById('bild').naturalWidth }))));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
