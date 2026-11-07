// pruefe_lernseite_stabil_1.0.js (07.11.2026) -- Instabilitaetsproben der Lernseite, sein Wort: "pruefe bitte
// auf instabilitaeten und versuche diese dann zu beseitigen". Vier Faelle, die im Laborbetrieb wirklich
// vorkommen: das Bild kommt nicht an, zwei schnelle Klicks auf Speichern, die Liste kommt nicht an, und
// Umschalten waehrend noch geladen wird. Gemessen wird, was die Seite danach anzeigt und tut.
//   node pruefe_lernseite_stabil_1.0.js ../lernen_1.6.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.6.html'; const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const listeRoh = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const boxen = fs.readFileSync(M + 'lernen_boxen_20261106_100110_b185.json', 'utf8');
const BILD = M + '20261106_100110_b185.jpg';

async function seite(b, opt) {
  const pg = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const posts = []; const fehler = []; const stand = JSON.parse(JSON.stringify(listeRoh));
  pg.on('pageerror', e => fehler.push(String(e.message)));
  await pg.route('**/*', async r => {
    const u = r.request().url(), m = r.request().method();
    if (/\/lernen\/liste/.test(u)) { if (opt.listeKaputt) return r.abort('failed');
      return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(stand) }); }
    if (/\/lernen\/fertig/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true,"uhr":"11:40:00"}' });
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { if (m === 'POST') { const d = JSON.parse(r.request().postData() || '{}'); posts.push({ name: mb[1], status: d.status });
        if (opt.langsamSpeichern) await new Promise(s => setTimeout(s, 400));
        const e = stand.find(x => x.name === mb[1]); if (e) e.status = d.status;
        return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, name: mb[1], status: d.status, n_boxen: (d.boxen||[]).length }) }); }
      if (opt.langsamBoxen) await new Promise(s => setTimeout(s, 500));
      return r.fulfill({ status: 200, contentType: 'application/json', body: boxen }); }
    if (/\/lernen\/bild\//.test(u)) { if (opt.bildKaputt) return r.fulfill({ status: 404, body: '' });
      return r.fulfill({ status: 200, contentType: 'image/jpeg', path: BILD }); }
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html });
    return r.fulfill({ status: 404, body: '' }); });
  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil: 'load' }); await pg.waitForTimeout(1300);
  return { pg, posts, fehler };
}

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME }); const P = [];

  // S1: Bild kommt nicht an -> darf nicht das vorige Bild stehen lassen und muss das Bewerten sperren
  { const { pg } = await seite(b, {});
    await pg.selectOption('#filter', 'zurueckgestellt').catch(()=>{}); await pg.waitForTimeout(500);
    await pg.click('#liste div:nth-child(1)'); await pg.waitForTimeout(600);
    const vorher = await pg.evaluate(() => document.getElementById('leinwand').toDataURL().length);
    await pg.route('**/lernen/bild/**', r => r.fulfill({ status: 404, body: '' }));
    await pg.click('#weiter'); await pg.waitForTimeout(900);
    const z = await pg.evaluate(() => ({ laenge: document.getElementById('leinwand').toDataURL().length,
      richtig_aus: document.getElementById('richtig').disabled, info: document.getElementById('info').textContent.slice(0,70) }));
    P.push({ name: 'S1 Bild kommt nicht an', ok: z.richtig_aus === true && z.laenge !== vorher,
      grund: `Leinwand ${z.laenge !== vorher ? 'geaendert' : 'UNVERAENDERT (altes Bild steht noch)'}, Speichern ${z.richtig_aus ? 'gesperrt' : 'WEITER MOEGLICH'}` });
    await pg.close(); }

  // S2: zwei schnelle Klicks auf Speichern -> genau EIN Speichervorgang
  { const { pg, posts } = await seite(b, { langsamSpeichern: true });
    await pg.selectOption('#filter', 'zurueckgestellt').catch(()=>{}); await pg.waitForTimeout(400);
    await pg.click('#liste div:nth-child(1)'); await pg.waitForTimeout(600);
    const n0 = posts.length;
    await pg.evaluate(() => { const b = document.getElementById('richtig'); b.click(); b.click(); b.click(); });
    await pg.waitForTimeout(1600);
    const n = posts.length - n0;
    P.push({ name: 'S2 Dreifachklick auf Speichern', ok: n === 1, grund: `${n} Speichervorgaenge ausgeloest (genau 1 ist richtig)` });
    await pg.close(); }

  // S3: Liste kommt nicht an -> sichtbare Meldung, nicht nur eine leere Seite
  { const { pg } = await seite(b, { listeKaputt: true });
    const z = await pg.evaluate(() => ({ info: (document.getElementById('info')||{}).textContent || '',
      nochmal: !!document.getElementById('nochmal'), eintraege: document.querySelectorAll('#liste div').length }));
    P.push({ name: 'S3 Liste kommt nicht an', ok: /nicht an|kam nicht|Fehler/i.test(z.info) && z.nochmal,
      grund: z.info ? `meldet: "${z.info.slice(0,60)}"` + (z.nochmal ? ' mit Wiederholknopf' : ' OHNE Wiederholknopf') : 'die Seite schweigt' });
    await pg.close(); }

  // S4: waehrend ein Bild laedt die Auswahl umschalten -> angezeigter Name und aktiver Eintrag muessen passen
  { const { pg } = await seite(b, { langsamBoxen: true });
    await pg.selectOption('#filter', 'zurueckgestellt').catch(()=>{}); await pg.waitForTimeout(900);
    await pg.evaluate(() => { const d = document.querySelectorAll('#liste div'); if (d[5]) d[5].click(); });
    await pg.waitForTimeout(80);
    await pg.selectOption('#filter', 'geprueft').catch(()=>{});
    await pg.waitForTimeout(2200);
    const z = await pg.evaluate(() => ({ info: (document.getElementById('info')||{}).textContent || '',
      aktiv: (document.querySelector('#liste div.aktiv')||{}).textContent || '', filter: document.getElementById('filter').value }));
    const name = (z.info.match(/^(\S+)/) || [])[1] || '';
    const passt = !!name && z.aktiv.includes(name);
    P.push({ name: 'S4 Umschalten waehrend des Ladens', ok: passt,
      grund: passt ? `Anzeige und Liste zeigen dasselbe Bild (${name})` : `Anzeige "${name}" passt nicht zum aktiven Eintrag "${z.aktiv.trim()}"` });
    await pg.close(); }

  const n_ok = P.filter(x => x.ok).length;
  console.log('\n===== INSTABILITAETSPROBE ' + SEITE + '   ' + n_ok + ' von ' + P.length + ' bestanden');
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.name.padEnd(36)} ${x.grund}`);
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
