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

## Other looks (tag v2)

The same collection with four other cover designs. Every folder, row and source is identical to the
Aurora Glass file; only the covers change, so you can switch looks by importing a different file.

| Look | Import file | What it is |
|---|---|---|
| Polaroid Table | `styles/polaroid-table/polaroid-table.json` | Instant photos on a desk, labelled in marker; Top 10 gets a sticky note |
| Arcade | `styles/arcade/arcade.json` | Each film as a 16-bit title screen, PICO-8 colours, CRT glass |
| Riso Zine | `styles/riso-zine/riso-zine.json` | Two-ink risograph prints, torn, taped and scribbled on |
| Hype Reel | `styles/hype-reel/hype-reel.json` | Sports-broadcast style: slashed colour panel, cast breaking out, echoing type |

Two more under tag v3:

| Look | Import file | What it is |
|---|---|---|
| True Black Mono | `styles/true-black-mono/true-black-mono.json` | Pure black for OLED: the cast cut out in silver and lit out of the black, white type and logos |
| Showcase | `styles/showcase/showcase.json` | Built like a premium streaming app: true-colour key art, brand tiles for services, a Top 10 badge |

Each look has `covers/` (1600×900) and `anim/` (the 12 Top 10 hover loops) beside its import file, served from
`raw.githubusercontent.com/mali-king/nuvio-everything/<tag>/styles/<look>/`.

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

The other looks:

```sh
python3 -I build/styles_assets.py                      # stills, cut-outs, Polaroid back photos -> board/styles.js
node build/export_styles.cjs dist/styles               # all four looks; or name some: pol arc riso hype
python3 -I build/style_collections.py dist/styles <tag>  # one import file per look, v1 with the cover URLs swapped
```

The four designs live in `board/styles.html`; `styles.html#r-<look>-<folder key>` draws one cover and
`styles.html?s=<look>` draws a look's whole sheet.

True Black Mono and Showcase live in `board/looks3.html` (styles `mono` and `app`, same contract), with the
candidates that were not picked:

```sh
LAB=looks3 node build/export_styles.cjs dist/styles                                   # mono and app
python3 -I build/style_collections.py dist/styles <tag> true-black-mono showcase
```
