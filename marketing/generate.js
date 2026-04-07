/**
 * CryptoMentor Daily Poster Generator
 * Usage:
 *   node generate.js             → generate + send today's poster
 *   node generate.js --id=5      → generate + send specific post
 *   node generate.js --all       → generate all posts (no send)
 *   node generate.js --no-send   → generate only, skip Telegram
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const https = require('https');
const FormData = require('form-data');

const BOT_TOKEN = '<REDACTED_TELEGRAM_BOT_TOKEN>';
const CHAT_ID   = '1234500009';

const calendar = JSON.parse(fs.readFileSync(path.join(__dirname, 'content_calendar.json'), 'utf8'));
const args = process.argv.slice(2);

// ── Pick which post to generate ──
function getPost() {
  const idArg = args.find(a => a.startsWith('--id='));
  if (idArg) {
    const id = parseInt(idArg.split('=')[1]);
    return calendar.posts.find(p => p.id === id) || null;
  }
  // Default: rotate by day of year
  const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
  const idx = dayOfYear % calendar.posts.length;
  return calendar.posts[idx];
}

// ── Build HTML from template ──
function buildHtml(post) {
  const templateFile = post.type === 'education' ? 'education.html' : 'product.html';
  let html = fs.readFileSync(path.join(__dirname, 'templates', templateFile), 'utf8');
  const b = calendar.brand;

  // Brand tokens
  html = html.replace(/\{\{brand\.name\}\}/g, b.name);
  html = html.replace(/\{\{brand\.tagline\}\}/g, b.tagline);
  html = html.replace(/\{\{brand\.telegram\}\}/g, b.telegram);
  html = html.replace(/\{\{brand\.accent1\}\}/g, b.accent1);
  html = html.replace(/\{\{brand\.accent2\}\}/g, b.accent2);
  html = html.replace(/\{\{brand\.bg\}\}/g, b.bg);

  // Post tokens
  html = html.replace(/\{\{eyebrow\}\}/g, post.eyebrow);
  html = html.replace(/\{\{headline\}\}/g, post.headline);
  html = html.replace(/\{\{subtext\}\}/g, post.subtext);
  html = html.replace(/\{\{cta\}\}/g, post.cta);

  // Pillars (product template)
  if (post.pillars) {
    const pillarsHtml = post.pillars.map(p => `
      <div class="pillar">
        <div class="pillar-num">${p.num}</div>
        <div class="pillar-label">${p.label}</div>
        <div class="pillar-desc">${p.desc}</div>
      </div>`).join('');
    html = html.replace('{{pillars}}', pillarsHtml);
  }

  // Points (education template)
  if (post.points) {
    const pointsHtml = post.points.map(p => `
      <div class="point-card">
        <span class="point-icon">${p.icon}</span>
        <div>
          <div class="point-label">${p.label}</div>
          <div class="point-desc">${p.desc}</div>
        </div>
      </div>`).join('');
    html = html.replace('{{points}}', pointsHtml);
  }

  return html;
}

// ── Render one post to PNG ──
async function renderPost(post, browser) {
  const html = buildHtml(post);

  // Write temp HTML
  const tmpPath = path.join(__dirname, `_tmp_${post.id}.html`);
  fs.writeFileSync(tmpPath, html);

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 2 });
  await page.goto('file:///' + tmpPath.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500)); // wait for fonts

  // Ensure output dir exists
  const outDir = path.join(__dirname, 'output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  const date = new Date().toISOString().slice(0, 10);
  const outFile = path.join(outDir, `poster_${date}_${post.type}_${post.theme}.png`);

  await page.screenshot({ path: outFile, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  await page.close();
  fs.unlinkSync(tmpPath); // cleanup temp

  return outFile;
}

// ── Send PNG to Telegram ──
function sendPhoto(filePath, caption) {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append('chat_id', CHAT_ID);
    form.append('photo', fs.createReadStream(filePath), { filename: path.basename(filePath) });
    form.append('caption', caption);
    form.append('parse_mode', 'HTML');

    const options = {
      hostname: 'api.telegram.org',
      path: `/bot${BOT_TOKEN}/sendPhoto`,
      method: 'POST',
      headers: form.getHeaders()
    };

    const req = https.request(options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const json = JSON.parse(data);
        if (json.ok) resolve(json);
        else reject(new Error(json.description));
      });
    });
    req.on('error', reject);
    form.pipe(req);
  });
}

// ── Main ──
(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    executablePath: process.env.PUPPETEER_EXEC ||
      (process.platform === 'linux' ? '/usr/bin/chromium-browser' : undefined)
  });
  const noSend = args.includes('--no-send');

  if (args.includes('--all')) {
    console.log(`🎨 Generating all ${calendar.posts.length} posters...`);
    for (const post of calendar.posts) {
      const out = await renderPost(post, browser);
      console.log(`  ✓ [${post.id}] ${post.type} · ${post.theme} → ${path.basename(out)}`);
    }
  } else {
    const post = getPost();
    if (!post) { console.error('Post not found'); process.exit(1); }
    console.log(`🎨 Generating: [${post.id}] ${post.type} · ${post.theme}`);
    const out = await renderPost(post, browser);
    console.log(`✅ PNG saved → ${out}`);

    if (!noSend) {
      console.log(`📤 Sending to Telegram (${CHAT_ID})...`);
      const caption = `<b>${post.eyebrow}</b>\n\n${post.subtext}\n\n<i>${calendar.brand.telegram}</i>`;
      try {
        await sendPhoto(out, caption);
        console.log(`✅ Sent to Telegram successfully`);
      } catch (err) {
        console.error(`❌ Telegram send failed: ${err.message}`);
      }
    }
  }

  await browser.close();
})();
