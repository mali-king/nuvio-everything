# Nuvio Everything Collection

Seven Home rows and 78 folders for Nuvio, built on one AIOMetadata addon, **Everything Metadata**
(184 catalogs), with an Aurora Glass cover for every folder and an animated cover for each Top 10 folder.

Built against Nuvio 0.1.30 (`CollectionModels.kt`, `CollectionCatalogResolver.kt`). The JSON passes the
same checks as Nuvio's `validateImportModel`.

## What's in it

| Row (Home order) | Folders | Opens as | Built from |
|---|---|---|---|
| Top 10 Today | 12 | grid with All tab | FlixPatrol: Kenya for Netflix, the US for global services, India for JioHotstar and ZEE5 |
| Streaming Services | 21 | rows | Top 10, full catalog and New on … per service; five small Indian services from TMDB |
| Genres | 11 | rows | Popular, Top Rated and New, movies and series (MDBList) |
| Around the World | 9 | rows | K-Drama, Anime (MAL and MDBList), African and Made in Kenya; the rest by original language from TMDB |
| Moods & Themes | 14 | grid with All tab | TMDB keywords with a vote floor |
| The Canon | 5 | grid with All tab | IMDb Top 250, Best Picture, Letterboxd 250, A24, TMDB Top Rated |
| Decades | 6 | grid with All tab | Most-voted films of each decade |

246 rows in all: 193 from Everything Metadata and 53 that Nuvio reads from TMDB itself.

## Files

- `everything-collections.min.json`: the file to import (paste its contents).
- `everything-collections.json`: the same, indented, for reading and diffs.
- `covers/<row>/<folder>.webp`: 1600×900 covers, about 65 KB each.
- `anim/top-10-today/<folder>.webp`: 512×288 animated WebP, 36 frames at 10 fps, every frame a keyframe.
  The Mac plays it while you hover a tile; the iPhone loops it.
- `build/` and `board/`: the pipeline that produced all of it.

## Before you import

- Install Everything Metadata in Nuvio first. Nuvio only resolves an addon row when an installed addon's
  manifest declares that catalog.
- Importing replaces the collections on the profile.

## Rebuilding

```sh
python3 -I build/everything.py <everything-config.json> https://raw.githubusercontent.com/mali-king/nuvio-everything/<tag>/
python3 -I build/hires.py build/stills.json board/assets/art/art.json board/assets/hi/still
node build/export_covers.cjs
```

`build/everything.py` is the single spec: every folder's cover, its rows, and which collection it sits in.
It checks every addon row against the config before writing anything. The cover design lives in
`board/covers.html`; `covers.html#r-<folder key>` draws one cover full-window for the exporter. New covers
need a new tag, since Nuvio caches by URL.
