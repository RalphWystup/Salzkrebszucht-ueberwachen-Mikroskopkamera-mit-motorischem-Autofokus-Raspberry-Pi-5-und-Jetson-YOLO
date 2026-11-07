const { chromium } = require('playwright');
(async () => { const b = await chromium.launch({ executablePath: process.env.CHROME }); const pg = await b.newPage();
  await pg.goto('http://127.0.0.1:8090/', { waitUntil: 'load' }); await pg.waitForTimeout(8000);
  console.log('P8JSON ' + JSON.stringify(await pg.evaluate(() => ({ lampe: document.getElementById('jlampe').className, bild: document.getElementById('bild').naturalWidth }))));
  await b.close(); })().catch(e => { console.log('FEHLER ' + e.message); process.exit(1); });
