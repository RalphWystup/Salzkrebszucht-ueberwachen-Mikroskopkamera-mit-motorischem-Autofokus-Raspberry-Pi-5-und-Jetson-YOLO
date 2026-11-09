// pruefe_lernseite_nachziehen_1.0.js (09.11.2026) -- Knopfprobe Lernseite 1.10: Knopf "100 neue Bilder aus aktuellem Material".
// Stellvertreter fuer den Jetson-Dienst: Liste mit und ohne Marke, /stand mit Nachzieh-Zustand (laeuft -> fertig), POST /lernen/nachziehen.
//   NODE_PATH=/tmp/node_modules node pruefe_lernseite_nachziehen_1.0.js ../lernen_1.10.html
const { chromium } = require('playwright'); const fs = require('fs');
const html = fs.readFileSync(process.argv[2] || '../lernen_1.10.html', 'utf8');
const BILD = Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=', 'base64');
let liste = [ {name:'a_b1', status:'geprueft', n_boxen:2, datensatz:'alt'}, {name:'b_b1', status:'offen', n_boxen:1, datensatz:'alt'},
  {name:'c_b1', status:'offen', n_boxen:3, datensatz:'2026-11-08_1500'} ];
let nz = {laeuft:false, gestartet:null, ende:null, ergebnis:null, fehler:null}; let posts = 0, polls = 0;
(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined }); const P = []; let fehl = 0;
  const E = (ok, t) => { P.push((ok ? 'OK   ' : 'FEHL ') + t); if (!ok) fehl++; };
  const pg = await b.newPage({ viewport:{width:1400,height:900} }); const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  pg.on('dialog', d => d.accept());
  await pg.route('**/*', async r => { const u = r.request().url(), m = r.request().method();
    if (/\/lernen\/nachziehen$/.test(u) && m === 'POST') { posts++; nz = {laeuft:true, gestartet:'2026-11-09 10:30:00', ende:null, ergebnis:null, fehler:null};
      setTimeout(() => { nz = {laeuft:false, gestartet:'2026-11-09 10:30:00', ende:'2026-11-09 10:30:40', fehler:null,
        ergebnis:{neu:100, datensatz:'2026-11-09_1030', gewuenscht:100, saetze_benutzt:61, saetze_mit_video:218, saetze_juenger_h:218, aeltestes_benutzt_h:0.9, schon_vorhanden:0, gesamt:401}};
        for (let i = 0; i < 100; i++) liste.push({name:`n${i}_b${i}`, status:'offen', n_boxen:2, datensatz:'2026-11-09_1030'}); }, 4500);
      return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify({ok:true, gestartet:nz.gestartet, anzahl:100, stunden:6})}); }
    if (/\/stand/.test(u)) { polls++; return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify({fassung:'1.13', training:{laeuft:false}, yolo:{phase:'laeuft', modell:'best.pt', bilder_s:20, tiere:1, tiere_mittel_5s:1}, nachziehen:nz})}); }
    if (/\/lernen\/liste/.test(u)) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(liste)});
    if (/\/lernen\/boxen\//.test(u)) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify({boxen:[{x0:10,y0:10,x1:60,y1:40,klasse:'tier',quelle:'auswertung'}], status:'offen'})});
    if (/\/lernen\/bild\//.test(u)) return r.fulfill({status:200, contentType:'image/jpeg', body:BILD});
    if (/\/lernen$/.test(u)) return r.fulfill({status:200, contentType:'text/html; charset=utf-8', body:html});
    return r.fulfill({status:404, body:''}); });
  await pg.goto('http://127.0.0.1:8095/lernen', {waitUntil:'load'}); await pg.waitForTimeout(1200);
  E(/Seite 1\.10/.test(await pg.$eval('header', h => h.textContent)), 'Kopf nennt Seite 1.10');
  E(await pg.$('#nachziehen') !== null, 'Knopf Nachziehen vorhanden');
  const opt = await pg.$$eval('#filter option', os => os.map(o => [o.value, o.textContent, o.disabled]));
  E(opt.some(o => o[0] === 'neu' && /neueste Runde \(1\)/.test(o[1]) && !o[2]), `Auswahl neueste Runde: ${JSON.stringify(opt.find(o => o[0]==='neu'))}`);
  const zeilen = await pg.$$eval('#liste div', ds => ds.map(d => d.textContent));
  E(zeilen.some(z => /c_b1.*11-08_1500/.test(z)) && zeilen.some(z => /^b_b1\s+\(1\)$/.test(z.trim())), `Listenzeilen tragen die Marke: ${zeilen.join(' | ')}`);
  await pg.click('#nachziehen'); await pg.waitForTimeout(1500);
  E(posts === 1, `POST /lernen/nachziehen gesendet: ${posts}`);
  E(await pg.$eval('#nachziehen', b => b.disabled && /läuft/.test(b.textContent)), 'Knopf gesperrt und beschriftet "läuft" während des Laufs');
  E(/Nachziehen gestartet 10:30:00/.test(await pg.$eval('#gespeichert', e => e.textContent)), `Meldung: "${await pg.$eval('#gespeichert', e => e.textContent)}"`);
  await pg.waitForTimeout(2000);
  E(/Nachziehen läuft/.test(await pg.$eval('#bereit', e => e.textContent)), 'Bereit-Zeile nennt das laufende Nachziehen');
  await pg.waitForTimeout(5500);
  const bil = await pg.$eval('#bilanz', e => e.textContent);
  E(/Runde 2026-11-09_1030:.*100 neue Lernbilder aus 61 Aufnahmen/.test(bil), `Bilanz: "${bil.slice(0, 120)}"`);
  E((await pg.$eval('#filter', f => f.value)) === 'neu', 'Auswahl steht auf "neueste Runde"');
  const sicht = await pg.$$eval('#liste div', ds => ds.map(d => d.textContent));
  E(sicht.length === 100 && sicht.every(z => /11-09_1030/.test(z)), `Liste zeigt nur die neue Runde: ${sicht.length} Zeilen`);
  E(await pg.$eval('#nachziehen', b => !b.disabled && /100 neue Bilder/.test(b.textContent)), 'Knopf wieder frei');
  E(/zuletzt nachgezogen 100 Bilder/.test(await pg.$eval('#bereit', e => e.textContent)), 'Bereit-Zeile nennt die letzte Runde');
  await pg.screenshot({ path: 'lauf/lernseite_1.10_nachziehen.png' });
  E(fehler.length === 0, `Skriptfehler: ${fehler.join(' / ') || 'keine'}`);
  await b.close(); console.log(P.join('\n')); console.log(fehl ? `FEHL: ${fehl}` : 'ALLE PRUEFUNGEN BESTANDEN'); process.exit(fehl ? 1 : 0);
})();
