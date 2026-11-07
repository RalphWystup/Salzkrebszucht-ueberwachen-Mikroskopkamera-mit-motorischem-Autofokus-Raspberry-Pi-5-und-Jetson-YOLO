// pruefe_lernseite_platz_1.0.js (07.11.2026) -- Sein Wort: "neben das bild sonst muss man immer scrolen,
// bitte aendern". Diese Probe misst die LAGE der Teile bei verschiedenen Bildschirmgroessen:
//   steht die rechte Spalte (Hilfe + Bilderliste) wirklich NEBEN der Leinwand?
//   ist die Bilderliste ohne Scrollen zu sehen?
//   passt die ganze Seite ohne senkrechtes Scrollen?
// Bei schmalem Fenster (unter 1000 px) ist ein Umbruch nach unten richtig und wird auch so geprueft.
//   node pruefe_lernseite_platz_1.0.js ../lernen_1.8.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.8.html'; const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const stand = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const N = ['20261106_100110_b235','20261106_100410_b164','20261106_100410_b39','20261106_100510_b133'];
const BILD = {}, BOX = {}; for (const n of N) { BILD[n] = M + n + '.jpg'; BOX[n] = fs.readFileSync(M + 'lernen_boxen_' + n + '.json','utf8'); }
const STAND = { yolo:{phase:'laeuft',modell:'best.pt',bilder_s:28.8,tiere:2,tiere_mittel_5s:1.4},
  training:{laeuft:false,gestartet:'2026-11-06 16:42:54',letzte_runde:{uhr:'2026-11-06 16:42:54'}} };
// 1.9: die Umschaltung liegt bei 820 px -- damit die Seite auch im Reiter "Lernen" (Rahmen 960 px) zweispaltig ist.
const GROESSEN = [{w:1920,h:1080,name:'1920x1080'},{w:1600,h:900,name:'1600x900'},{w:1366,h:768,name:'1366x768'},
                  {w:960,h:860,name:'960x860 (Reiter)'},{w:700,h:800,name:'700x800 (schmal)'}];

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME }); const P = [];
  for (const g of GROESSEN) {
    const pg = await b.newPage({ viewport: { width: g.w, height: g.h } });
    await pg.route('**/*', async r => { const u = r.request().url();
      if (/\/stand/.test(u) && !/\/lernen/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(STAND) });
      if (/\/lernen\/liste/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(stand) });
      const mb = u.match(/\/lernen\/boxen\/([^?]+)/); if (mb) return r.fulfill({ status:200, contentType:'application/json', body: BOX[mb[1]] || BOX[N[0]] });
      const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/); if (mi) return r.fulfill({ status:200, contentType:'image/jpeg', path: BILD[mi[1]] || BILD[N[0]] });
      if (/\/lernen$/.test(u)) return r.fulfill({ status:200, contentType:'text/html; charset=utf-8', body: html });
      return r.fulfill({ status:404, body:'' }); });
    await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil:'load' }); await pg.waitForTimeout(1500);
    const gesprungen = await pg.evaluate(() => window.scrollY);       // springt die Seite beim Laden selbst nach unten?
    await pg.evaluate(() => window.scrollTo(0, 0)); await pg.waitForTimeout(150);
    const m = await pg.evaluate(() => { const r = i => { const e = document.getElementById(i); if (!e) return null;
        const b = e.getBoundingClientRect(); return { x: Math.round(b.x), y: Math.round(b.y), r: Math.round(b.right), u: Math.round(b.bottom), w: Math.round(b.width), h: Math.round(b.height) }; };
      return { leinwand: r('leinwand'), seite: r('seite'), liste: r('liste'), knopf: r('richtig'),
        hoehe: document.documentElement.scrollHeight, fenster: window.innerHeight, breite: window.innerWidth }; });
    const schmal = g.w < 820;
    const neben = m.seite && m.leinwand && m.seite.x >= m.leinwand.r - 2 && m.seite.y < m.leinwand.u;
    const listeSichtbar = m.liste && m.liste.y < m.fenster - 40;
    const knopfSichtbar = m.knopf && m.knopf.u <= m.fenster;
    const keinScroll = m.hoehe <= m.fenster + 2;
    if (schmal) {
      P.push({ n: `${g.name}: Umbruch nach unten ist richtig`, ok: !neben, txt: `rechte Spalte ${neben ? 'daneben' : 'darunter'} (bei schmalem Fenster gewollt)` });
    } else {
      P.push({ n: `${g.name}: Liste NEBEN dem Bild`, ok: !!neben,
        txt: neben ? `Spalte beginnt bei x=${m.seite.x}, Bild endet bei x=${m.leinwand.r}` : `Spalte bei x=${m.seite && m.seite.x}, y=${m.seite && m.seite.y}; Bild endet x=${m.leinwand.r}, y=${m.leinwand.u} -- UNTER dem Bild` });
      P.push({ n: `${g.name}: Bilderliste ohne Scrollen sichtbar`, ok: !!listeSichtbar,
        txt: `Liste beginnt bei y=${m.liste && m.liste.y}, Fenster ${m.fenster}` });
      P.push({ n: `${g.name}: Knopfreihe ohne Scrollen sichtbar`, ok: !!knopfSichtbar,
        txt: `gruener Knopf endet bei y=${m.knopf && m.knopf.u}, Fenster ${m.fenster}` });
      P.push({ n: `${g.name}: Seite passt ohne senkrechtes Scrollen`, ok: keinScroll,
        txt: `Seitenhoehe ${m.hoehe}, Fenster ${m.fenster}` });
      P.push({ n: `${g.name}: Seite springt beim Laden nicht weg`, ok: gesprungen === 0,
        txt: gesprungen ? `Seite stand nach dem Laden ${gesprungen} px tiefer (die Liste zog sie herunter)` : 'bleibt oben' });
    }
    if (g.w === 1920) await pg.screenshot({ path: '../medien/platz_1920.png' });
    await pg.close();
  }
  const n_ok = P.filter(x => x.ok).length;
  console.log('\n===== PLATZPROBE ' + SEITE + '   ' + n_ok + ' von ' + P.length + ' bestanden');
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.n.padEnd(48)} ${x.txt}`);
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
