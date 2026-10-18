// Export the production looks from a lab page, every folder.
// Usage: [LAB=styles|looks3] node export_styles.cjs OUT_DIR [style ...]
//   LAB=styles (default)  board/styles.html, styles pol arc riso hype
//   LAB=looks3            board/looks3.html, styles mono app (the lab's other styles are unpicked candidates;
//                         name one to render it)
//   KEYS=a,b   only these folder keys        NOANIM=1   skip the Top 10 hover loops   ONLYANIM=1   only the loops
// OUT_DIR/<look>/covers/<collection>/<folder>.webp   1600x900 still (Nuvio's coverImageUrl)
// OUT_DIR/<look>/anim/<collection>/<folder>.webp     512x288, 36 frames at 10 fps, every frame a keyframe,
//                                                    Top 10 only (focusGifUrl)
// Frame i of a loop is drawn at t = i / 36, so frame 0 is the still and the loop closes.
// The Riso halftone reads stills into a canvas, so Chromium runs with file access from files.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "/Users/elmarco/Projects/kabacade-hq/node_modules/@playwright/test");
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const LAB = process.env.LAB || "styles";
const PAGE = path.join(ROOT, "board", `${LAB}.html`);
const LAB_STYLES = { styles: ["pol", "arc", "riso", "hype"], looks3: ["mono", "app"] };
const FRAMES = 36;
const LOOKS = { pol: "polaroid-table", arc: "arcade", riso: "riso-zine", hype: "hype-reel", mono: "true-black-mono", app: "showcase", vhs: "vhs-rental", film: "lightbox", gallery: "gallery", cine: "movie-night", flap: "split-flap", sticker: "sticker-pack", slate: "slate" };
// cwebp / img2webp quality per look: halftone dots and dithered pixels cost far more bytes than photos,
// so those looks trade a little quality for loops the iPhone can hold in memory.
const Q = { pol: [82, 70], arc: [80, 66], riso: [78, 58], hype: [82, 70], mono: [84, 72], app: [82, 72], vhs: [82, 70], film: [82, 70], gallery: [82, 70], cine: [82, 70], flap: [82, 70], sticker: [84, 72], slate: [82, 70] };
const js = fs.readFileSync(path.join(ROOT, "board", "folders.js"), "utf8");
const FOLDERS = JSON.parse(js.match(/window\.FOLDERS = ([\s\S]*?);\nwindow\.ROWS/)[1]);

async function open(ctx, style, key, width, height) {
  const page = await ctx.newPage();
  page.on("pageerror", (e) => console.error(style, key, e.message));
  await page.setViewportSize({ width, height });
  await page.goto(`file://${PAGE}#r-${style}-${key}`, { waitUntil: "load" });
  await page.waitForFunction(() => window.renderReady === true || window.renderError, null, { timeout: 60000 });
  const err = await page.evaluate(() => window.renderError);
  if (err) throw new Error(`${style} ${key}: ${err}`);
  await page.evaluate(async () => {
    const urls = new Set();
    document.querySelectorAll("#render *").forEach((el) => {
      const cs = getComputedStyle(el);
      for (const v of [cs.backgroundImage, cs.maskImage || cs.webkitMaskImage || ""])
        for (const m of v.matchAll(/url\("?([^")]+)"?\)/g)) if (!m[1].startsWith("data:")) urls.add(m[1]);
    });
    document.querySelectorAll("#render img").forEach((i) => urls.add(i.src));
    await Promise.all([...urls].map((u) => { const i = new Image(); i.src = u; return i.decode().catch(() => {}); }));
  });
  await page.waitForTimeout(200);
  return page;
}

(async () => {
  const [out, ...only] = process.argv.slice(2);
  const styles = only.length ? only : LAB_STYLES[LAB];
  const keys = process.env.KEYS ? process.env.KEYS.split(",") : Object.keys(FOLDERS);
  const browser = await chromium.launch({ args: ["--allow-file-access-from-files"] });
  const ctx = await browser.newContext({ deviceScaleFactor: 1 });
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "stcovers-"));
  const queue = [
    ...(process.env.ONLYANIM ? [] : styles.flatMap((s) => keys.map((k) => ["still", s, k]))),
    ...(process.env.NOANIM ? [] : styles.flatMap((s) => keys.filter((k) => FOLDERS[k].kind === "top").map((k) => ["anim", s, k]))),
  ];
  const total = queue.length;
  let done = 0;
  async function render(kind, s, k) {
    const [coll, slug] = k.split("--");
    if (kind === "still") {
      const page = await open(ctx, s, k, 1600, 900);
      const png = path.join(tmp, `${s}-${k}.png`);
      await page.screenshot({ path: png, type: "png" });
      await page.close();
      const dst = path.join(out, LOOKS[s], "covers", coll, `${slug}.webp`);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      execFileSync("cwebp", ["-quiet", "-q", String(Q[s][0]), "-m", "6", "-sharp_yuv", png, "-o", dst]);
      fs.rmSync(png);
    } else {
      const page = await open(ctx, s, k, 512, 288);
      const dir = fs.mkdtempSync(path.join(tmp, `${s}-${k}-`));
      const frames = [];
      for (let i = 0; i < FRAMES; i++) {
        await page.evaluate((t) => { window.setT(t); return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }, i / FRAMES);
        const f = path.join(dir, `f${String(i).padStart(2, "0")}.png`);
        await page.screenshot({ path: f, type: "png" });
        frames.push(f);
      }
      await page.close();
      const dst = path.join(out, LOOKS[s], "anim", coll, `${slug}.webp`);
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      execFileSync("img2webp", ["-loop", "0", "-kmin", "0", "-kmax", "1", "-lossy", "-q", String(Q[s][1]), "-m", "6", "-d", "100", ...frames, "-o", dst], { stdio: "ignore" });
      fs.rmSync(dir, { recursive: true, force: true });
    }
  }
  // A page can time out while five loops are capturing at once; each job gets a second try, and anything
  // that still fails is listed at the end instead of stopping the whole run.
  const failed = [];
  async function worker() {
    while (queue.length) {
      const job = queue.shift();
      try { await render(...job); } catch (e) {
        try { await render(...job); } catch (e2) { failed.push(`${job.join(" ")}: ${e2.message.split("\n")[0]}`); }
      }
      done++;
      if (done % 20 === 0 || done === total) console.log(`${done}/${total}`);
    }
  }
  await Promise.all(Array.from({ length: 5 }, worker));
  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });
  if (failed.length) { console.error("FAILED\n" + failed.join("\n")); process.exit(1); }
})();
