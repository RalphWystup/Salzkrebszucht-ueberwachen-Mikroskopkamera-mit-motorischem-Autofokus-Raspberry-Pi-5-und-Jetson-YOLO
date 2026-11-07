// pruefe_lernseite_reiter_1.0.js (07.11.2026) -- Sein Wort: "immer noch nicht nach rechts beim reiter lernen!"
// und "immer wenn ich rahmen stimm...weiter druecke springt das bild nach unten".
// Die Lernseite laeuft bei ihm NICHT allein, sondern im Reiter "Lernen" der Pi-Seite: in einem Rahmen,
// dessen Umgebung auf 960 px Breite begrenzt ist (.text{max-width:960px}) und der nur 80vh hoch ist.
// Diese Probe baut genau das nach und misst darin:
//   steht die Bilderliste rechts vom Bild?   springt beim Weiterschalten etwas?
//   node pruefe_lernseite_reiter_1.0.js ../lernen_1.9.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.9.html'; const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const stand = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const N = ['20261106_100110_b235','20261106_100410_b164','20261106_100410_b39','20261106_100510_b133'];
const BILD = {}, BOX = {}; for (const n of N) { BILD[n] = M + n + '.jpg'; BOX[n] = fs.readFileSync(M + 'lernen_boxen_' + n + '.json','utf8'); }
const STAND = { yolo:{phase:'laeuft',modell:'best.pt',bilder_s:28.8,tiere:2,tiere_mittel_5s:1.4},
  training:{laeuft:false,gestartet:'2026-11-06 16:42:54',letzte_runde:{uhr:'2026-11-06 16:42:54'}} };
// Aussenseite wie der Reiter "Lernen" der Pi-Seite 1.33
const AUSSEN = `<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Mikroskop</title><style>
body{font-family:system-ui,sans-serif;margin:0;background:#f5f4f0}
nav{display:flex;gap:6px;padding:8px 16px 0;border-bottom:1.5px solid #ccc;flex-wrap:wrap}
nav button{font:inherit;padding:7px 14px;border:1px solid #ccc;border-bottom:none;border-radius:8px 8px 0 0;background:#ebe9e3}
section{padding:14px 16px}
.text{max-width:960px}
.text h2{font-size:17px;margin:18px 0 6px}
</style></head><body>
<nav><button>Bedienen</button><button>Statistik</button><button class="an">Lernen</button><button>Hardware</button></nav>
<section><div class="text"><h2>Lernbilder bewerten — die Lernseite des Jetson</h2>
<p>Die Lernseite läuft auf dem Jetson und wird hier erst geladen, wenn dieser Reiter offen ist.</p>
<iframe id="lrahmen" src="http://127.0.0.1:8095/lernen" style="width:100%;height:80vh;border:1px solid #ccc;background:#fff;margin-top:8px"></iframe>
</div></section></body></html>`;

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  await pg.route('**/*', async r => { const u = r.request().url(), m = r.request().method();
    if (/\/aussen$/.test(u)) return r.fulfill({ status:200, contentType:'text/html; charset=utf-8', body: AUSSEN });
    if (/\/stand/.test(u) && !/\/lernen/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(STAND) });
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify(stand) });
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { if (m === 'POST') { const d = JSON.parse(r.request().postData()||'{}');
        const e = stand.find(x => x.name === mb[1]); if (e) e.status = d.status;
        return r.fulfill({ status:200, contentType:'application/json', body: JSON.stringify({ok:true,name:mb[1],status:d.status,n_boxen:(d.boxen||[]).length}) }); }
      return r.fulfill({ status:200, contentType:'application/json', body: BOX[mb[1]] || BOX[N[0]] }); }
    const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/);
    if (mi) return r.fulfill({ status:200, contentType:'image/jpeg', path: BILD[mi[1]] || BILD[N[0]] });
    if (/\/lernen$/.test(u)) return r.fulfill({ status:200, contentType:'text/html; charset=utf-8', body: html });
    return r.fulfill({ status:404, body:'' }); });

  await pg.goto('http://127.0.0.1:8095/aussen', { waitUntil:'load' }); await pg.waitForTimeout(2200);
  const P = [];
  const rahmen = pg.frames().find(f => /\/lernen$/.test(f.url()));
  if (!rahmen) { console.log('ABBRUCH: Rahmen nicht gefunden'); await b.close(); process.exit(2); }
  const rbreite = await pg.evaluate(() => Math.round(document.getElementById('lrahmen').getBoundingClientRect().width));
  P.push({ n: 'R0 Rahmen ist so schmal wie im Reiter', ok: rbreite <= 980 && rbreite >= 700, txt: `${rbreite} px breit (die Pi-Seite begrenzt auf 960)` });

  const lage = () => rahmen.evaluate(() => { const r = i => { const e = document.getElementById(i); if (!e) return null;
      const b = e.getBoundingClientRect(); return { x:Math.round(b.x), y:Math.round(b.y), r:Math.round(b.right), u:Math.round(b.bottom), w:Math.round(b.width), h:Math.round(b.height) }; };
    return { leinwand:r('leinwand'), seite:r('seite'), liste:r('liste'), breit:document.body.classList.contains('breit'),
      innenScroll:window.scrollY, innenHoehe:document.documentElement.scrollHeight, fenster:window.innerHeight,
      aktiv:(document.querySelector('#liste div.aktiv')||{}).textContent||'' }; });
  const m = await lage();
  P.push({ n: 'R1 Seite erkennt den Platz als breit', ok: m.breit, txt: m.breit ? 'zweispaltig' : 'einspaltig (Liste unter dem Bild)' });
  const neben = m.seite && m.leinwand && m.seite.x >= m.leinwand.r - 2 && m.seite.y < m.leinwand.u;
  P.push({ n: 'R2 Bilderliste RECHTS vom Bild', ok: !!neben,
    txt: neben ? `Liste beginnt bei x=${m.seite.x}, Bild endet bei x=${m.leinwand.r}` : `Liste bei x=${m.seite&&m.seite.x}, y=${m.seite&&m.seite.y}; Bild endet y=${m.leinwand&&m.leinwand.u} -- DARUNTER` });
  P.push({ n: 'R3 im Rahmen wird nicht gescrollt', ok: m.innenHoehe <= m.fenster + 2,
    txt: `Inhalt ${m.innenHoehe} px, Rahmen ${m.fenster} px` });

  // Weiterschalten: nichts darf springen -- weder aussen noch innen
  const aussenVor = await pg.evaluate(() => window.scrollY);
  await pg.evaluate(() => window.scrollTo(0, 0)); await pg.waitForTimeout(200);
  const vorAktiv = (await lage()).aktiv;
  await rahmen.click('#richtig'); await pg.waitForTimeout(1200);
  const n2 = await lage(); const aussenNach = await pg.evaluate(() => window.scrollY);
  P.push({ n: 'R4 Weiterschalten blaettert wirklich', ok: n2.aktiv !== vorAktiv, txt: `${vorAktiv.trim().slice(0,24)} -> ${n2.aktiv.trim().slice(0,24)}` });
  P.push({ n: 'R5 aeussere Seite springt NICHT', ok: aussenNach === 0, txt: aussenNach === 0 ? 'bleibt stehen' : `springt auf ${aussenNach} px` });
  P.push({ n: 'R6 Seite im Rahmen springt NICHT', ok: n2.innenScroll === 0, txt: n2.innenScroll === 0 ? 'bleibt stehen' : `springt auf ${n2.innenScroll} px` });
  for (let i = 0; i < 3; i++) { await rahmen.click('#richtig'); await pg.waitForTimeout(700); }
  const n3 = await lage(); const a3 = await pg.evaluate(() => window.scrollY);
  P.push({ n: 'R7 auch nach vier Durchgaengen kein Sprung', ok: a3 === 0 && n3.innenScroll === 0, txt: `aussen ${a3} px, innen ${n3.innenScroll} px` });

  await pg.screenshot({ path: '../medien/reiter_lernen.png' });
  const n_ok = P.filter(x => x.ok).length;
  console.log(`\n===== REITERPROBE ${SEITE}   ${n_ok} von ${P.length} bestanden`);
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.n.padEnd(44)} ${x.txt}`);
  if (fehler.length) console.log('  Seitenfehler: ' + fehler.join(' | '));
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
