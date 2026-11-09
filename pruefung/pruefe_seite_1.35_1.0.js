// pruefe_seite_1.35_1.0.js (09.11.2026) -- Knopfprobe der Pi-Seite 1.35 (ohne Wache-Reiter).
// Sein Wort: "dann entferne die wache und den reiter dazu". Geprueft wird im echten Browser (Chromium):
//   1. kein Reiter "Wache", acht Reiter, jeder Reiter zeigt beim Klick seinen Abschnitt
//   2. KEINE Anfrage an Port 8091 in 6 s (auch nicht im Vollbild)
//   3. Kopf nennt "Seite 1.35", meta fassung 1.35
//   4. Vollbild (?vollbild): zweite Zeile zeigt die Auswertung (8092), nicht die Wache
//   5. keine Skriptfehler
//   node pruefe_seite_1.35_1.0.js ../../seite_1.35.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../../seite_1.35.html';
const html = fs.readFileSync(SEITE, 'utf8');
const STAND8092 = { fassung:'1.4_rev2', phase:'wacht', objekte:2, aufnahmen:17, bilder_s:19.7, verworfen:0, warteschlange:0, uebersprungen:751, speicher_mb:271,
  letzte:{uhr:'10:09:40', bilder:130}, zeichnet:false, rest_s:0, bilder:1629, laeuft_min:3 };
const ZAEHLER = { stunden:[{uhr:'2026-11-09T00:00',hoechstens:9,mittel:1.27,bilder:62672},{uhr:'2026-11-09T01:00',hoechstens:7,mittel:1.1,bilder:30000}], laufend:{uhr:'2026-11-09T10:00',hoechstens:3,bilder:522,mittel:0.86}, fassung:'1.4_rev2' };
const PUNKTE = { t: Date.now()/1000, alter_s:0.1, breite:640, hoehe:480, massstab_um_px:null, tiere:[{nr:3,x:300,y:200,rx:280,ry:190,rb:40,rh:20,L:40,B:12,w:10,ruht:false}], erinnert:[], ruhend:[] };
const STATUS8090 = { winkel:154.7, schaerfe:17234, phase:'bereit', max:0, max_winkel:null, lauf:false, fps:28.9, meldungen:['10:09 Probe'], puls:false, ergebnis:'', stromlos:true, kurve:[] };
const STAND8095 = { fassung:'1.12', laeuft_min:120, platte_frei_gb:12, cpu:0, gpu:0, ram:'1.9/7.4 GB', temp:48, statistik:{saetze:11206,bahnen:24135,laenge_um_median:986,tempo_mm_s_median:1.79,tiere_je_bild:0.57}, verfolgung:{getroffen_prozent:89,wechsel_prozent:0.8}, yolo:{phase:'laeuft',modell:'best.pt',bilder_s:0.2,tiere:0}, training:{laeuft:false}, live:{verbunden:true,bilder_je_s:19,mbit_je_s:7} };
const STAND8096 = { fassung:'1.3', modell:'best.pt', phase:'laeuft', tiere:1, tiere_mittel_5s:1, bewegt:1, ruhend:0, koerner:0, groesse_mm_median:1.0, tempo_mm_s_median:1.6, bilder_s:19, massstab_um_px:10.55, zaehler:ZAEHLER };
const BILD = Buffer.from('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=', 'base64');

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME || undefined }); let fehlerGesamt = 0; const P = [];
  for (const vollbild of [false, true]) {
    const pg = await b.newPage({ viewport:{width:1600,height:900} });
    const fehler = [], an8091 = []; pg.on('pageerror', e => fehler.push(String(e.message)));
    await pg.route('**/*', async r => { const u = r.request().url();
      if (/:8091\//.test(u)) { an8091.push(u); return r.fulfill({status:404, body:''}); }
      if (/8092\/stand/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STAND8092)});
      if (/8092\/zaehler/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(ZAEHLER)});
      if (/8092\/punkte/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(PUNKTE)});
      if (/8092\/strom/.test(u) || /8096\/strom/.test(u) || /8090\/strom/.test(u) || /\/bild\.jpg/.test(u)) return r.fulfill({status:200,contentType:'image/jpeg',body:BILD});
      if (/8096\/stand/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STAND8096)});
      if (/8095\/stand/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STAND8095)});
      if (/8095\/yolo\/verlauf/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({laeuft:false,runden:[],laeufe:[]})});
      if (/8095\/lernen/.test(u)) return r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:'<!doctype html><title>Lernseite</title>Stellvertreter'});
      if (/8090\/status/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STATUS8090)});
      if (/8090\/(seite|\?|$)/.test(u) || /8090\/\?vollbild/.test(u)) return r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:html});
      if (/8090\//.test(u)) return r.fulfill({status:200,contentType:'application/json',body:'{}'});
      return r.fulfill({status:404,body:''}); });
    await pg.goto('http://127.0.0.1:8090/' + (vollbild ? '?vollbild' : ''), {waitUntil:'load'});
    await pg.waitForTimeout(vollbild ? 6500 : 1500);
    const E = (bed, text) => { P.push((bed ? 'OK   ' : 'FEHL ') + (vollbild ? '[Vollbild] ' : '[Seite]    ') + text); if (!bed) fehlerGesamt++; };
    if (!vollbild) {
      const knoepfe = await pg.$$eval('nav button', bs => bs.map(x => [x.dataset.r, x.textContent.trim()]));
      E(knoepfe.length === 8 && !knoepfe.some(k => k[0] === 'wache' || /Wache/.test(k[1])), `Reiter: ${knoepfe.map(k=>k[1]).join(' | ')}`);
      E(await pg.$('section#wache') === null, 'kein Abschnitt id=wache');
      for (const [r] of knoepfe) {
        await pg.click(`nav button[data-r="${r}"]`); await pg.waitForTimeout(250);
        const sichtbar = await pg.$$eval('section.an', s => s.map(x => x.id));
        E(sichtbar.length === 1 && sichtbar[0] === r, `Reiter ${r} -> Abschnitt ${sichtbar.join(',') || '(keiner)'}`);
      }
      await pg.click('nav button[data-r="bedienen"]'); await pg.waitForTimeout(5000);
      E(/Seite 1\.35/.test(await pg.$eval('header', h => h.textContent)), 'Kopf nennt Seite 1.35');
      E((await pg.$eval('meta[name="fassung"]', m => m.content)) === '1.35', 'meta fassung 1.35');
      const rs = await pg.$eval('#rahmen_stand', e => e.textContent).catch(() => '');
      E(/Tier/.test(rs) && !/Wache/.test(rs), `Zustandstext Bedienen: "${rs}"`);
      await pg.screenshot({ path: 'lauf/seite_1.35_bedienen.png', clip:{x:0,y:0,width:1600,height:900} });
    } else {
      const vb2 = await pg.$eval('#vb2', e => e.textContent); const vb3 = await pg.$eval('#vb3', e => e.textContent);
      E(/Auswertung 1\.4_rev2/.test(vb2) && /17 Aufnahmen/.test(vb2) && !/Wache/.test(vb2), `Vollbildzeile 2: "${vb2}"`);
      E(/zuletzt 10:09:40/.test(vb3), `Vollbildzeile 3: "${vb3}"`);
      await pg.screenshot({ path: 'lauf/seite_1.35_vollbild.png' });
    }
    E(an8091.length === 0, `Anfragen an Port 8091: ${an8091.length}`);
    E(fehler.length === 0, `Skriptfehler: ${fehler.length ? fehler.join(' / ') : 'keine'}`);
    await pg.close();
  }
  await b.close(); console.log(P.join('\n')); console.log(fehlerGesamt ? `FEHL: ${fehlerGesamt}` : 'ALLE PRUEFUNGEN BESTANDEN'); process.exit(fehlerGesamt ? 1 : 0);
})();
