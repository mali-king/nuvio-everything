// One full-page screenshot of a local HTML page, after fonts and late CSS images settle.
// Usage: node shot.cjs page.html out.png [width]
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/Users/elmarco/Projects/kabacade-hq/node_modules/@playwright/test");
(async () => {
  const [html, out, width] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: Number(width || 1400), height: 900 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto("file://" + html, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: out, fullPage: true, type: "jpeg", quality: 70 });
  console.log("errors:", errors.length ? errors.join(" | ") : "none");
  await browser.close();
})();
