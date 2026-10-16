// Render one animated cover from aurora.html as numbered PNG frames.
// Usage: node export_frames.cjs <aurora.html> <variant> <motion> <folder key> <out dir> [frames] [width] [height]
// Frame i is drawn at --t = i / frames, so frame 0 is the still cover and the loop closes cleanly.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/Users/elmarco/Projects/kabacade-hq/node_modules/@playwright/test");
const fs = require("fs");
const path = require("path");

(async () => {
  const [html, variant, motion, key, outDir, frames = "36", width = "512", height = "288"] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width), height: Number(height) }, deviceScaleFactor: 1 });
  await page.goto(`file://${html}#r-${variant}-${motion}-${key}`, { waitUntil: "load" });
  await page.waitForFunction(() => window.renderReady === true, null, { timeout: 30000 });
  await page.waitForTimeout(800); // late CSS background images
  const n = Number(frames);
  for (let i = 0; i < n; i++) {
    await page.evaluate((t) => window.setT(t), i / n);
    await page.screenshot({ path: path.join(outDir, `f${String(i).padStart(3, "0")}.png`), type: "png" });
  }
  await browser.close();
  console.log(`${key}: ${n} frames -> ${outDir}`);
})();
