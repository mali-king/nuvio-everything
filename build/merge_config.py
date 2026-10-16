"""Merge the Services-Metadata and Genre Metadata AIOMetadata exports into one
"Everything Metadata" config, in AIOMetadata 3.5.1's own export format.

Usage: python3 -I merge_config.py SERVICES.json GENRES.json OUT.json
"""
import copy
import json
import sys

SERVICES, GENRES, OUT = sys.argv[1:4]
svc = json.load(open(SERVICES))
gen = json.load(open(GENRES))
S, G = svc["config"], gen["config"]

assert svc["version"] == gen["version"] == "3.5.1", "both exports must be 3.5.1"
assert S["apiKeys"] == G["apiKeys"], "api keys differ between exports; merge them by hand"

TTL = 86400

# ---------------------------------------------------------------- top level
cfg = copy.deepcopy(S)  # Services had search on and the richer settings
cfg["addonName"] = "Everything Metadata"
cfg["mal"]["allowEpisodeMarking"] = S["mal"]["allowEpisodeMarking"] or G["mal"]["allowEpisodeMarking"]
for flag in ("traktWatchTracking", "anilistWatchTracking", "mdblistWatchTracking",
             "malWatchTracking", "simklWatchTracking"):
    cfg[flag] = bool(S.get(flag) or G.get(flag))
cfg["hideWatchedMdblist"] = G.get("hideWatchedMdblist", False)
cfg["showDisabledCatalogs"] = False
cfg["searchEnabled"] = True
cfg["search"]["enabled"] = True
cfg["search"]["engineEnabled"] = {**G["search"]["engineEnabled"], **S["search"]["engineEnabled"]}
cfg["search"]["providers"].setdefault("people_search_movie", "tmdb.people.search")
cfg["search"]["providers"].setdefault("people_search_series", "tmdb.people.search")
# New in this merge: the TopPoster key was set but no provider was picked, which
# AIOMetadata reads as 'none', so rating posters never showed.
cfg["posterRatingProvider"] = "top"
cfg["timezone"] = "Africa/Nairobi"
# Server stamps; AIOMetadata writes fresh ones on save.
for stamp in ("configHash", "lastModified", "configVersion"):
    cfg.pop(stamp, None)

# ---------------------------------------------------------------- catalogs
by_key = {}
for c in S["catalogs"] + G["catalogs"]:
    by_key[(c["id"], c["type"])] = copy.deepcopy(c)


def mdb(list_id, typ, name=None):
    c = by_key[(f"mdblist.{list_id}", typ)]
    if name:
        c["name"] = name
    c["enabled"] = True
    c.setdefault("displayType", typ)  # one Genres entry lacked it
    return c


def new_mdb(list_id, typ, name, author, slug, count, home=False):
    return {
        "id": f"mdblist.{list_id}", "name": name, "sort": "default", "type": typ,
        "order": "asc", "source": "mdblist", "enabled": True, "cacheTTL": TTL,
        "metadata": {"url": f"https://mdblist.com/lists/{author}/{slug}", "author": author,
                     "itemCount": count, "mediatype": "movie" if typ == "movie" else "show"},
        "showInHome": home, "displayType": typ, "genreSelection": "standard",
        "enableRatingPosters": True,
    }


def builtin(cid, typ, name, source, home=False):
    return {"id": cid, "name": name, "type": typ, "source": source, "enabled": True,
            "showInHome": home, "enableRatingPosters": True, "randomizePerPage": False}


def flix(service, country, slug, typ, name, home=False):
    return {"id": f"flixpatrol.{service}.{country}.{typ}", "type": typ, "name": name,
            "enabled": True, "showInHome": home, "source": "flixpatrol",
            "enableRatingPosters": True, "metadata": {"countrySlug": slug}}


SUFFIX = "mgt7x0"  # base36 stamp, as the Discover builder makes one
_seq = iter(range(1000))


def discover(typ, slug, name, params, form):
    """A TMDB Discover catalog in the Discover builder's own v2 shape."""
    tmdb_type = "movie" if typ == "movie" else "tv"
    params = {"sort_by": "popularity.desc", "include_adult": False, **params}
    query = "&".join(f"{k}={v}" for k, v in params.items() if v not in ("", None))
    form = {"catalogName": name, "discoverSource": "tmdb", "sortBy": params["sort_by"],
            "cacheTTL": None, "catalogType": typ, "tmdbMediaType": tmdb_type,
            "includeAdult": False, **form}
    return {
        "id": f"tmdb.discover.{typ}.{slug}.{SUFFIX}{next(_seq):02d}",
        "type": typ, "name": name, "enabled": True, "showInHome": False,
        "source": "tmdb", "cacheTTL": TTL, "enableRatingPosters": True,
        "metadata": {
            "description": f"TMDB Discover ({tmdb_type})",
            "url": f"https://www.themoviedb.org/discover/{tmdb_type}?{query}",
            "discover": {"version": 2, "source": "tmdb", "mediaType": tmdb_type,
                         "params": params, "formState": form},
        },
    }


def provider_discover(typ, slug, name, region, providers):
    ids = "|".join(str(p[0]) for p in providers)
    return discover(typ, slug, name,
                    {"watch_region": region, "with_watch_providers": ids,
                     "with_watch_monetization_types": "flatrate|free|ads", "vote_count.gte": 5},
                    {"watchRegion": region, "providerJoinMode": "or", "voteCountMin": 5,
                     "watchProviders": [{"id": p[0], "label": p[1]} for p in providers]})


def keyword_discover(typ, slug, name, keywords, min_votes):
    ids = "|".join(str(k[0]) for k in keywords)
    return discover(typ, slug, name, {"with_keywords": ids, "vote_count.gte": min_votes},
                    {"withKeywords": [{"id": k[0], "label": k[1]} for k in keywords],
                     "keywordJoinMode": "or", "voteCountMin": min_votes})


def country_discover(typ, slug, name, countries, min_votes):
    return discover(typ, slug, name, {"with_origin_country": countries, "vote_count.gte": min_votes},
                    {"originCountry": countries, "voteCountMin": min_votes})


def decade(start, name):
    end = start + 9
    return discover("movie", f"the_{start}s", name,
                    {"sort_by": "vote_count.desc", "primary_release_date.gte": f"{start}-01-01",
                     "primary_release_date.lte": f"{end}-12-31", "vote_count.gte": 100},
                    {"movieDatePreset": "custom", "primaryReleaseFrom": f"{start}-01-01",
                     "primaryReleaseTo": f"{end}-12-31", "voteCountMin": 100})


cats = []
add = cats.extend

# Home rows
add([mdb(87667, "movie"), mdb(88434, "series"),
     flix("netflix", "ke", "kenya", "movie", "Netflix Top 10 · Kenya", home=True),
     flix("netflix", "ke", "kenya", "series", "Netflix Top 10 · Kenya", home=True)])

# Everything-wide
add([mdb(42822, "movie"), mdb(42836, "series"),
     builtin("tmdb.top_rated", "movie", "Top Rated", "tmdb"),
     builtin("tmdb.top_rated", "series", "Top Rated", "tmdb"),
     builtin("tmdb.airing_today", "series", "Airing Today", "tmdb")])

# Streaming services: Top 10, the full catalog, what's new
SERVICES_BLOCK = [
    # name, flixpatrol id, (catalog movie, series), (new movie, series)
    ("Netflix", "netflix", (88328, 88329), (86752, 86751)),
    ("Prime Video", "amazon-prime", (88332, 88333), (86755, 86753)),
    ("Disney+", "disney", (88322, 88323), (86759, 86758)),
    ("HBO Max", "hbo-max", (88324, 88325), (89647, 89649)),
    ("Apple TV+", "apple-tv", (88317, 88319), (86757, 86756)),
    ("Paramount+", "paramount", (88330, 88331), (86762, 86761)),
    ("Hulu", "hulu", (88326, 88327), None),
    ("Peacock", "peacock", (84239, 84240), None),
]
for name, fp, (cm, cs), new in SERVICES_BLOCK:
    add([flix(fp, "us", "united-states", "movie", f"{name} Top 10 · US"),
         flix(fp, "us", "united-states", "series", f"{name} Top 10 · US"),
         mdb(cm, "movie", name), mdb(cs, "series", name)])
    if new:
        add([mdb(new[0], "movie", f"New on {name}"), mdb(new[1], "series", f"New on {name}")])
    if fp == "hulu":  # snoak's Latest Hulu lists were deleted from MDBList
        add([new_mdb(216816, "movie", "New on Hulu", "amything", "latest-hulu-movies", 200),
             new_mdb(216834, "series", "New on Hulu", "amything", "latest-hulu-shows", 200)])
add([flix("crunchyroll", "us", "united-states", "all", "Crunchyroll Top 10 · US"),
     mdb(98862, "movie"), mdb(99202, "series")])

# Indian streaming (TMDB watch providers, region IN)
add([flix("hotstar", "in", "india", "all", "JioHotstar Top 10 · India"),
     provider_discover("movie", "jiohotstar", "JioHotstar", "IN", [(2336, "JioHotstar")]),
     provider_discover("series", "jiohotstar", "JioHotstar", "IN", [(2336, "JioHotstar")]),
     provider_discover("movie", "sonyliv", "SonyLIV", "IN", [(237, "Sony Liv")]),
     provider_discover("series", "sonyliv", "SonyLIV", "IN", [(237, "Sony Liv")]),
     flix("zee5", "in", "india", "all", "ZEE5 Top 10 · India"),
     provider_discover("movie", "zee5", "ZEE5", "IN", [(232, "Zee5")]),
     provider_discover("series", "zee5", "ZEE5", "IN", [(232, "Zee5")]),
     provider_discover("movie", "sun_nxt", "Sun NXT", "IN", [(309, "Sun Nxt")]),
     provider_discover("movie", "aha", "aha", "IN", [(532, "aha")]),
     provider_discover("movie", "hoichoi", "Hoichoi", "IN", [(315, "Hoichoi")]),
     provider_discover("movie", "amazon_mx_player", "Amazon MX Player", "IN",
                       [(1898, "Amazon MX Player"), (515, "MX Player")])])

# Genres: Popular / Top Rated / New, movies and series
GENRES_BLOCK = [
    ("Action", (91211, 91213), (2407, 45762), (128037, 128029)),
    ("Animation", (116037, 116038), (69018, None), (128035, 128034)),
    ("Comedy", (91223, 91224), (2195, 45764), (128040, 128041)),
    ("Documentary", (128051, 128052), (2406, 78412), (128027, 128028)),
    ("Drama", (91296, 91297), (2408, 45766), (128043, 128044)),
    ("Family", (24262, 147641), (2415, 157286), (76113, 59967)),
    ("Horror", (91215, 91217), (2410, 10665), (128045, 128046)),
    ("Mystery", None, (2416, 45183), None),
    ("Romance", (128262, 128265), None, (128261, 128264)),
    ("Sci-Fi", (91220, 91221), (2412, 79476), (128047, 128048)),
    ("Thriller", (91893, 91894), None, (128049, 128050)),
]
for g, pop, top, new in GENRES_BLOCK:
    if pop:
        add([mdb(pop[0], "movie", f"Popular {g}"), mdb(pop[1], "series", f"Popular {g}")])
    if top:
        add([mdb(top[0], "movie", f"Top Rated {g}")])
        if top[1]:
            add([mdb(top[1], "series", f"Top Rated {g}")])
        elif g == "Animation":  # rinaldiaris.ar0's list was deleted from MDBList
            add([new_mdb(56500, "series", "Top Rated Animation", "whiskeytime",
                         "top-animated-shows", 200)])
    if new:
        add([mdb(new[0], "movie", f"New {g}"), mdb(new[1], "series", f"New {g}")])

# Around the world
add([mdb(130778, "movie", "Popular K-Drama"), mdb(130775, "series", "Popular K-Drama"),
     mdb(150310, "movie", "Top Rated Korean"), mdb(3584, "series", "Top Rated Korean"),
     mdb(130779, "movie", "New K-Drama"), mdb(130777, "series", "New K-Drama"),
     mdb(104289, "movie"), mdb(105461, "series"),
     mdb(88468, "movie"), mdb(88469, "series"),
     mdb(2483, "movie", "New Anime"), mdb(2472, "series", "New Anime"),
     builtin("mal.airing", "anime", "Airing Now", "mal"),
     builtin("mal.upcoming", "anime", "Upcoming Anime Season", "mal"),
     builtin("mal.top_anime", "anime", "Top Anime", "mal"),
     builtin("mal.most_popular", "anime", "Most Popular Anime", "mal"),
     builtin("mal.top_movies", "anime", "Top Anime Movies", "mal"),
     builtin("mal.top_series", "anime", "Top Anime Series", "mal"),
     builtin("mal.seasons", "anime", "Anime Seasons", "mal"),
     country_discover("movie", "african_cinema", "African Cinema",
                      "NG|ZA|KE|GH|EG|SN|TZ|UG|CM|ET|MA|TN|RW", 20),
     country_discover("series", "african_series", "African Series", "NG|ZA|KE|GH|EG", 5),
     country_discover("movie", "nollywood", "Nollywood", "NG", 10),
     country_discover("movie", "made_in_kenya", "Made in Kenya", "KE", 3),
     builtin("tmdb.language", "movie", "By Language", "tmdb"),
     builtin("tmdb.language", "series", "By Language", "tmdb")])

# The canon
add([new_mdb(12306, "movie", "IMDb Top 250", "aramil89", "imdb-top-250", 250),
     new_mdb(94576, "series", "IMDb Top 250", "treeman183", "imdb-top-250-tv-shows", 250),
     new_mdb(110942, "movie", "Oscar Best Picture Winners", "apg2886", "oscar-best-picture-winners", 99),
     new_mdb(84226, "movie", "Oscar Best Picture Nominees", "alaxkouad",
             "oscar-best-picture-nominees-2000-ykkgpe7d2t", 189),
     new_mdb(10526, "movie", "Letterboxd Top 250", "slugfest201", "letterboxd-top-250", 250),
     new_mdb(6395, "movie", "A24", "mdatum", "a24", 173)])

# Themes (TMDB keywords)
add([keyword_discover("movie", "spooky_season", "Spooky Season", [(3335, "halloween")], 50),
     keyword_discover("movie", "true_crime", "True Crime", [(33722, "true crime")], 20),
     keyword_discover("series", "true_crime", "True Crime", [(33722, "true crime")], 20),
     keyword_discover("movie", "heists", "Heists", [(10051, "heist")], 100),
     keyword_discover("movie", "time_travel", "Time Travel", [(4379, "time travel")], 100),
     keyword_discover("series", "time_travel", "Time Travel", [(4379, "time travel")], 30),
     keyword_discover("movie", "superheroes", "Superheroes", [(9715, "superhero")], 200),
     keyword_discover("series", "superheroes", "Superheroes", [(9715, "superhero")], 50),
     keyword_discover("movie", "dystopian_futures", "Dystopian Futures",
                      [(4565, "dystopia"), (4458, "post-apocalyptic future")], 200),
     keyword_discover("movie", "zombies", "Zombies", [(12377, "zombie")], 100),
     keyword_discover("series", "serial_killers", "Serial Killers", [(10714, "serial killer")], 30),
     keyword_discover("movie", "spies", "Spies & Espionage", [(470, "spy")], 200),
     keyword_discover("movie", "martial_arts", "Martial Arts", [(779, "martial arts")], 100),
     keyword_discover("movie", "true_story", "Based on a True Story", [(9672, "based on true story")], 300),
     keyword_discover("movie", "space_cyberpunk", "Space & Cyberpunk",
                      [(161176, "space opera"), (12190, "cyberpunk")], 100),
     keyword_discover("movie", "coming_of_age", "Coming of Age", [(10683, "coming of age")], 300),
     keyword_discover("movie", "christmas", "Christmas", [(207317, "christmas")], 50)])

# Decades
add([decade(1970, "The 70s"), decade(1980, "The 80s"), decade(1990, "The 90s"),
     decade(2000, "The 2000s"), decade(2010, "The 2010s"), decade(2020, "The 2020s"),
     builtin("tmdb.year", "movie", "By Year", "tmdb"),
     builtin("tmdb.year", "series", "By Year", "tmdb")])

# ---------------------------------------------------------------- checks
keys = [(c["id"], c["type"]) for c in cats]
assert len(keys) == len(set(keys)), "duplicate catalog"
dropped = {f"mdblist.{n}" for n in (127955, 127954, 153462)}
used = {k for k in keys}
missing = [k for k in by_key if k not in used and k[0] not in dropped]
assert not missing, f"source catalogs left out: {missing}"
assert all(c["enabled"] for c in cats)
assert len(cats) <= 200, "ElfHosted allows 200 enabled catalogs"

cfg["catalogs"] = cats
out = {
    "version": svc["version"],
    "exportedAt": "2026-10-16T02:00:00.000Z",
    "config": cfg,
    "metadata": {"apiKeysExcluded": False, "totalCatalogs": len(cats), "enabledCatalogs": len(cats)},
}
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print(f"{len(cats)} catalogs ({sum(c['showInHome'] for c in cats)} on home) -> {OUT}")
