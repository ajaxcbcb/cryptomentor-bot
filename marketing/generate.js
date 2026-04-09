/**
 * CryptoMentor Daily Poster Generator
 * Usage:
 *   node generate.js             → generate + send today's poster
 *   node generate.js --id=5      → generate + send specific post
 *   node generate.js --all       → generate all posts (no send)
 *   node generate.js --no-send   → generate only, skip Telegram
 */

// Load environment variables
require('dotenv').config();

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const https = require('https');
const FormData = require('form-data');

// Get credentials from environment (with fallbacks for security)
const BOT_TOKEN = process.env.BOT_TOKEN;
const CHAT_ID   = process.env.CHAT_ID;

// Validate required configuration
if (!BOT_TOKEN || !CHAT_ID) {
  console.error('❌ ERROR: BOT_TOKEN and CHAT_ID environment variables are required.');
  console.error('   Copy .env.example to .env and fill in your Telegram credentials.');
  process.exit(1);
}

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
  
  try {
    fs.writeFileSync(tmpPath, html);

    const page = await browser.newPage();
    try {
      await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 2 });
      await page.goto('file:///' + tmpPath.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
      await new Promise(r => setTimeout(r, 1500)); // wait for fonts

      // Ensure output dir exists
      const outDir = path.join(__dirname, 'output');
      if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

      const date = new Date().toISOString().slice(0, 10);
      const outFile = path.join(outDir, `poster_${date}_${post.type}_${post.theme}.png`);

      await page.screenshot({ path: outFile, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
      return outFile;
    } finally {
      await page.close().catch(err => console.error('Failed to close page:', err));
    }
  } finally {
    // Always cleanup temp file, even on error
    try {
      if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
    } catch (err) {
      console.warn(`Warning: Failed to cleanup temp file ${tmpPath}:`, err.message);
    }
  }
}

// ── Send PNG to Telegram with retry logic ──
async function sendPhoto(filePath, caption, retries = 3, delayMs = 1000) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await new Promise((resolve, reject) => {
        const form = new FormData();
        form.append('chat_id', CHAT_ID);
        form.append('photo', fs.createReadStream(filePath), { filename: path.basename(filePath) });
        form.append('caption', caption);
        form.append('parse_mode', 'HTML');

        const options = {
          hostname: 'api.telegram.org',
          path: `/bot${BOT_TOKEN}/sendPhoto`,
          method: 'POST',
          headers: form.getHeaders(),
          timeout: 10000, // 10 second timeout
        };

        const req = https.request(options, res => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              if (json.ok) {
                resolve(json);
              } else {
                reject(new Error(`Telegram API error: ${json.description || 'Unknown error'}`));
              }
            } catch (err) {
              reject(new Error(`Failed to parse Telegram response: ${err.message}`));
            }
          });
        });

        req.on('error', reject);
        req.on('timeout', () => {
          req.abort();
          reject(new Error('Request timeout'));
        });
        
        form.pipe(req);
      });
    } catch (err) {
      const isLastAttempt = attempt === retries;
      const errorMsg = `Attempt ${attempt}/${retries} failed: ${err.message}`;
      
      if (isLastAttempt) {
        throw new Error(`Failed to send photo after ${retries} retries: ${err.message}`);
      } else {
        console.warn(`⚠️  ${errorMsg} — Retrying in ${delayMs}ms...`);
        await new Promise(r => setTimeout(r, delayMs));
        // Exponential backoff
        delayMs = Math.min(delayMs * 1.5, 10000);
      }
    }
  }
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
