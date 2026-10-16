"""Fetch each cover's still at full resolution and crop it to 1920x1080.

Usage: python3 -I hires.py STILLS.json ART.json OUT_DIR
STILLS maps a folder key to "movie:<id>" / "tv:<id>" or a local image. A ref the design board
already used (ART.json) keeps the same backdrop; otherwise the best textless backdrop is picked.
"""
import json
import os
import subprocess
import sys
import urllib.request

KEY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmdbkey")).read().strip()
UA = {"User-Agent": "curl/8.7.1"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def best_backdrop(ref):
    media, tmdb_id = ref.split(":")
    imgs = json.loads(get(f"https://api.themoviedb.org/3/{media}/{tmdb_id}/images?api_key={KEY}"
                          f"&include_image_language=en,null"))
    for lang in (None, "en"):
        pool = [i for i in imgs.get("backdrops", []) if i.get("iso_639_1") == lang and i.get("width", 0) >= 1280]
        pool.sort(key=lambda i: (i.get("vote_average", 0) * min(i.get("vote_count", 0), 10), i.get("width", 0)),
                  reverse=True)
        if pool:
            return pool[0]["file_path"]
    raise RuntimeError(f"no backdrop for {ref}")


def main():
    stills, art, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
    os.makedirs(out, exist_ok=True)
    known = {v["ref"]: v["backdrop"] for v in art.values() if v.get("backdrop")}
    for k, src in stills.items():
        dest = os.path.join(out, f"{k}.jpg")
        if os.path.exists(dest):
            continue
        if src.startswith("/"):
            raw, how = src, "local"
        else:
            path = known.get(src) or best_backdrop(src)
            raw = os.path.join(out, f".{k}.orig.jpg")
            with open(raw, "wb") as fh:
                fh.write(get(f"https://image.tmdb.org/t/p/original{path}"))
            how = f"{src} {path}"
        subprocess.run(["magick", raw, "-resize", "1920x1080^", "-gravity", "center", "-extent", "1920x1080",
                        "-strip", "-quality", "88", dest], check=True)
        if raw.startswith(out):
            os.remove(raw)
        print(f"{k:42} {how}")


if __name__ == "__main__":
    main()
