"""Nuvio import files for the four production looks, one per look, beside the Aurora Glass original.

Usage: python3 -I build/style_collections.py RENDER_DIR TAG
  RENDER_DIR  export_styles.cjs output (RENDER_DIR/<look>/covers, RENDER_DIR/<look>/anim)
  TAG         git tag the covers are published under, e.g. v2
Each file is everything-collections.json (validated against the addon config by everything.py) with only the
cover and hover-loop URLs swapped, so every folder, row and source is the same as v1. Covers are served from
raw.githubusercontent.com/mali-king/nuvio-everything/<TAG>/styles/<look>/. Checks that every URL it writes
points at a file that was rendered. Writes RENDER_DIR/<look>/<look>.json (compact, the file to paste).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1 = "https://raw.githubusercontent.com/mali-king/nuvio-everything/v1/"
LOOKS = ["polaroid-table", "arcade", "riso-zine", "hype-reel"]


def main():
    render, tag = sys.argv[1], sys.argv[2]
    src = json.load(open(os.path.join(ROOT, "everything-collections.json")))
    for look in LOOKS:
        base = f"https://raw.githubusercontent.com/mali-king/nuvio-everything/{tag}/styles/{look}/"
        out, missing = json.loads(json.dumps(src)), []
        for coll in out:
            for f in coll["folders"]:
                for field in ("coverImageUrl", "focusGifUrl"):
                    url = f.get(field)
                    if not url:
                        continue
                    assert url.startswith(V1), url
                    rel = url[len(V1):]
                    if not os.path.exists(os.path.join(render, look, rel)):
                        missing.append(rel)
                    f[field] = base + rel
        if missing:
            sys.exit(f"{look}: not rendered: {missing[:5]} ({len(missing)} in all)")
        path = os.path.join(render, look, f"{look}.json")
        with open(path, "w") as fh:
            json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
        n = sum(len(c["folders"]) for c in out)
        a = sum(1 for c in out for f in c["folders"] if f.get("focusGifUrl"))
        print(f"{look:15} {n} folders, {a} animated -> {path}")


if __name__ == "__main__":
    main()
