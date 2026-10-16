"""The Everything collection: 7 Home rows, 78 folders, Aurora Glass covers (A4 Glass Type,
Top 10 animated with T2 Aurora Flow). One spec drives the covers and the Nuvio import file.

Usage: python3 -I everything.py CONFIG.json COVER_BASE
  CONFIG.json  the merged Everything Metadata export (merge_config.py output)
  COVER_BASE   public URL prefix the covers are served from, ending in "/"
Writes board/folders.js (what the cover page draws), build/stills.json (art to fetch) and
everything-collections.json (the import file, plus a .min copy to paste). Every addon source is checked against CONFIG.
"""
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NS = uuid.UUID("6f1c3a8e-2b7d-4e55-9a51-0c7e1d2f4b90")
ADDON_ID, ADDON_NAME = "aio-metadata", "Everything Metadata"
NO_TALK = "10763|10767|10766"  # news, talk, soap


# ------------------------------------------------------------------ sources
def addon(cid, typ):
    return {"addon": (cid, typ)}


def tmdb(title, media, sort=None, **filters):
    s = {"provider": "tmdb", "tmdbSourceType": "DISCOVER", "title": title, "mediaType": media}
    if sort:
        s["sortBy"] = sort
    s["filters"] = filters
    return s


def both(cid):
    return [addon(cid, "movie"), addon(cid, "series")]


def mdb(*ids):
    """mdblist ids as (movie, series) pairs or single movie ids."""
    out = []
    for i in ids:
        if isinstance(i, tuple):
            out += [addon(f"mdblist.{i[0]}", "movie"), addon(f"mdblist.{i[1]}", "series")]
        else:
            out.append(addon(f"mdblist.{i}", "movie"))
    return out


def flix(service, country):
    if service in ("crunchyroll", "hotstar", "zee5"):
        return [addon(f"flixpatrol.{service}.{country}.all", "all")]
    return [addon(f"flixpatrol.{service}.{country}.movie", "movie"),
            addon(f"flixpatrol.{service}.{country}.series", "series")]


def disc(typ, slug, n):
    return addon(f"tmdb.discover.{typ}.{slug}.mgt7x0{n:02d}", typ)


def provider_rows(pid, series=True):
    """Indian services Everything Metadata does not carry; Nuvio reads them from TMDB."""
    f = {"withWatchProviders": str(pid), "watchRegion": "IN"}
    rows = [tmdb("Popular Movies", "movie", voteCountGte=3, **f),
            tmdb("New Movies", "movie", "primary_release_date.desc", voteCountGte=1, **f)]
    if series:
        rows += [tmdb("Popular Series", "tv", voteCountGte=1, withoutGenres=NO_TALK, **f),
                 tmdb("New Series", "tv", "first_air_date.desc", voteCountGte=1, withoutGenres=NO_TALK, **f)]
    rows.append(tmdb("Top Rated Movies", "movie", "vote_average.desc", voteCountGte=15, **f))
    return rows


def language_rows(lang, series_name, extra=None, movie_lang=None):
    f = dict(extra or {})
    ml = movie_lang or lang
    tv = {**f, "withoutGenres": "|".join(filter(None, [f.get("withoutGenres"), NO_TALK]))}
    return [tmdb("Popular Movies", "movie", voteCountGte=30, withOriginalLanguage=ml, **f),
            tmdb(f"Popular {series_name}", "tv", voteCountGte=20, withOriginalLanguage=lang, **tv),
            tmdb("New Movies", "movie", "primary_release_date.desc", voteCountGte=10,
                 withOriginalLanguage=ml, **f),
            tmdb(f"New {series_name}", "tv", "first_air_date.desc", voteCountGte=5,
                 withOriginalLanguage=lang, **tv),
            tmdb("Top Rated Movies", "movie", "vote_average.desc", voteCountGte=300,
                 withOriginalLanguage=ml, **f)]


def genre(pop, top, new):
    out = []
    for pair in (pop, top, new):
        if pair is None:
            continue
        m, s = pair
        out.append(addon(f"mdblist.{m}", "movie"))
        if s:
            out.append(addon(f"mdblist.{s}", "series"))
    return out


# ------------------------------------------------------------------ folders
# kind: top (glass panel, brand light, animated) | svc (service logo over the film) | name (glass type)
# still: TMDB ref "movie:<id>" / "tv:<id>", or a local image path.
NC = "/Users/elmarco/Projects/nuvio-collections/build/assets/img/"


def top(slug, title, logo, c1, c2, where, sources, ke=False):
    return dict(slug=slug, title=title, kind="top", logo=logo, c1=c1, c2=c2, where=where, ke=ke,
                sources=sources)


def svc(slug, title, still, c1, sources, logo=None):
    return dict(slug=slug, title=title, kind="svc", still=still, c1=c1, logo=logo, sources=sources)


def name(slug, title, still, sources):
    return dict(slug=slug, title=title, kind="name", still=still, sources=sources)


COLLECTIONS = [
    ("Top 10 Today", "top-10-today", "TABBED_GRID", [
        top("kenya", "Kenya", "netflix", "#c4121a", "#0b6b2a", "Kenya", flix("netflix", "ke"), ke=True),
        top("netflix", "Netflix", "netflix", "#e50914", "#3a0006", "Today", flix("netflix", "us")),
        top("prime-video", "Prime Video", "prime-video", "#1a98ff", "#03204a", "Today", flix("amazon-prime", "us")),
        top("disney-plus", "Disney+", "disney-plus", "#2350ff", "#0a1a5c", "Today", flix("disney", "us")),
        top("hbo-max", "HBO Max", "hbo-max", "#9b3bff", "#2a0660", "Today", flix("hbo-max", "us")),
        top("apple-tv", "Apple TV+", "apple-tv", "#8a8a98", "#1c1c22", "Today", flix("apple-tv", "us")),
        top("paramount-plus", "Paramount+", "paramount-plus", "#0a64ff", "#001a4d", "Today", flix("paramount", "us")),
        top("hulu", "Hulu", "hulu", "#1ce783", "#003d22", "Today", flix("hulu", "us")),
        top("peacock", "Peacock", "peacock", "#f5a300", "#3b0a63", "Today", flix("peacock", "us")),
        top("crunchyroll", "Crunchyroll", "crunchyroll", "#f47521", "#4a1a00", "Today", flix("crunchyroll", "us")),
        top("jiohotstar", "JioHotstar", "jiohotstar", "#7b3cff", "#0b1f6b", "India", flix("hotstar", "in")),
        top("zee5", "ZEE5", "zee5", "#a438e8", "#2a0a40", "India", flix("zee5", "in")),
    ]),
    ("Streaming Services", "streaming-services", "ROWS", [
        svc("netflix", "Netflix", "tv:66732", "#e50914", flix("netflix", "ke") + mdb((88328, 88329), (86752, 86751)), "netflix"),
        svc("prime-video", "Prime Video", "tv:76479", "#1a98ff", flix("amazon-prime", "us") + mdb((88332, 88333), (86755, 86753)), "prime-video"),
        svc("disney-plus", "Disney+", "tv:83867", "#2350ff", flix("disney", "us") + mdb((88322, 88323), (86759, 86758)), "disney-plus"),
        svc("hbo-max", "HBO Max", "tv:100088", "#9b3bff", flix("hbo-max", "us") + mdb((88324, 88325), (89647, 89649)), "hbo-max"),
        svc("apple-tv", "Apple TV+", "tv:95396", "#8a8a98", flix("apple-tv", "us") + mdb((88317, 88319), (86757, 86756)), "apple-tv"),
        svc("paramount-plus", "Paramount+", "tv:157741", "#0a64ff", flix("paramount", "us") + mdb((88330, 88331), (86762, 86761)), "paramount-plus"),
        svc("hulu", "Hulu", "tv:136315", "#1ce783", flix("hulu", "us") + mdb((88326, 88327), (216816, 216834)), "hulu"),
        svc("peacock", "Peacock", "tv:222766", "#f5a300", flix("peacock", "us") + mdb((84239, 84240)), "peacock"),
        svc("crunchyroll", "Crunchyroll", "tv:127532", "#f47521", flix("crunchyroll", "us") + mdb((98862, 99202)), "crunchyroll"),
        svc("jiohotstar", "JioHotstar", "tv:104913", "#7b3cff", flix("hotstar", "in") + [disc("movie", "jiohotstar", 0), disc("series", "jiohotstar", 1)], "jiohotstar"),
        svc("sonyliv", "SonyLIV", "tv:111188", "#e8b400", [disc("movie", "sonyliv", 2), disc("series", "sonyliv", 3)]),
        svc("zee5", "ZEE5", "movie:1123960", "#a438e8", flix("zee5", "in") + [disc("movie", "zee5", 4), disc("series", "zee5", 5)], "zee5"),
        svc("sun-nxt", "Sun NXT", "movie:937020", "#ff6a00", [disc("movie", "sun_nxt", 6)]),
        svc("aha", "aha", "movie:784572", "#ff6b00", [disc("movie", "aha", 7)], "aha"),
        svc("hoichoi", "Hoichoi", "tv:75964", "#e3262f", [disc("movie", "hoichoi", 8)], "hoichoi"),
        svc("amazon-mx-player", "Amazon MX Player", "tv:107588", "#2f7cff", [disc("movie", "amazon_mx_player", 9)]),
        svc("manoramamax", "ManoramaMAX", "movie:1069945", "#e8262c", provider_rows(482, series=False)),
        svc("shemaroome", "ShemarooMe", "movie:12259", "#ffb000", provider_rows(474, series=False)),
        svc("epic-on", "EPIC ON", "tv:136552", "#d4a017", provider_rows(476)),
        svc("hungama-play", "Hungama Play", "movie:14752", "#ff2d55", provider_rows(437)),
        svc("lionsgate-play", "Lionsgate Play", "movie:603692", "#ff7a00", provider_rows(561)),
    ]),
    ("Genres", "genres", "ROWS", [
        name("action", "Action", "movie:76341", genre((91211, 91213), (2407, 45762), (128037, 128029))),
        name("comedy", "Comedy", "movie:120467", genre((91223, 91224), (2195, 45764), (128040, 128041))),
        name("drama", "Drama", "movie:244786", genre((91296, 91297), (2408, 45766), (128043, 128044))),
        name("thriller", "Thriller", "movie:146233", genre((91893, 91894), None, (128049, 128050))),
        name("horror", "Horror", "movie:1233413", genre((91215, 91217), (2410, 10665), (128045, 128046))),
        name("sci-fi", "Sci-Fi", "movie:693134", genre((91220, 91221), (2412, 79476), (128047, 128048))),
        name("romance", "Romance", "movie:313369", genre((128262, 128265), None, (128261, 128264))),
        name("mystery", "Mystery", NC + "bd_8rvLEmdI4gLrMO1rLqbNdnNcPFE.jpg", genre(None, (2416, 45183), None)),
        name("family", "Family", NC + "bd_iJgNOTSBNrC90U2xyYq9ln0b35o.jpg", genre((24262, 147641), (2415, 157286), (76113, 59967))),
        name("animation", "Animation", NC + "bd_jJKZaTBNenlFclQyjrnvzkRmvWE.jpg", genre((116037, 116038), (69018, 56500), (128035, 128034))),
        name("documentary", "Documentary", "tv:83880", genre((128051, 128052), (2406, 78412), (128027, 128028))),
    ]),
    ("Around the World", "around-the-world", "ROWS", [
        name("k-drama", "K-Drama", "tv:93405", mdb((130778, 130775), (150310, 3584), (130779, 130777))),
        name("anime", "Anime", "tv:85937",
             [addon("mal.airing", "anime"), addon("mal.top_anime", "anime"), addon("mal.most_popular", "anime")]
             + mdb((104289, 105461), (88468, 88469), (2483, 2472))
             + [addon("mal.top_series", "anime"), addon("mal.top_movies", "anime"), addon("mal.upcoming", "anime")]),
        name("indian", "Indian", "movie:579974",
             [tmdb(f"{lang} Movies", "movie", voteCountGte=v, withOriginalLanguage=code)
              for lang, code, v in (("Hindi", "hi", 8), ("Telugu", "te", 8), ("Tamil", "ta", 8),
                                    ("Malayalam", "ml", 8), ("Kannada", "kn", 3), ("Bengali", "bn", 3))]
             + [tmdb("Indian Series", "tv", withOriginCountry="IN", voteCountGte=20,
                     releaseDateGte="2015-01-01", withoutGenres=NO_TALK)]),
        name("african", "African", "movie:1013865",
             [disc("movie", "african_cinema", 10), disc("series", "african_series", 11),
              disc("movie", "nollywood", 12), disc("movie", "made_in_kenya", 13)]),
        name("japanese", "Japanese", NC + "bd_oHBhHoNe59VH6bUMazDtJmWOFSS.jpg",
             language_rows("ja", "J-Dramas", {"withoutGenres": "16"})),
        name("spanish", "Spanish", "tv:71446", language_rows("es", "Series", {"withOriginCountry": "ES"})),
        name("french", "French", "tv:96677", language_rows("fr", "Series")),
        name("turkish", "Turkish", NC + "bd_ogyUszy5ZjQyXpKd6f5aT4lHVaq.jpg", language_rows("tr", "Dizi")),
        name("chinese", "Chinese", NC + "bd_jDz6RYN3nKYtlo7J9IMvGoJit7B.jpg", language_rows("zh", "C-Dramas", movie_lang="zh|cn")),
    ]),
    ("Moods & Themes", "moods-and-themes", "TABBED_GRID", [
        name("spooky-season", "Spooky Season", "movie:1078605", [disc("movie", "spooky_season", 14)]),
        name("true-crime", "True Crime", "movie:1949", [disc("movie", "true_crime", 15), disc("series", "true_crime", 16)]),
        name("heists", "Heists", "movie:161", [disc("movie", "heists", 17)]),
        name("time-travel", "Time Travel", "tv:70523", [disc("movie", "time_travel", 18), disc("series", "time_travel", 19)]),
        name("superheroes", "Superheroes", "movie:414906", [disc("movie", "superheroes", 20), disc("series", "superheroes", 21)]),
        name("dystopian-futures", "Dystopian Futures", "movie:335984", [disc("movie", "dystopian_futures", 22)]),
        name("zombies", "Zombies", NC + "bd_rAOjnEFTuNysY7bot8zonhImGMh.jpg", [disc("movie", "zombies", 23)]),
        name("serial-killers", "Serial Killers", "tv:67744", [disc("series", "serial_killers", 24)]),
        name("spies", "Spies", "movie:353081", [disc("movie", "spies", 25)]),
        name("martial-arts", "Martial Arts", NC + "bd_69QJSMkm5Hh0x9fLElZ8hjv5N4P.jpg", [disc("movie", "martial_arts", 26)]),
        name("true-stories", "True Stories", "movie:640", [disc("movie", "true_story", 27)]),
        name("space-and-cyberpunk", "Space & Cyberpunk", "movie:118340", [disc("movie", "space_cyberpunk", 28)]),
        name("coming-of-age", "Coming of Age", NC + "bd_yjGllQUm28R4X9xD9T5xMszirgw.jpg", [disc("movie", "coming_of_age", 29)]),
        name("christmas", "Christmas", NC + "bd_ih2xVgeMS8R5WUetYE8Mr9hVTlB.jpg", [disc("movie", "christmas", 30)]),
    ]),
    ("The Canon", "the-canon", "TABBED_GRID", [
        name("imdb-top-250", "IMDb Top 250", "movie:238", mdb((12306, 94576))),
        name("best-picture", "Best Picture", "movie:872585", mdb(110942, 84226)),
        name("letterboxd-250", "Letterboxd 250", "movie:496243", mdb(10526)),
        name("a24", "A24", "movie:545611", mdb(6395)),
        name("top-rated", "Top Rated", "movie:278", both("tmdb.top_rated")),
    ]),
    ("Decades", "decades", "TABBED_GRID", [
        name("70s", "70s", "movie:578", [disc("movie", "the_1970s", 31)]),
        name("80s", "80s", "movie:105", [disc("movie", "the_1980s", 32)]),
        name("90s", "90s", "movie:680", [disc("movie", "the_1990s", 33)]),
        name("2000s", "2000s", "movie:155", [disc("movie", "the_2000s", 34)]),
        name("2010s", "2010s", "movie:27205", [disc("movie", "the_2010s", 35)]),
        name("2020s", "2020s", "movie:361743", [disc("movie", "the_2020s", 36)]),
    ]),
]


def key(coll_slug, f):
    return f"{coll_slug}--{f['slug']}"


def main():
    config_path, base = sys.argv[1], sys.argv[2]
    assert base.endswith("/"), "COVER_BASE must end in /"
    catalogs = {(c["id"], c.get("displayType") or c["type"]): c for c in json.load(open(config_path))["config"]["catalogs"]}

    folders_js, stills, out, problems = {}, {}, [], []
    for title, cslug, view, folders in COLLECTIONS:
        cid = str(uuid.uuid5(NS, f"everything/{cslug}"))
        coll = {"id": cid, "title": title, "backdropImageUrl": None, "pinToTop": True,
                "focusGlowEnabled": True, "viewMode": view, "showAllTab": True, "folders": []}
        for f in folders:
            k = key(cslug, f)
            sources = []
            for s in f["sources"]:
                if "addon" in s:
                    cat_id, typ = s["addon"]
                    cat = catalogs.get((cat_id, typ))
                    if not cat:
                        problems.append(f"{k}: {cat_id} ({typ}) is not in the addon config")
                        continue
                    sources.append({"provider": "addon", "addonId": ADDON_ID, "addonName": ADDON_NAME,
                                    "type": typ, "catalogId": cat_id, "catalogName": cat["name"],
                                    "title": cat["name"], "genre": None})
                else:
                    sources.append(s)
            if not sources:
                problems.append(f"{k}: no sources")
            anim = f["kind"] == "top"
            coll["folders"].append({
                "id": str(uuid.uuid5(NS, f"everything/{cslug}/{f['slug']}")),
                "title": f["title"],
                "coverImageUrl": f"{base}covers/{cslug}/{f['slug']}.webp",
                "focusGifUrl": f"{base}anim/{cslug}/{f['slug']}.webp" if anim else None,
                "focusGifEnabled": anim,
                "coverEmoji": None, "tileShape": "LANDSCAPE", "hideTitle": True,
                "sources": sources,
                "heroBackdropUrl": None, "heroVideoUrl": None, "titleLogoUrl": None,
            })
            vis = {"name": f["title"], "kind": f["kind"]}
            for fld in ("logo", "c1", "c2", "where"):
                if f.get(fld):
                    vis[fld] = f[fld]
            if f.get("ke"):
                vis["ke"] = True
            if f.get("still"):
                vis["img"] = k
                stills[k] = f["still"]
            folders_js[k] = vis
        out.append(coll)

    if problems:
        print("\n".join(problems))
        sys.exit(1)
    with open(os.path.join(ROOT, "board", "folders.js"), "w") as fh:
        fh.write("// Generated by build/everything.py. Folder key -> what its cover shows.\n")
        fh.write("window.FOLDERS = " + json.dumps(folders_js, ensure_ascii=False, indent=1) + ";\n")
        fh.write("window.ROWS = " + json.dumps([[t, [key(c, f) for f in fs]] for t, c, _, fs in COLLECTIONS],
                                               ensure_ascii=False) + ";\n")
    json.dump(stills, open(os.path.join(HERE, "stills.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "everything-collections.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    with open(os.path.join(ROOT, "everything-collections.min.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    n_f = sum(len(c["folders"]) for c in out)
    n_s = sum(len(f["sources"]) for c in out for f in c["folders"])
    n_a = sum(1 for c in out for f in c["folders"] for s in f["sources"] if s["provider"] == "addon")
    used = {(s["catalogId"], s["type"]) for c in out for f in c["folders"] for s in f["sources"] if s["provider"] == "addon"}
    print(f"{len(out)} collections, {n_f} folders, {n_s} rows ({n_a} from {ADDON_NAME}, {n_s - n_a} from TMDB); "
          f"{len(used)} of {len(catalogs)} addon catalogs used")


if __name__ == "__main__":
    main()
