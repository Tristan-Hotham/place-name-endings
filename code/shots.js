// Test screenshots with Playwright (headless Chromium). Usage: node code/shots.js http://localhost:8765/ work/shots
const { chromium } = require('playwright');
(async () => {
  const [url, dir] = process.argv.slice(2);
  const b = await chromium.launch();
  const errs = [];
  async function page(w, h) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.route(/cdnjs\.cloudflare\.com\/ajax\/libs\/leaflet\/1\.9\.4\/(leaflet\.min\.(js|css))/, r => { const f = r.request().url().endsWith('.js') ? 'leaflet.js' : 'leaflet.css'; r.fulfill({ path: '/tmp/claude-0/lf/node_modules/leaflet/dist/' + f }); });
    await p.route(/fonts\.(googleapis|gstatic)\.com|arcgisonline/, r => r.fulfill({ body: '', contentType: 'text/css' }));
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
    return p;
  }
  // desktop
  let p = await page(1300, 1000);
  await p.evaluate(() => document.getElementById('mapfig').scrollIntoView());
  await p.waitForTimeout(500);
  await (await p.$('#mapfig')).screenshot({ path: dir + '/d_fam.png' });
  await p.click('#ireBtns .btn[data-i="townlands"]'); await p.waitForTimeout(2500);
  await p.evaluate(() => { lmap.setView([53.4, -7.8], 7, { animate: false }); }); await p.waitForTimeout(800);
  await (await p.$('#mapfig')).screenshot({ path: dir + '/d_townlands.png' });
  await p.evaluate(() => { showEl('kil', false); }); await p.waitForTimeout(800);
  await (await p.$('#mapfig')).screenshot({ path: dir + '/d_kil.png' });
  await p.evaluate(() => { S.mode = 'fam'; setMode('fam'); lmap.setView([53.2, -0.4], 9.5, { animate: false }); }); await p.waitForTimeout(1500);
  await p.mouse.click(400, 400);
  await (await p.$('#mapfig')).screenshot({ path: dir + '/d_dots.png' });
  await p.evaluate(() => { const i = document.getElementById('q'); i.value = 'Ballina'; i.dispatchEvent(new Event('input')); }); await p.waitForTimeout(600);
  await p.keyboard.press('Tab');
  await p.evaluate(() => { const i = document.getElementById('q'); i.focus(); }); await p.keyboard.press('Enter'); await p.waitForTimeout(1200);
  await (await p.$('#mapfig')).screenshot({ path: dir + '/d_search.png' });
  await p.screenshot({ path: dir + '/d_full.png', fullPage: true });
  await p.close();
  // phone
  p = await page(390, 844);
  await p.screenshot({ path: dir + '/m_top.png' });
  await p.evaluate(() => document.getElementById('mapfig').scrollIntoView());
  await p.waitForTimeout(400);
  await p.screenshot({ path: dir + '/m_map.png' });
  await p.evaluate(() => document.querySelector('#scotCards .card').click()); await p.waitForTimeout(1500);
  await p.screenshot({ path: dir + '/m_card.png' });
  const sw = await p.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
  await p.screenshot({ path: dir + '/m_full.png', fullPage: true });
  console.log('scrollWidth', sw);
  await p.close();
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
