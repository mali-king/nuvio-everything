"""Fetch textless backdrops and English title logos from TMDB for the design board.

Usage: python3 -I fetch_art.py SPEC.json OUT_DIR
SPEC maps a name to "movie:<tmdb id>" or "tv:<tmdb id>". Writes OUT_DIR/<name>.bd.jpg,
OUT_DIR/<name>.logo.png (when TMDB has one) and OUT_DIR/art.json describing what it got.
"""
import json
import os
import sys
import urllib.request

KEY = os.environ.get("TMDB_API_KEY") or open(os.path.join(os.path.dirname(__file__), ".tmdbkey")).read().strip()
UA = {"User-Agent": "curl/8.7.1"}


def get_json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))


def download(url, path):
    if os.path.exists(path):
        return
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    with open(path, "wb") as fh:
        fh.write(data)


def best(images, lang):
    pool = [i for i in images if i.get("iso_639_1") == lang]
    pool.sort(key=lambda i: (i.get("vote_average", 0) * min(i.get("vote_count", 0), 10), i.get("width", 0)), reverse=True)
    return pool[0] if pool else None


def fetch(name, ref, out, size="w1280"):
    media, tmdb_id = ref.split(":")
    base = f"https://api.themoviedb.org/3/{media}/{tmdb_id}"
    info = get_json(f"{base}?api_key={KEY}")
    imgs = get_json(f"{base}/images?api_key={KEY}&include_image_language=en,null")
    bd = best(imgs.get("backdrops", []), None) or best(imgs.get("backdrops", []), "en")
    logo = best([l for l in imgs.get("logos", []) if l["file_path"].endswith(".png")], "en")
    rec = {"ref": ref, "title": info.get("title") or info.get("name"),
           "year": (info.get("release_date") or info.get("first_air_date") or "")[:4]}
    if bd:
        download(f"https://image.tmdb.org/t/p/{size}{bd['file_path']}", os.path.join(out, f"{name}.bd.jpg"))
        rec["backdrop"] = bd["file_path"]
    if logo:
        download(f"https://image.tmdb.org/t/p/w500{logo['file_path']}", os.path.join(out, f"{name}.logo.png"))
        rec["logo"] = logo["file_path"]
    return rec


def main():
    spec, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    manifest_path = os.path.join(out, "art.json")
    art = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    for name, ref in spec.items():
        if art.get(name, {}).get("ref") == ref:
            continue
        try:
            art[name] = fetch(name, ref, out)
            print(f"{name:28} {art[name]['title']} ({art[name]['year']})"
                  f"{'' if 'backdrop' in art[name] else '  NO BACKDROP'}{'' if 'logo' in art[name] else '  no logo'}")
        except Exception as exc:  # report and keep going
            print(f"{name:28} FAILED {exc}")
    json.dump(art, open(manifest_path, "w"), indent=1)


if __name__ == "__main__":
    main()
