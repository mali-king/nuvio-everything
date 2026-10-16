// Export every Everything cover from board/covers.html.
// Usage: node export_covers.cjs [only-key ...]
// covers/<collection>/<folder>.webp   1600x900 still (Nuvio's coverImageUrl)
// anim/<collection>/<folder>.webp     512x288, 36 frames at 10 fps, Top 10 only (focusGifUrl)
// Frame i of an animation is drawn at --t = i / 36, so frame 0 is the still and the loop closes.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/Users/elmarco/Projects/kabacade-hq/node_modules/@playwright/test");
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PAGE = path.join(ROOT, "board", "covers.html");
const DIST = ROOT;
const FRAMES = 36;

const js = fs.readFileSync(path.join(ROOT, "board", "folders.js"), "utf8");
const FOLDERS = JSON.parse(js.match(/window\.FOLDERS = ([\s\S]*?);\nwindow\.ROWS/)[1]);

async function open(ctx, key, width, height) {
  const page = await ctx.newPage();
  await page.setViewportSize({ width, height });
  await page.goto(`file://${PAGE}#r-${key}`, { waitUntil: "load" });
  await page.waitForFunction(() => window.renderReady === true, null, { timeout: 30000 });
  // CSS background stills and logos: wait until every one has decoded.
  await page.evaluate(async () => {
    const urls = new Set();
    document.querySelectorAll("#render *").forEach((el) => {
      const m = getComputedStyle(el).backgroundImage.match(/url\("?([^")]+)"?\)/);
      if (m && !m[1].startsWith("data:")) urls.add(m[1]);
    });
    document.querySelectorAll("#render img").forEach((i) => urls.add(i.src));
    await Promise.all([...urls].map((u) => { const i = new Image(); i.src = u; return i.decode(); }));
  });
  await page.waitForTimeout(250);
  return page;
}

(async () => {
  const only = process.argv.slice(2);
  const keys = Object.keys(FOLDERS).filter((k) => !only.length || only.includes(k));
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ deviceScaleFactor: 1 });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "evcovers-"));
  const queue = keys.slice();
  let done = 0;

  async function worker() {
    while (queue.length) {
      const key = queue.shift();
      const [coll, slug] = key.split("--");
      const png = path.join(tmp, `${key}.png`);
      const still = path.join(DIST, "covers", coll, `${slug}.webp`);
      fs.mkdirSync(path.dirname(still), { recursive: true });
      let page = await open(ctx, key, 1600, 900);
      await page.screenshot({ path: png, type: "png" });
      await page.close();
      execFileSync("cwebp", ["-quiet", "-q", "84", "-m", "6", "-sharp_yuv", png, "-o", still]);

      if (FOLDERS[key].kind === "top") {
        const dir = path.join(tmp, key);
        fs.mkdirSync(dir);
        page = await open(ctx, key, 512, 288);
        const frames = [];
        for (let i = 0; i < FRAMES; i++) {
          await page.evaluate((t) => window.setT(t), i / FRAMES);
          const f = path.join(dir, `f${String(i).padStart(3, "0")}.png`);
          await page.screenshot({ path: f, type: "png" });
          frames.push(f);
        }
        await page.close();
        const anim = path.join(DIST, "anim", coll, `${slug}.webp`);
        fs.mkdirSync(path.dirname(anim), { recursive: true });
        execFileSync("img2webp", ["-loop", "0", "-kmin", "0", "-kmax", "1", "-lossy", "-q", "75", "-d", "100", ...frames, "-o", anim]);
      }
      done++;
      if (done % 10 === 0 || done === keys.length) console.log(`${done}/${keys.length}`);
    }
  }
  await Promise.all(Array.from({ length: 5 }, worker));
  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
})();
