"""Art for the four production looks (Polaroid Table, Arcade, Riso Zine, Hype Reel) on all 78 folders.

Usage: python3 -I build/styles_assets.py
  board/assets/st/still/<key>.jpg  1920x1080 still per folder: v1's still, a new one for each Top 10 folder
                                   (v1 drew those with no photo), and a textless one where v1's carried a title
  board/assets/st/cut/<key>.png    Vision cut-out of each still (Hype break-out, Riso subject plate)
  board/assets/st/bd/<name>.jpg    w780 textless backdrops of other titles in the folder (Polaroid backs)
  board/styles.js                  window.PD: folder key -> {still, cut, box, lum, bd}
Every title is used once across the whole collection, so neighbouring tiles never repeat a film.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = os.environ.get("TMDB_API_KEY") or open(os.path.join(ROOT, "build", ".tmdbkey")).read().strip()
UA = {"User-Agent": "curl/8.7.1"}
ST = os.path.join(ROOT, "board", "assets", "st")
HI = os.path.join(ROOT, "board", "assets", "hi", "still")
RD = os.path.join(ROOT, "board", "assets", "rd", "still")
N_BD = 3

# Stills v1 did not have (Top 10) or should not reuse (a title burned into the art).
TOP = {
    "top-10-today--kenya": "rd",              # Wednesday, as on the boards
    "top-10-today--netflix": "tv:91239",      # Bridgerton
    "top-10-today--prime-video": "tv:106379",  # Fallout
    "top-10-today--disney-plus": "tv:82856",  # The Mandalorian
    "top-10-today--hbo-max": "rd",            # The White Lotus, as on the boards
    "top-10-today--apple-tv": "tv:125988",    # Silo
    "top-10-today--paramount-plus": "tv:153312",  # Tulsa King
    "top-10-today--hulu": "tv:126308",        # Shogun
    "top-10-today--peacock": "tv:2316",       # The Office
    "top-10-today--crunchyroll": "tv:209867",  # Frieren
    "top-10-today--jiohotstar": "movie:1291608",  # Dhurandhar
    "top-10-today--zee5": "tv:127332",        # Sunflower
}
TEXTLESS = {
    "streaming-services--aha": "movie:23790",  # Magadheera (Krack's art all carries its title)
    "streaming-services--hoichoi": "tv:207305",  # Karagar (Byomkesh has no textless art)
}

# v1 stills that came from local files, so the backs never repeat them; and art with a title burned in.
LOCAL = [("tv", "Sherlock", 2010), ("movie", "Paddington 2", 2017), ("movie", "Inside Out 2", 2024),
         ("movie", "Godzilla Minus One", 2023), ("movie", "Miracle in Cell No. 7", 2019), ("movie", "Hero", 2002),
         ("tv", "The Walking Dead", 2010), ("movie", "Ip Man", 2008), ("movie", "Stand by Me", 1986),
         ("movie", "Home Alone", 1990), ("movie", "Krack", 2021)]
EXCLUDE = {("movie", "Prem Granth")}

# Polaroid backs: TMDB discover queries per folder, as (kind, params); the first titles with a textless backdrop win.
US = {"watch_region": "US"}


def net(n, prov=None):
    q = [("tv", {"with_networks": n, "sort_by": "popularity.desc", "vote_count.gte": 150})]
    if prov:
        q.append(("movie", {"with_watch_providers": prov, **US, "sort_by": "popularity.desc", "vote_count.gte": 300}))
    return q


def india(prov):
    return [("movie", {"with_watch_providers": prov, "watch_region": "IN", "with_origin_country": "IN",
                       "sort_by": "popularity.desc", "vote_count.gte": 5}),
            ("tv", {"with_watch_providers": prov, "watch_region": "IN", "with_origin_country": "IN",
                    "sort_by": "popularity.desc", "vote_count.gte": 3, "without_genres": "10763|10767|10766"})]


def genre(g, kind="movie"):
    return [(kind, {"with_genres": g, "sort_by": "vote_count.desc"})]


def lang(code, kind="movie", **extra):
    return [(kind, {"with_original_language": code, "sort_by": "vote_count.desc", **extra})]


def kw(k, kind="movie", n=100):
    return [(kind, {"with_keywords": k, "sort_by": "vote_count.desc", "vote_count.gte": n})]


def decade(a):
    return [("movie", {"primary_release_date.gte": f"{a}-01-01", "primary_release_date.lte": f"{a + 9}-12-31",
                       "sort_by": "vote_count.desc"})]


BEST_PICTURE = ["Everything Everywhere All at Once", "Nomadland", "Moonlight", "The Shape of Water", "Birdman",
                "No Country for Old Men", "Slumdog Millionaire", "Gladiator", "Titanic", "The Departed", "Anora",
                "CODA", "Spotlight", "Argo"]
BACKS = {
    "top-10-today--kenya": [("tv", {"with_networks": 213, "sort_by": "popularity.desc", "vote_count.gte": 300})],
    "top-10-today--netflix": [("movie", {"with_watch_providers": 8, **US, "sort_by": "popularity.desc", "vote_count.gte": 300})] + net(213),
    "top-10-today--prime-video": net(1024, 9),
    "top-10-today--disney-plus": net(2739, 337),
    "top-10-today--hbo-max": net("49|3186", 1899),
    "top-10-today--apple-tv": net(2552, 350),
    "top-10-today--paramount-plus": net(4330, 531),
    "top-10-today--hulu": net(453, 15),
    "top-10-today--peacock": net(3353, 386),
    "top-10-today--crunchyroll": [("tv", {"with_watch_providers": 283, **US, "with_genres": 16, "sort_by": "popularity.desc", "vote_count.gte": 200})],
    "top-10-today--jiohotstar": india(2336),
    "top-10-today--zee5": india(232),
    "streaming-services--netflix": [("tv", {"with_networks": 213, "sort_by": "vote_count.desc"})],
    "streaming-services--prime-video": [("tv", {"with_networks": 1024, "sort_by": "vote_count.desc"})],
    "streaming-services--disney-plus": [("tv", {"with_networks": 2739, "sort_by": "vote_count.desc"})],
    "streaming-services--hbo-max": [("tv", {"with_networks": "49|3186", "sort_by": "vote_count.desc"})],
    "streaming-services--apple-tv": [("tv", {"with_networks": 2552, "sort_by": "vote_count.desc"})],
    "streaming-services--paramount-plus": [("tv", {"with_networks": 4330, "sort_by": "vote_count.desc"})],
    "streaming-services--hulu": [("tv", {"with_networks": 453, "sort_by": "vote_count.desc"})],
    "streaming-services--peacock": [("tv", {"with_networks": 3353, "sort_by": "vote_count.desc"})],
    "streaming-services--crunchyroll": [("tv", {"with_watch_providers": 283, **US, "with_genres": 16, "sort_by": "vote_count.desc"})],
    "streaming-services--jiohotstar": india(2336),
    "streaming-services--sonyliv": india(237),
    "streaming-services--zee5": india(232),
    "streaming-services--sun-nxt": india(309),
    "streaming-services--aha": india(532),
    "streaming-services--hoichoi": india(315),
    "streaming-services--amazon-mx-player": india("1898|515"),
    "streaming-services--manoramamax": india(482),
    "streaming-services--shemaroome": india(474),
    "streaming-services--epic-on": india(476),
    "streaming-services--hungama-play": india(437),
    "streaming-services--lionsgate-play": [("movie", {"with_watch_providers": 561, "watch_region": "IN", "sort_by": "popularity.desc", "vote_count.gte": 200})],
    "genres--action": genre(28),
    "genres--comedy": genre(35),
    "genres--drama": genre(18),
    "genres--thriller": genre(53),
    "genres--horror": genre(27),
    "genres--sci-fi": genre(878),
    "genres--romance": genre(10749),
    "genres--mystery": genre(9648),
    "genres--family": genre(10751),
    "genres--animation": genre(16),
    "genres--documentary": [("tv", {"with_genres": 99, "sort_by": "vote_count.desc"}), ("movie", {"with_genres": 99, "sort_by": "vote_count.desc"})],
    "around-the-world--k-drama": lang("ko", "tv", with_genres=18),
    "around-the-world--anime": [("tv", {"with_original_language": "ja", "with_genres": 16, "sort_by": "vote_count.desc"})],
    "around-the-world--indian": lang("hi") + lang("te") + lang("ta"),
    "around-the-world--african": [("movie", {"with_origin_country": "NG|ZA|KE|GH|EG", "sort_by": "popularity.desc", "vote_count.gte": 20})],
    "around-the-world--japanese": lang("ja", without_genres=16),
    "around-the-world--spanish": lang("es", "tv", with_origin_country="ES") + lang("es", with_origin_country="ES"),
    "around-the-world--french": lang("fr"),
    "around-the-world--turkish": lang("tr", "tv") + lang("tr"),
    "around-the-world--chinese": lang("zh") + lang("cn"),
    "moods-and-themes--spooky-season": kw(3335, n=50),
    "moods-and-themes--true-crime": kw(33722, "tv", 20) + kw(33722, n=20),
    "moods-and-themes--heists": kw(10051),
    "moods-and-themes--time-travel": kw(4379),
    "moods-and-themes--superheroes": kw(9715, n=200),
    "moods-and-themes--dystopian-futures": kw("4565|4458", n=200),
    "moods-and-themes--zombies": kw(12377),
    "moods-and-themes--serial-killers": kw(10714, "tv", 30),
    "moods-and-themes--spies": kw(470, n=200),
    "moods-and-themes--martial-arts": kw(779),
    "moods-and-themes--true-stories": kw(9672, n=300),
    "moods-and-themes--space-and-cyberpunk": kw("161176|12190"),
    "moods-and-themes--coming-of-age": kw(10683, n=300),
    "moods-and-themes--christmas": kw(207317, n=50),
    "the-canon--imdb-top-250": [("movie", {"sort_by": "vote_average.desc", "vote_count.gte": 15000})],
    "the-canon--best-picture": "best",
    "the-canon--letterboxd-250": [("movie", {"sort_by": "vote_average.desc", "vote_count.gte": 2500, "primary_release_date.lte": "1995-12-31"})],
    "the-canon--a24": [("movie", {"with_companies": 41077, "sort_by": "vote_count.desc"})],
    "the-canon--top-rated": [("movie", {"sort_by": "vote_average.desc", "vote_count.gte": 8000, "primary_release_date.gte": "1996-01-01"})],
    "decades--70s": decade(1970),
    "decades--80s": decade(1980),
    "decades--90s": decade(1990),
    "decades--2000s": decade(2000),
    "decades--2010s": decade(2010),
    "decades--2020s": decade(2020),
}

# Hand-picked backs where a query lands on the wrong films; (kind, title, year), searched on TMDB.
CURATED = {
    "top-10-today--kenya": [("tv", "Black Mirror", 2011), ("tv", "Ozark", 2017), ("tv", "The Witcher", 2019)],
    "top-10-today--netflix": [("tv", "Adolescence", 2025), ("movie", "KPop Demon Hunters", 2025), ("tv", "The Diplomat", 2023)],
    "top-10-today--prime-video": [("tv", "Reacher", 2022), ("tv", "The Lord of the Rings: The Rings of Power", 2022), ("tv", "The Summer I Turned Pretty", 2022)],
    "top-10-today--disney-plus": [("tv", "Loki", 2021), ("tv", "Percy Jackson and the Olympians", 2023), ("tv", "Daredevil: Born Again", 2025)],
    "top-10-today--hbo-max": [("tv", "Game of Thrones", 2011), ("tv", "The Pitt", 2025), ("tv", "Succession", 2018)],
    "top-10-today--hulu": [("tv", "The Handmaid's Tale", 2017), ("tv", "Paradise", 2025), ("tv", "Futurama", 1999)],
    "top-10-today--peacock": [("tv", "Poker Face", 2023), ("tv", "Love Island USA", 2019), ("tv", "Yellowstone", 2018)],
    "top-10-today--crunchyroll": [("tv", "Dan Da Dan", 2024), ("tv", "Jujutsu Kaisen", 2020), ("tv", "Chainsaw Man", 2022)],
    "genres--action": [("movie", "Die Hard", 1988), ("movie", "Gladiator", 2000), ("movie", "Heat", 1995)],
    "genres--comedy": [("movie", "Superbad", 2007), ("movie", "The Hangover", 2009), ("movie", "Barbie", 2023)],
    "genres--drama": [("movie", "The Social Network", 2010), ("movie", "Titanic", 1997), ("movie", "Marriage Story", 2019)],
    "genres--thriller": [("movie", "Nightcrawler", 2014), ("movie", "No Country for Old Men", 2007), ("movie", "Sicario", 2015)],
    "genres--horror": [("movie", "Get Out", 2017), ("movie", "It", 2017), ("movie", "Hereditary", 2018)],
    "genres--sci-fi": [("movie", "Interstellar", 2014), ("movie", "Arrival", 2016), ("movie", "Ex Machina", 2015)],
    "genres--romance": [("movie", "Eternal Sunshine of the Spotless Mind", 2004), ("movie", "Her", 2013), ("movie", "Pride & Prejudice", 2005)],
    "genres--mystery": [("movie", "Gone Girl", 2014), ("movie", "Knives Out", 2019), ("movie", "Shutter Island", 2010)],
    "genres--family": [("movie", "Up", 2009), ("movie", "E.T. the Extra-Terrestrial", 1982), ("movie", "The Wild Robot", 2024)],
    "genres--animation": [("movie", "Spirited Away", 2001), ("movie", "Spider-Man: Into the Spider-Verse", 2018), ("movie", "Toy Story", 1995)],
    "genres--documentary": [("tv", "Planet Earth II", 2016), ("movie", "Free Solo", 2018), ("movie", "My Octopus Teacher", 2020)],
    "moods-and-themes--spooky-season": [("movie", "Hocus Pocus", 1993), ("movie", "Beetlejuice", 1988), ("movie", "Halloween", 1978)],
    "moods-and-themes--true-crime": [("tv", "When They See Us", 2019), ("tv", "Making a Murderer", 2015), ("tv", "Dahmer - Monster: The Jeffrey Dahmer Story", 2022)],
    "moods-and-themes--heists": [("movie", "Baby Driver", 2017), ("movie", "Inside Man", 2006), ("movie", "The Italian Job", 2003)],
    "moods-and-themes--time-travel": [("movie", "Looper", 2012), ("movie", "Tenet", 2020), ("movie", "Edge of Tomorrow", 2014)],
    "moods-and-themes--superheroes": [("movie", "Avengers: Endgame", 2019), ("movie", "Spider-Man: No Way Home", 2021), ("movie", "Wonder Woman", 2017)],
    "moods-and-themes--dystopian-futures": [("movie", "The Hunger Games", 2012), ("movie", "Children of Men", 2006), ("movie", "Snowpiercer", 2013)],
    "moods-and-themes--zombies": [("movie", "Train to Busan", 2016), ("movie", "World War Z", 2013), ("movie", "Zombieland", 2009)],
    "moods-and-themes--serial-killers": [("tv", "Dexter", 2006), ("movie", "The Silence of the Lambs", 1991), ("tv", "Hannibal", 2013)],
    "moods-and-themes--spies": [("movie", "Kingsman: The Secret Service", 2014), ("movie", "Skyfall", 2012), ("movie", "Casino Royale", 2006)],
    "moods-and-themes--martial-arts": [("movie", "Kill Bill: Vol. 1", 2003), ("movie", "Enter the Dragon", 1973), ("movie", "The Raid", 2011)],
    "moods-and-themes--true-stories": [("movie", "The Revenant", 2015), ("movie", "The Imitation Game", 2014), ("movie", "Bohemian Rhapsody", 2018)],
    "moods-and-themes--space-and-cyberpunk": [("movie", "Ghost in the Shell", 1995), ("movie", "Gravity", 2013), ("movie", "The Martian", 2015)],
    "moods-and-themes--coming-of-age": [("movie", "The Perks of Being a Wallflower", 2012), ("movie", "Lady Bird", 2017), ("movie", "Dead Poets Society", 1989)],
    "moods-and-themes--christmas": [("movie", "Elf", 2003), ("movie", "Love Actually", 2003), ("movie", "Klaus", 2019)],
    "the-canon--letterboxd-250": [("movie", "Portrait of a Lady on Fire", 2019), ("movie", "In the Mood for Love", 2000), ("movie", "12 Angry Men", 1957)],
    "decades--2020s": [("movie", "Avatar: The Way of Water", 2022), ("movie", "Soul", 2020), ("movie", "Poor Things", 2023)],
}


def get_json(path, **q):
    q["api_key"] = KEY
    url = f"https://api.themoviedb.org/3/{path}?" + urllib.parse.urlencode(q)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))


def download(url, path):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    with open(path, "wb") as fh:
        fh.write(data)


def textless(kind, tmdb_id, min_w):
    imgs = get_json(f"{kind}/{tmdb_id}/images", include_image_language="null")
    pool = [i for i in imgs.get("backdrops", []) if i.get("iso_639_1") is None and i.get("width", 0) >= min_w]
    pool.sort(key=lambda i: (i.get("vote_average", 0) * min(i.get("vote_count", 0), 10), i.get("width", 0)), reverse=True)
    return pool[0]["file_path"] if pool else None


def crop_1080(raw, dest):
    subprocess.run(["magick", raw, "-resize", "1920x1080^", "-gravity", "center", "-extent", "1920x1080",
                    "-strip", "-quality", "88", dest], check=True)


def ref_id(ref):
    return tuple(ref.split(":")) if ref and ":" in ref else None


def candidates(spec):
    if spec and len(spec[0]) == 3:
        for kind, title, year in spec:
            yk = "first_air_date_year" if kind == "tv" else "year"
            res = get_json(f"search/{kind}", query=title, **{yk: year})["results"]
            if not res:
                sys.exit(f"not found: {kind} {title} {year}")
            yield kind, res[0]
        return
    if spec == "best":
        for title in BEST_PICTURE:
            res = get_json("search/movie", query=title)["results"]
            if res:
                yield "movie", res[0]
        return
    for kind, params in spec:
        for page in (1, 2, 3):
            for r in get_json(f"discover/{kind}", include_adult="false", page=page, **params)["results"]:
                yield kind, r


def main():
    for d in ("still", "cut", "bd"):
        os.makedirs(os.path.join(ST, d), exist_ok=True)
    stills = json.load(open(os.path.join(ROOT, "build", "stills.json")))
    keys = list(TOP) + list(stills)
    used = set()
    for k, src in stills.items():
        if ref_id(src):
            used.add(ref_id(src))
    for src in list(TOP.values()) + list(TEXTLESS.values()):
        if ref_id(src):
            used.add(ref_id(src))
    used |= {("tv", "119051"), ("tv", "111803")}  # Wednesday, The White Lotus
    for kind, title, year in LOCAL:
        yk = "first_air_date_year" if kind == "tv" else "year"
        res = get_json(f"search/{kind}", query=title, **{yk: year})["results"]
        used.add((kind, str(res[0]["id"])))

    # stills
    for k in keys:
        dest = os.path.join(ST, "still", f"{k}.jpg")
        if os.path.exists(dest):
            continue
        src = TOP.get(k) or TEXTLESS.get(k)
        if src == "rd":
            os.symlink(os.path.join(RD, f"{k}.jpg"), dest)
        elif src:
            kind, tid = ref_id(src)
            path = textless(kind, tid, 1280)
            if not path:
                sys.exit(f"{k}: no textless backdrop for {src}")
            raw = dest + ".orig.jpg"
            download(f"https://image.tmdb.org/t/p/original{path}", raw)
            crop_1080(raw, dest)
            os.remove(raw)
            print(f"still {k:44} {src} {path}")
        else:
            os.symlink(os.path.join(HI, f"{k}.jpg"), dest)

    # cut-outs
    todo = []
    for k in keys:
        cut = os.path.join(ST, "cut", f"{k}.png")
        if not os.path.exists(cut):
            todo += [os.path.join(ST, "still", f"{k}.jpg"), cut]
    if todo:
        subprocess.run([os.path.join(ROOT, "build", "cutout"), *todo], check=False)

    # polaroid backs
    cache_path = os.path.join(ST, "bd.json")
    backs = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    for k in keys:
        for b in backs.get(k, []):
            used.add((b["kind"], str(b["id"])))
    for k in keys:
        if len(backs.get(k, [])) >= N_BD:
            continue
        got = []
        for kind, r in candidates(CURATED.get(k) or BACKS[k]):
            ident = (kind, str(r["id"]))
            if ident in used or (kind, r.get("title") or r.get("name")) in EXCLUDE:
                continue
            path = textless(kind, r["id"], 780)
            if not path:
                continue
            name = path.strip("/").rsplit(".", 1)[0]
            dest = os.path.join(ST, "bd", f"{name}.jpg")
            if not os.path.exists(dest):
                download(f"https://image.tmdb.org/t/p/w780{path}", dest)
            used.add(ident)
            got.append({"kind": kind, "id": r["id"], "title": r.get("title") or r.get("name"), "img": name})
            if len(got) == N_BD:
                break
        backs[k] = got
        print(f"backs {k:44} {[g['title'] for g in got]}")
        json.dump(backs, open(cache_path, "w"), indent=1, ensure_ascii=False)

    # subject box and brightness per still
    data = {}
    for k in keys:
        still, cut = os.path.join(ST, "still", f"{k}.jpg"), os.path.join(ST, "cut", f"{k}.png")
        rec = {"still": f"st/still/{k}.jpg", "bd": [b["img"] for b in backs[k]]}
        if os.path.exists(cut):
            geo = subprocess.run(["magick", cut, "-alpha", "extract", "-threshold", "50%", "-format", "%@ %w %h %[fx:mean]", "info:"],
                                 capture_output=True, text=True, check=True).stdout.split()
            m = re.match(r"(\d+)x(\d+)\+(\d+)\+(\d+)", geo[0])
            w, h, x, y = map(float, m.groups())
            fw, fh = float(geo[1]), float(geo[2])
            rec["cut"] = f"st/cut/{k}.png"
            rec["box"] = [round(100 * x / fw, 1), round(100 * y / fh, 1), round(100 * w / fw, 1), round(100 * h / fh, 1)]
            rec["area"] = round(float(geo[3]), 3)  # share of the frame the subject covers
        else:
            rec["box"] = [30, 15, 40, 70]
            rec["area"] = 0
        rec["lum"] = round(float(subprocess.run(["magick", still, "-colorspace", "gray", "-format", "%[fx:mean]", "info:"],
                                                capture_output=True, text=True, check=True).stdout), 3)
        data[k] = rec
    with open(os.path.join(ROOT, "board", "styles.js"), "w") as fh:
        fh.write("// Generated by build/styles_assets.py. Folder key -> art for the production looks.\n")
        fh.write("window.PD = " + json.dumps(data, indent=1) + ";\n")
    print(len(data), "folders")


if __name__ == "__main__":
    main()
