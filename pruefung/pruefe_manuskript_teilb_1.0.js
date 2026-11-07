// pruefe_manuskript_teilb_1.0.js (06.11.2026) -- Seite 1.32: Reiter "Manuskript: Methoden" zeigt Teil A (Kapitel 1-7) und Teil B (Kapitel 9-18); fehlende Bilder
// (auf dem Pi gibt es bilder/ nicht) blenden ihre Figur still aus; keine Seitenfehler. Bildschirmfoto des Reiters.
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage({ viewport: { width: 1300, height: 1800 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(e.message));
  await pg.route('**/<IP-des-Jetson>:*/**', r => r.abort('connectionrefused'));
  await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.click('nav button[data-r=manuskript]'); await pg.waitForTimeout(2500);
  const d = await pg.evaluate(() => { const s = document.getElementById('manuskript'); const hs = [...s.querySelectorAll('h2')].map(h => h.textContent.trim().slice(0, 40));
    const figs = [...s.querySelectorAll('figure')].map(f => getComputedStyle(f).display); const tabs = s.querySelectorAll('.teilb table').length;
    return { kapitel: hs.length, erste: hs.slice(0, 3), letzte: hs.slice(-3), figuren: figs.length, versteckt: figs.filter(x => x === 'none').length, tabellen: tabs, sichtbar: s.classList.contains('an'), seite: (document.querySelector('header small').textContent.match(/Seite (1\.\d+)/) || [])[1] }; });
  await pg.screenshot({ path: 'manuskript_teilb.png', clip: { x: 0, y: 0, width: 1300, height: 1800 } });
  const urteil = { seite132: d.seite === '1.32', teilAundB: d.kapitel >= 18, tabellenDa: d.tabellen >= 4, figurenVersteckt: d.figuren > 0 && d.versteckt === d.figuren, keineFehler: fehler.length === 0 };
  console.log('MANJSON ' + JSON.stringify({ d, urteil, fehler, bestanden: Object.values(urteil).every(Boolean) }));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
