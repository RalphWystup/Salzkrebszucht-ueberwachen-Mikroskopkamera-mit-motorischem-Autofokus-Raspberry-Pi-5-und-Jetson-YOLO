// pruefe_piseite_platz_1.0.js (07.11.2026) -- Platzprobe der PI-SEITE. Sein Wort zum Reiter Statistik:
// "Tiere je Stunde (YOLO) das auch rechts, das ist immer platz frei und ich will nicht nach unter scrollen,
// sieh dir das an und nutze die flaeche besser damit man nicht rauf und runter schrollen muss!"
// und zum Reiter Lernen: "immer noch nicht nach rechts beim reiter lernen!"
// Geprueft wird die LAGE der Teile bei 1920x1080 und 1600x900, mit einem Stellvertreter fuer den Jetson.
//   node pruefe_piseite_platz_1.0.js ../../seite_1.34.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../../seite_1.34.html';
const html = fs.readFileSync(SEITE, 'utf8');
const M = '../medien/';
const STAND8095 = { fassung:'1.12', laeuft_min: 120, platte_frei_gb: 16, cpu: 18, gpu: 20, ram:'2.0/7.4 GB', temp: 54,
  statistik:{saetze:6400,bahnen:13000,laenge_um_median:1009,tempo_mm_s_median:1.9,tiere_je_bild:0.52},
  verfolgung:{getroffen_prozent:88,wechsel_prozent:0.3}, yolo:{phase:'laeuft',modell:'best.pt',bilder_s:28.8,tiere:2},
  training:{laeuft:false,gestartet:'2026-11-06 16:42:54',letzte_runde:{uhr:'2026-11-06 16:42:54'}} };
const STAND8096 = { fassung:'1.3', modell:'best.pt', phase:'laeuft', tiere:2, tiere_mittel_5s:1.4, bewegt:1, ruhend:1,
  koerner:0, groesse_mm_median:1.02, tempo_mm_s_median:1.6, bilder_s:28.8, massstab_um_px:10.55,
  zaehler:{ stunden:[{uhr:'2026-11-07T08:00',hoechstens:3,mittel:0.05,bilder:103054},{uhr:'2026-11-07T09:00',hoechstens:3,mittel:0.06,bilder:102759}], laufend:{uhr:'2026-11-07T10:00',hoechstens:2,summe:1533,bilder:91109} } };
function kurve(n, von, bis){ return Array.from({length:n}, (_,i)=>({epoche:i+1, mAP50: von + (bis-von)*i/(n-1), mAP50_95: (von+(bis-von)*i/(n-1))*0.6, genauigkeit:0.7, trefferquote:0.6 })); }
const VERLAUF = { laeuft:false, modell:{mAP50:0.526, uhr:'2026-11-06 16:46:00'},
  runden:[{uhr:'2026-11-06 16:42:54', datensatz:{train:44, val:8}}, {uhr:'2026-11-07 12:00:00', datensatz:{train:160, val:28}}],
  laeufe:[{lauf:'lauf_1642', epochen:40, uhr:'2026-11-06 16:46', mAP50:0.526, mAP50_95:0.31, kurve:kurve(40,0.02,0.526)},
          {lauf:'lauf_1205', epochen:40, uhr:'2026-11-07 12:09', mAP50:0.712, mAP50_95:0.44, kurve:kurve(40,0.10,0.712)}] };

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME }); const P = [];
  for (const g of [{w:1920,h:1080},{w:1600,h:900}]) {
    const pg = await b.newPage({ viewport:{width:g.w,height:g.h} });
    const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
    await pg.route('**/*', async r => { const u = r.request().url();
      if (/8096\/stand/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STAND8096)});
      if (/8096\/strom/.test(u)) return r.fulfill({status:200,contentType:'image/jpeg',path:M+'20261106_100110_b235.jpg'});
      if (/8095\/yolo\/verlauf/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(VERLAUF)});
      if (/8095\/stand/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(STAND8095)});
      if (/8095\/lernen/.test(u)) return r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:'<!doctype html><title>Lernseite</title><body style="font:14px system-ui">Lernseite (Stellvertreter)'});
      if (/\/seite$/.test(u)) return r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:html});
      if (/8090\//.test(u)) return r.fulfill({status:200,contentType:'application/json',body:'{}'});
      return r.fulfill({status:404,body:''}); });
    await pg.goto('http://127.0.0.1:8090/seite', {waitUntil:'load'}); await pg.waitForTimeout(800);

    // Reiter Statistik
    await pg.click('nav button[data-r="statistik"]'); await pg.waitForTimeout(1500);
    const s = await pg.evaluate(() => { const r=i=>{const e=document.getElementById(i); if(!e) return null; const b=e.getBoundingClientRect();
        return {x:Math.round(b.x),y:Math.round(b.y),r:Math.round(b.right),u:Math.round(b.bottom),w:Math.round(b.width),h:Math.round(b.height)};};
      return {tab:r('ystunden'), kurve:r('ykurve'), bild:r('ystrom'), melder:r('melder'), kurvetext:(document.getElementById('ykurvetext')||{}).textContent||'',
        hoehe:document.documentElement.scrollHeight, fenster:window.innerHeight,
        gemalt:(()=>{const c=document.getElementById('ykurve'); if(!c) return null; const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
          let n=0; for(let i=0;i<d.length;i+=400) if(d[i]!==255||d[i+1]!==255||d[i+2]!==255) n++; return n;})()}; });
    // 1.1 (07.11.2026): "rechts" heisst rechts DANEBEN -- die x-Lage allein genuegt nicht. Die erste Fassung
    // dieser Probe bestand, obwohl die Tafel UNTER dem Bild stand und nur rechtsbuendig sass.
    const daneben = !!(s.tab && s.bild && s.tab.x >= s.bild.r - 4 && s.tab.y < s.bild.u - 20);
    P.push({n:`${g.w}x${g.h} Statistik: Stundentafel rechts NEBEN dem Bild`, ok: daneben,
      txt: s.tab ? `Tafel x=${s.tab.x} y=${s.tab.y}; Livebild endet x=${s.bild && s.bild.r} y=${s.bild && s.bild.u}` + (daneben ? '' : ' -- steht DARUNTER') : 'Tafel nicht gefunden'});
    P.push({n:`${g.w}x${g.h} Statistik: Lernkurve vorhanden`, ok: !!(s.kurve && s.kurve.w > 200), txt: s.kurve ? `${s.kurve.w} x ${s.kurve.h}` : 'fehlt'});
    // 1.2: #melder schwebt fest am rechten Rand -- er darf die Kurve nicht verdecken
    const frei = !(s.melder && s.kurve) || s.melder.x >= s.kurve.r - 2 || s.melder.u < s.kurve.y || s.melder.y > s.kurve.u;
    P.push({n:`${g.w}x${g.h} Melder verdeckt die Kurve nicht`, ok: frei,
      txt: s.melder ? `Melder x=${s.melder.x}..${s.melder.r}, Kurve endet x=${s.kurve && s.kurve.r}` : 'kein Melder'});
    P.push({n:`${g.w}x${g.h} Lernkurve ist wirklich gezeichnet`, ok: !!(s.kurve && s.kurve.w > 200) && (s.gemalt||0) > 50, txt: `${s.gemalt} gefärbte Stichproben; ${s.kurvetext.slice(0,70)}`});
    P.push({n:`${g.w}x${g.h} Statistik ohne langes Scrollen`, ok: s.hoehe <= s.fenster*1.35,
      txt: `Seitenhöhe ${s.hoehe}, Fenster ${s.fenster}`});

    // Reiter Lernen
    await pg.click('nav button[data-r="lernen"]'); await pg.waitForTimeout(1500);
    const l = await pg.evaluate(() => { const e=document.getElementById('lrahmen'); const b=e.getBoundingClientRect();
      return {w:Math.round(b.width), h:Math.round(b.height), src:e.getAttribute('src')||'', fenster:window.innerHeight}; });
    P.push({n:`${g.w}x${g.h} Lernreiter: Rahmen nutzt die Breite`, ok: l.w > 1100, txt:`${l.w} px breit (vorher auf 960 begrenzt)`});
    P.push({n:`${g.w}x${g.h} Lernreiter: Rahmen nutzt die Höhe`, ok: l.h >= Math.min(520, l.fenster-260), txt:`${l.h} px hoch bei Fenster ${l.fenster}`});
    if (g.w===1920) await pg.screenshot({path:'../medien/piseite_statistik.png'});
    if (fehler.length) P.push({n:`${g.w}x${g.h} keine Seitenfehler`, ok:false, txt:fehler.join(' | ').slice(0,120)});
    await pg.close();
  }
  const n_ok = P.filter(x=>x.ok).length;
  console.log(`\n===== PI-SEITEN-PLATZPROBE ${SEITE}   ${n_ok} von ${P.length} bestanden`);
  for (const x of P) console.log(`  ${x.ok?'JA  ':'NEIN'} ${x.n.padEnd(52)} ${x.txt}`);
  await b.close(); process.exit(n_ok===P.length?0:1);
})().catch(e=>{console.log('ABBRUCH '+e.message);process.exit(2);});
