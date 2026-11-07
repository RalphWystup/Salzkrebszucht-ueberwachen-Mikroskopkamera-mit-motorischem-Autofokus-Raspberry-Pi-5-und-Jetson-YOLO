// pruefe_lernseite_knopf_1.1.js (07.11.2026) -- KNOPFPROBE der Lernseite, sein Wort: "Bitte alles mit
// Knopftest pruefen vor Auslieferung!" Die Seite wird im echten Browser geladen und jeder Knopf gedrueckt;
// der Jetson wird durch die ECHTEN geholten Daten ersetzt (Liste mit 301 Eintraegen, zwei echte Lernbilder
// und ihre Rahmen). Gemessen wird, was danach auf der Seite steht -- nicht, ob ein Abruf 200 liefert.
//   node pruefe_lernseite_knopf_1.0.js ../lernen_1.5.html
const { chromium } = require('playwright'); const fs = require('fs');
const SEITE = process.argv[2] || '../lernen_1.5.html';
const M = '../medien/';
const html = fs.readFileSync(SEITE, 'utf8');
const liste = JSON.parse(fs.readFileSync(M + 'lernen_liste_2026-11-07.json', 'utf8'));
const boxen = {
  '20261106_100110_b235': fs.readFileSync(M + 'lernen_boxen_20261106_100110_b235.json', 'utf8'),
  '20261106_100110_b185': fs.readFileSync(M + 'lernen_boxen_20261106_100110_b185.json', 'utf8') };
const BILD = { '20261106_100110_b235': M + '20261106_100110_b235.jpg', '20261106_100110_b185': M + '20261106_100110_b185.jpg' };
const stand = JSON.parse(JSON.stringify(liste));           // Serverzustand, den POST veraendert
const posts = [];

(async () => {
  const b = await chromium.launch({ executablePath: process.env.CHROME });
  const pg = await b.newPage({ viewport: { width: 1500, height: 1050 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e.message)));
  pg.on('console', m => { if (m.type() === 'error') fehler.push('console: ' + m.text()); });
  await pg.route('**/*', async r => {
    const u = r.request().url(); const m = r.request().method();
    if (/\/lernen\/liste/.test(u)) return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(stand) });
    if (/\/lernen\/fertig/.test(u)) { posts.push({ art: 'fertig' });
      return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, uhr: '11:30:00', training: true }) }); }
    const mb = u.match(/\/lernen\/boxen\/([^?]+)/);
    if (mb) { const name = mb[1];
      if (m === 'POST') { const d = JSON.parse(r.request().postData() || '{}'); posts.push({ art: 'boxen', name, status: d.status, n: (d.boxen || []).length });
        const e = stand.find(x => x.name === name); if (e) { e.status = d.status; e.n_boxen = (d.boxen || []).length; }
        return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, name, status: d.status, n_boxen: (d.boxen || []).length }) }); }
      const key = boxen[name] ? name : '20261106_100110_b185';
      return r.fulfill({ status: 200, contentType: 'application/json', body: boxen[key] }); }
    const mi = u.match(/\/lernen\/bild\/([^?.]+)\.jpg/);
    if (mi) { const key = BILD[mi[1]] ? mi[1] : '20261106_100110_b185'; return r.fulfill({ status: 200, contentType: 'image/jpeg', path: BILD[key] }); }
    if (/\/lernen$/.test(u)) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: html });
    return r.fulfill({ status: 404, body: '' }); });

  const lage = () => pg.evaluate(() => ({
    stand: (document.getElementById('stand') || {}).textContent || '',
    info: (document.getElementById('info') || {}).textContent || '',
    gespeichert: (document.getElementById('gespeichert') || {}).textContent || '',
    eintraege: document.querySelectorAll('#liste div').length,
    aktiv: (document.querySelector('#liste div.aktiv') || {}).textContent || '',
    filter: (document.getElementById('filter') || {}).value || '',
    leinwand_leer: (() => { const c = document.getElementById('leinwand'); if (!c) return null;
      const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
      for (let i = 0; i < d.length; i += 4000) if (d[i] !== 0 || d[i+1] !== 0 || d[i+2] !== 0) return false; return true; })() }));

  const P = []; const schritt = async (name, tun, erwartung) => {
    const vor = await lage(); try { await tun(); } catch (e) { P.push({ name, ok: false, grund: 'Klick fehlgeschlagen: ' + e.message }); return; }
    await pg.waitForTimeout(600); const nach = await lage();
    const u = erwartung(vor, nach); P.push({ name, ok: u.ok, grund: u.grund, info: nach.info.slice(0, 90), eintraege: nach.eintraege, aktiv: nach.aktiv.trim().slice(0, 30) }); };

  await pg.goto('http://127.0.0.1:8095/lernen', { waitUntil: 'load' }); await pg.waitForTimeout(1200);
  const start = await lage();
  P.push({ name: 'K0 Start: Liste gefuellt', ok: start.eintraege > 0, grund: `Filter "${start.filter}", ${start.eintraege} Eintraege in der Liste`, info: start.info.slice(0, 90) });
  P.push({ name: 'K0b Start: Bild gezeichnet', ok: start.leinwand_leer === false, grund: start.leinwand_leer ? 'Leinwand ist schwarz' : 'Bild steht auf der Leinwand' });

  await schritt('K1 "nur blaettern" schaltet weiter', () => pg.click('#weiter'),
    (v, n) => ({ ok: n.info !== v.info && !/Keine weiteren/.test(n.info), grund: /Keine weiteren/.test(n.info) ? 'meldet "Keine weiteren Bilder"' : (n.info === v.info ? 'Infozeile unveraendert' : 'neues Bild geoeffnet') }));

  await schritt('K2 Filter auf "zurueckgestellte"', () => pg.selectOption('#filter', 'zurueckgestellt'),
    (v, n) => ({ ok: n.eintraege > 0, grund: `${n.eintraege} Eintraege sichtbar` }));

  await schritt('K3 Eintrag in der Liste anklicken', () => pg.click('#liste div:nth-child(3)'),
    (v, n) => ({ ok: n.aktiv !== '' && n.leinwand_leer === false, grund: n.aktiv ? 'geoeffnet: ' + n.aktiv.trim() : 'kein Eintrag aktiv' }));

  await schritt('K4 "nur blaettern" im Filter', () => pg.click('#weiter'),
    (v, n) => ({ ok: n.aktiv !== v.aktiv && !/Keine weiteren/.test(n.info), grund: /Keine weiteren/.test(n.info) ? 'meldet "Keine weiteren Bilder"' : (n.aktiv === v.aktiv ? 'dasselbe Bild' : 'weitergeschaltet auf ' + n.aktiv.trim()) }));

  await schritt('K5 "zurueck" bleibt in der Auswahl', () => pg.click('#zurueck'),
    (v, n) => ({ ok: n.aktiv !== v.aktiv && n.aktiv.trim() !== '', grund: n.aktiv.trim() === '' ? 'geoeffnetes Bild steht nicht in der Auswahl (kein Eintrag aktiv)' : 'zurueck auf ' + n.aktiv.trim() }));

  const vorP = posts.length;
  await schritt('K6 "Rahmen stimmen, speichern, weiter"', () => pg.click('#richtig'),
    (v, n) => ({ ok: posts.length > vorP && /gespeichert/.test(n.gespeichert), grund: posts.length > vorP ? `gespeichert als ${posts[posts.length-1].status}, ${n.gespeichert.slice(0,40)}` : 'kein Speichern ausgeloest' }));

  await schritt('K7 Tastatur nach Knopfdruck (Eingabetaste)', async () => { await pg.keyboard.press('Enter'); },
    (v, n) => ({ ok: n.aktiv !== v.aktiv || posts.length > vorP + 1, grund: n.aktiv === v.aktiv ? 'Eingabetaste ohne Wirkung (Fokus klebt am Knopf)' : 'hat weitergeschaltet' }));

  await schritt('K8 "Vorschlaege wiederherstellen"', () => pg.click('#reset'),
    (v, n) => ({ ok: n.leinwand_leer === false, grund: 'Bild weiterhin gezeichnet' }));

  const vorV = posts.length;
  await schritt('K9 "Bild unbrauchbar, speichern, weiter"', () => pg.click('#verwerfen'),
    (v, n) => ({ ok: posts.length > vorV && posts[posts.length-1].status === 'verworfen', grund: posts.length > vorV ? 'als verworfen gespeichert' : 'kein Speichern ausgeloest' }));

  let kornAktiv = false;
  await schritt('K10 Klassenknopf "Korn"', async () => { await pg.click('button.kl[data-klasse="korn"]'); await pg.waitForTimeout(200);
      kornAktiv = await pg.evaluate(() => !!document.querySelector('button.kl[data-klasse="korn"].aktiv')); },
    () => ({ ok: kornAktiv, grund: kornAktiv ? 'Klasse Korn ist hervorgehoben' : 'Knopf wird nicht hervorgehoben' }));

  const vorF = posts.length;
  await schritt('K11 "Fertig fuer heute"', () => pg.click('#fertig'),
    (v, n) => ({ ok: posts.slice(vorF).some(x => x.art === 'fertig'), grund: posts.slice(vorF).some(x => x.art === 'fertig') ? 'Runde an den Jetson gemeldet' : 'keine Meldung an den Jetson' }));
  const bilanz = await pg.evaluate(() => { const b = document.getElementById('bilanz'); return b && !b.hidden ? b.textContent.slice(0, 120) : ''; });

  const zahlen = await pg.evaluate(() => [...document.querySelectorAll('#filter option')].map(o => o.textContent));
  P.push({ name: 'K12 Auswahl zeigt ihre Zahlen', ok: zahlen.every(x => /\(\d+\)/.test(x)), grund: zahlen.join(' / ') });
  const gesperrt = await pg.evaluate(() => { const b = document.getElementById('weiter'); return { aus: b.disabled, warum: b.title }; });
  P.push({ name: 'K13 gesperrter Knopf sagt warum', ok: !gesperrt.aus || /Auswahl|weiteres/.test(gesperrt.warum), grund: gesperrt.aus ? 'gesperrt mit Begruendung: ' + gesperrt.warum : 'nicht gesperrt' });
  const platz = await pg.evaluate(() => (document.getElementById('platz') || {}).textContent || '(kein Feld)');
  P.push({ name: 'K14 Platzanzeige vorhanden', ok: /von|leer|Auswahl/.test(platz), grund: platz });

  await pg.screenshot({ path: '../medien/knopfprobe_' + SEITE.replace(/.*\//, '').replace('.html', '') + '.png' });
  const n_ok = P.filter(x => x.ok).length;
  console.log('\n===== KNOPFPROBE ' + SEITE + '   ' + n_ok + ' von ' + P.length + ' bestanden');
  for (const x of P) console.log(`  ${x.ok ? 'JA  ' : 'NEIN'} ${x.name.padEnd(46)} ${x.grund || ''}`);
  console.log('  Bilanzfeld nach "Fertig": ' + (bilanz || '(leer)'));
  console.log('  Seitenfehler: ' + (fehler.length ? fehler.join(' | ') : 'keine'));
  console.log('KNOPFJSON ' + JSON.stringify({ seite: SEITE, bestanden: n_ok, gesamt: P.length, punkte: P, fehler, posts }));
  await b.close(); process.exit(n_ok === P.length ? 0 : 1);
})().catch(e => { console.log('ABBRUCH ' + e.message); process.exit(2); });
