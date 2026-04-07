const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });

  // ── STEP 1: Grab logo from Telegram channel preview ──
  console.log('📥 Fetching logo from Telegram...');
  const tgPage = await browser.newPage();
  await tgPage.setViewport({ width: 1280, height: 800 });
  await tgPage.goto('https://t.me/CryptoMentorID', { waitUntil: 'networkidle2', timeout: 30000 });

  // Telegram preview page has an <img> with the channel avatar
  const logoBase64 = await tgPage.evaluate(async () => {
    // Try multiple selectors Telegram uses for channel photo
    const selectors = [
      '.tgme_page_photo_image',
      '.tgme_page_photo img',
      'img.tgme_page_photo_image',
      '.tgme_page img'
    ];
    let imgEl = null;
    for (const sel of selectors) {
      imgEl = document.querySelector(sel);
      if (imgEl) break;
    }
    if (!imgEl) return null;

    // Fetch image and convert to base64
    const response = await fetch(imgEl.src);
    const blob = await response.blob();
    return new Promise(resolve => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  });

  await tgPage.close();

  let logoSrc = '';
  if (logoBase64) {
    // Save as file too
    const base64Data = logoBase64.replace(/^data:image\/\w+;base64,/, '');
    fs.writeFileSync(path.resolve(__dirname, 'logo.png'), Buffer.from(base64Data, 'base64'));
    logoSrc = logoBase64;
    console.log('✓ Logo downloaded successfully');
  } else {
    // Fallback: use inline SVG placeholder if Telegram blocks
    console.log('⚠ Could not fetch logo from Telegram, using fallback');
    logoSrc = 'fallback';
  }

  // ── STEP 2: Render poster with real logo ──
  console.log('🎨 Rendering poster...');
  const posterPage = await browser.newPage();
  await posterPage.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });

  const filePath = 'file:///' + path.resolve(__dirname, 'poster_autotrade.html').replace(/\\/g, '/');
  await posterPage.goto(filePath, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));

  // Inject real logo into poster
  if (logoSrc !== 'fallback') {
    await posterPage.evaluate((src) => {
      const logoImg = document.querySelector('.logo-img');
      if (logoImg) logoImg.src = src;
    }, logoSrc);
    await new Promise(r => setTimeout(r, 500));
  }

  await posterPage.screenshot({
    path: path.resolve(__dirname, 'poster_autotrade.png'),
    clip: { x: 0, y: 0, width: 1080, height: 1080 }
  });

  await browser.close();
  console.log('✅ Done! Saved: marketing/poster_autotrade.png (2160×2160 @2x)');
})();
