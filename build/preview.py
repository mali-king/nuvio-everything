"""Write the preview page for the exported Everything covers.

Usage: python3 -I preview.py OUT_DIR
OUT_DIR holds c/<collection>--<folder>.webp (800x450 stills) and a/<collection>--<folder>.webp
(the Top 10 loops); this writes OUT_DIR/index.html from everything-collections.json.
"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]
colls = json.load(open(os.path.join(ROOT, "everything-collections.json")))

OPENS = {"ROWS": "Opens as rows", "TABBED_GRID": "Opens as a grid with an All tab"}
TYPE = {"movie": "Movies", "series": "Series", "anime": "Anime", "all": "All", "tv": "Series"}


def slug_of(url):
    coll, name = url.rsplit("/", 2)[-2:]
    return f"{coll}--{name[:-5]}"


def row_label(s):
    if s["provider"] == "addon":
        return f'{s["catalogName"]} ({TYPE[s["type"]]})'
    return f'{s["title"]} · TMDB'


sections = []
for c in colls:
    tiles, lists = [], []
    for f in c["folders"]:
        key = slug_of(f["coverImageUrl"])
        t = html.escape(f["title"])
        n = len(f["sources"])
        if f["focusGifUrl"]:
            img = f'<img src="a/{key}" alt="{t} Top 10 cover, animated" loading="lazy" width="512" height="288">'
        else:
            img = f'<img src="c/{key}.webp" alt="{t} cover" loading="lazy" width="800" height="450">'
        tiles.append(f'<figure>{img.replace("a/" + key, "a/" + key + ".webp")}'
                     f'<figcaption><span>{t}</span><span>{n} row{"s" if n != 1 else ""}</span></figcaption></figure>')
        rows = "".join(f"<li>{html.escape(row_label(s))}</li>" for s in f["sources"])
        lists.append(f"<div><h4>{t}</h4><ol>{rows}</ol></div>")
    n_rows = sum(len(f["sources"]) for f in c["folders"])
    sections.append(f"""
<section>
  <header class="sh"><h2>{html.escape(c["title"])}</h2>
    <p>{len(c["folders"])} folders · {OPENS[c["viewMode"]]} · {n_rows} rows in all</p></header>
  <div class="track">{"".join(tiles)}</div>
  <details><summary>What each folder opens to</summary><div class="lists">{"".join(lists)}</div></details>
</section>""")

n_f = sum(len(c["folders"]) for c in colls)
n_s = sum(len(f["sources"]) for c in colls for f in c["folders"])
n_t = sum(1 for c in colls for f in c["folders"] for s in f["sources"] if s["provider"] == "tmdb")

page = f"""<title>Everything Covers</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@900&family=Geist:wght@400..700&display=swap">
<style>
/* Layout: Nuvio's own black home, one shelf per collection, tiles at their real 16:9 cut. Single dark look on purpose: the covers are made for an AMOLED black app. */
:root {{
  color-scheme: dark;
  --void: #000;
  --panel: #0e0e11;
  --rule: #222228;
  --fg: #f2f2f4;
  --mute: #9a9aa5;
  --pick: #ffcf5a;
  --ui: "Geist", -apple-system, "Helvetica Neue", sans-serif;
  --display: "Big Shoulders Display", "Impact", sans-serif;
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--void); color: var(--fg); font: 15px/1.5 var(--ui); -webkit-font-smoothing: antialiased; }}
.wrap {{ max-width: 1400px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 48px 72px; }}
.eyebrow {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--mute); }}
h1 {{ font: 900 clamp(52px, 8vw, 104px)/.88 var(--display); text-transform: uppercase; margin: 16px 0 18px; text-wrap: balance; }}
.lead {{ max-width: 66ch; color: #c8c8d0; font-size: 17px; margin: 0; }}
.facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 28px 0 8px; }}
.facts div {{ border-left: 2px solid var(--pick); padding: 2px 0 2px 14px; color: var(--mute); font-size: 14px; min-width: 0; }}
.facts b {{ display: block; color: var(--fg); font-weight: 600; }}
section {{ border-top: 1px solid var(--rule); padding-block: 26px; }}
.sh {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 16px; margin-bottom: 14px; }}
h2 {{ font-size: 22px; letter-spacing: -.01em; margin: 0; text-wrap: balance; }}
.sh p {{ margin: 0; color: var(--mute); font-size: 14px; }}
.track {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(232px, 1fr)); gap: 12px; }}
figure {{ margin: 0; min-width: 0; }}
figure img {{ display: block; width: 100%; max-width: 100%; height: auto; aspect-ratio: 16 / 9; border-radius: 10px; background: var(--panel); }}
figcaption {{ display: flex; justify-content: space-between; gap: 8px; font-size: 13px; margin-top: 6px; }}
figcaption span:last-child {{ color: var(--mute); font-variant-numeric: tabular-nums; }}
details {{ margin-top: 16px; }}
summary {{ cursor: pointer; color: var(--mute); font-size: 14px; width: fit-content; }}
summary:hover, summary:focus-visible {{ color: var(--fg); }}
summary:focus-visible {{ outline: 2px solid var(--pick); outline-offset: 3px; border-radius: 4px; }}
.lists {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px 22px; margin-top: 14px; }}
.lists div {{ min-width: 0; }}
.lists h4 {{ margin: 0 0 4px; font-size: 14px; }}
.lists ol {{ margin: 0; padding-left: 20px; color: var(--mute); font-size: 13px; }}
footer {{ border-top: 1px solid var(--rule); padding-top: 26px; color: var(--mute); max-width: 72ch; }}
footer strong {{ color: var(--fg); }}
</style>
<div class="wrap">
  <header>
    <div class="eyebrow"><span>Aurora Glass · A4 Glass Type</span><span>Top 10 · T2 Aurora Flow</span><span>Nuvio 0.1.30</span></div>
    <h1>Everything<br>Covers</h1>
    <p class="lead">All {n_f} covers as exported, with the 12 Top 10 loops playing. On the Mac Nuvio shows the still and plays the loop while you hover; the iPhone loops it all the time.</p>
    <div class="facts">
      <div><b>{n_f} covers, 1600×900</b>WebP stills, about 65 KB each.</div>
      <div><b>12 Top 10 loops</b>512×288 animated WebP, 10 frames a second, 3.6 s, about 190 KB each.</div>
      <div><b>{n_s} rows across 7 collections</b>{n_s - n_t} from Everything Metadata, {n_t} read from TMDB by Nuvio itself.</div>
      <div><b>Small fixes over the lab</b>A soft corner shade so names stay readable on bright stills, and logos sized by area so Paramount+ weighs the same as Netflix.</div>
    </div>
  </header>
  {"".join(sections)}
  <footer><p><strong>Not imported yet.</strong> Nuvio loads covers from a public web address, so they go online before the import file can point at them. Importing replaces the Streaming Services and Genres collections on this profile.</p></footer>
</div>
"""
open(os.path.join(OUT, "index.html"), "w").write(page)
print(f"{n_f} folders, {n_s} rows -> {OUT}/index.html")
