# UD Campus Map — Session Summary & Handoff

## What this is

An interactive map of the University of Delaware's Newark campus, built
from the official 2025 UD viewbook campus map PNG. It now exists in **two
forms**, both generated from the same underlying data:

1. **Single-file version** (`index.html`, ~3.8MB) — everything (image,
   data, code) embedded in one portable HTML file. Opens standalone,
   works offline, easiest to share as a single attachment.
2. **Multi-file website version** (`ud-campus-map-website/`, ~1.6MB total)
   — the same app split into `index.html` + `style.css` + `app.js` +
   `buildings.json` + `map.webp`, built for actual web hosting. Roughly
   59% smaller in transfer size, renders progressively instead of
   blocking on one giant download, and lets a browser cache the static
   assets between visits. Requires being served over `http://`/`https://`
   (won't run by double-clicking) — see that folder's own `README.md`
   for hosting and local-preview instructions.

**Both have already been delivered to the user directly in this
conversation.** This package is the *source* behind both — the data and
generator scripts needed to modify or regenerate either one without
redoing the extraction work from scratch.

If you're picking this up in Claude Code: this is the whole project,
there's no other repo. If you're picking this up in Cowork: the
immediate next action is almost always "edit a data/template file, then
run the matching generator script."

---

## How to regenerate each version

**Single-file** (from inside `single-file/`):
```bash
cd single-file
python3 build_html.py
```
Reads `map_base64.txt` and `buildings_final.json` from that same folder,
writes `index.html` next to itself.

**Multi-file website** (from inside `website/`):
```bash
cd website
python3 build_site.py
```
Reads `buildings_final.json`, `map.webp`, `site_style.css`, `site_app.js`,
and `site_body.html` from that same folder, writes a complete `site/`
subfolder (`index.html`, `style.css`, `app.js`, `buildings.json`,
`map.webp`).

Both folders are self-contained — each has its own copy of
`buildings_final.json` so you can `cd` into either one and run its
script with nothing else needed. If you correct a building position and
want it reflected in *both* versions, update both copies (or copy one
over the other) — see "Files in this package" below.

Both scripts are template-based: the editable source (CSS/JS/HTML
fragments plus the two data files) is kept separate from the generated
output, since the generated files are too large to comfortably hand-edit
in place (a ~3MB embedded image, a 190-row JSON array, etc.). To change
anything about look or behavior, edit the `site_*` files (for the
website) or the HTML-template string inside `build_html.py` (for the
single-file version) — **not** the generated output — then re-run the
matching script.

Note the two generators currently have separate CSS/JS source (extracted
from a common ancestor early on, then evolved independently as features
were added — see request history below). They're kept behaviorally in
sync by hand, feature-for-feature, but are not literally the same file.
If that divergence ever becomes annoying, unifying them into one shared
template with two output modes would be a reasonable refactor.

---

## Methodology (how the building data was extracted)

This is the part worth understanding before touching the data — it took
most of the effort in the early part of this session and isn't obvious
from the output alone.

**Source:** `Campus_Map_2025-07.png`, 6682×10418px, the official UD Office
of Undergraduate Admissions viewbook campus map (provided by the user;
not included in this package — see "What's not included").

1. **Building list (name + number + rough grid cell):** Read directly off
   the map's own printed, numbered building index (1–190) via cropped,
   high-resolution image inspection. Ground-truth list, stored as
   `buildings.py`.

2. **Reference grid → pixel coordinates:** The map has a printed
   reference grid (columns 1–7, rows A–L). Boundary pixel positions were
   found by scanning for the grid's white gridlines against the cream
   background and clustering the matches. Gives an exact pixel bounding
   box for any grid cell like "E3".

3. **Precise per-building coordinates via OCR:** Every building number is
   also printed directly on the map, in a consistent red color, at the
   building's actual location. Isolated with a color mask, then OCR'd
   (`tesseract`) per-blob (crop each candidate region individually and
   OCR it separately — far more reliable than OCR-ing the whole page at
   once), cross-validated against the expected grid cell from step 2 to
   catch misreads. Resolved 171 of 190 buildings this way.

4. **Fallback placement, later corrected by hand:** The remaining 19
   (mostly in the dense historic core — grid cells D3/E3/E4/F4, where
   labels overlap too much for reliable OCR) were placed at a
   deterministic sub-grid position within their known cell — approximate,
   not the real footprint. **The user subsequently went through and
   manually corrected all 19**, plus 3 more that hadn't been flagged
   (24 in total, across two correction rounds) using the in-app Edit
   Positions feature (drag to reposition, export corrected data, feed
   back into `buildings_final.json`) — see request history. Every
   building originally on the fallback list now has a real,
   user-verified position.

5. **Residence hall tagging:** Done by sampling the actual map pixel
   color around each building's resolved coordinate and checking it
   against the legend's exact green swatch RGB (`167,215,175`) — not
   guessed from names. 16 buildings matched with high confidence; stored
   as `residence_halls.json`. Conservative (precision over recall) — may
   be missing some residence halls whose number label didn't land
   squarely on the green fill.

6. **Walking-distance scale calibration:** No printed scale bar exists on
   the source map. Calibrated by looking up real GPS coordinates for
   pairs of known campus landmarks, computing real distance (haversine),
   and dividing by pixel distance between those same buildings in the
   extracted dataset. Two independent pairs agreed within 1.3%, landing
   on `1.31` ft/pixel (`FT_PER_PX` in both generators). Straight-line
   only — the app is upfront with users that actual walking distance
   along paths will be longer.

7. **Image processing:** Originally downscaled 50% (3341px wide) and
   JPEG-encoded (quality 87, ~2.9MB) for the single-file version. For the
   website version, re-encoded as WebP instead (quality 82) — 46%
   smaller than the JPEG at matching visual legibility, confirmed by
   side-by-side crop comparison at the same zoom level.

---

## Current feature set (all implemented and tested)

- Pan (drag), zoom (scroll/pinch/buttons — mouse-wheel tuned to ~7-8% per
  notch, scaling smoothly with actual scroll input rather than a flat
  step), search-and-jump for all 190 buildings by name or number
- **Reset zoom** button (renamed from "Reset view" this session)
- Legend panel: static reproduction of the map's printed key, plus live
  toggleable filtering for Residence Halls vs. other buildings (mobile:
  bottom sheet, not a side panel)
- Multi-stop walking directions: ordered route building, reorder/remove
  stops, auto-zoom to building-level on the first stop then re-fit to
  show the whole route as stops are added/removed, straight-line
  distance + walking-time estimate (per-leg and total)
- Route stops render as colored map-pin icons (green start / amber via /
  crimson end) with the stop's sequence number in the pin's head
- **Hide Numbers** — toggles both the number labels *and* the marker
  circles themselves, for an unobstructed view of the base map
- **Edit Positions** — drag any building marker or route pin to correct
  its location; edited markers get a gold dashed ring; **Download
  corrected data** exports all 190 buildings as JSON in the same shape as
  `buildings_final.json`, ready to feed back into the generator
- **Collapsible footer menu** — Hide Numbers and Edit Positions live
  behind a "Tools" toggle in the footer, collapsed by default
- Fully responsive; touch-tested (drag-pan, pinch-zoom, tap, drag-to-edit)
  at phone viewport with real synthetic pointer/touch events, not just
  CSS breakpoints
- **Website version only:** async data loading with a loading-spinner
  overlay, `<link rel="preload">` hints so the image starts fetching
  immediately, graceful behavior if someone interacts before load
  completes

Built and regression-tested throughout with Playwright (headless
Chromium) — both desktop and mobile viewports, real pointer/touch event
simulation, and (for the website version) an actual local HTTP server
under simulated slow-network conditions, not just static screenshots.

**Two real bugs were caught this way and fixed, worth knowing if you
extend the pan/zoom/drag logic:**
- Calling `setPointerCapture` on every `pointerdown` (even simple clicks)
  silently broke click-through to markers — fixed by only capturing once
  actual drag movement is detected. Keep that disambiguation pattern
  intact if you touch this code.
- A "just finished dragging, suppress the next click" flag could get
  stuck true if an unrelated click happened before the marker got
  clicked again — fixed with a short safety-net timeout. Same pattern
  applies anywhere else a similar suppress-flag gets added.

Also worth knowing: the edit-mode status bar (top-center pill) needed
`pointer-events: none` on its own background, with `pointer-events: auto`
restored only on its buttons — otherwise it silently blocks drag/click on
any marker that happens to render underneath it.

---

## Known limitations

- Residence hall tagging (16 buildings) is conservative — may not be
  fully exhaustive.
- Walking directions are straight-line only; no real sidewalk/path
  network exists in the data.
- Dining/Bookstore/Restroom/Admissions/Parking icons from the map's
  legend are shown for reference only — not individually plotted as
  searchable points.
- The two generator scripts' CSS/JS are hand-synced rather than shared
  (see "How to regenerate" above).

---

## Files in this package

```
ud-campus-map-handoff/
├── SESSION_SUMMARY.md      (this file)
├── single-file/            self-contained — cd in, run build_html.py
├── website/                self-contained — cd in, run build_site.py
└── reference/               not needed to build anything; background/provenance
```

### `single-file/` — produces `index.html` (~3.8MB, one portable file)
| File | What it is |
|---|---|
| `build_html.py` | Generator |
| `buildings_final.json` | All 190 buildings: `n`, `name`, `cat`, `x`/`y` (pixel coords, original 6682×10418 image space) — **includes the user's 21 manual corrections** |
| `map_base64.txt` | Base64 JPEG embedded by the generator |

### `website/` — produces `site/` (5 files, ~1.6MB total, for real hosting)
| File | What it is |
|---|---|
| `build_site.py` | Generator |
| `buildings_final.json` | Same dataset as above — a separate copy, so this folder runs standalone |
| `site_body.html` | HTML body template |
| `site_style.css` | CSS source |
| `site_app.js` | JS source (async data-loading version) |
| `map.webp` | Campus map image, WebP |

**`buildings_final.json` is intentionally duplicated in both folders**
rather than shared from one place, so each folder works by itself with
no relative-path dependencies between them. If you correct a building
position, update whichever one you regenerated from, then copy that file
over the other copy to keep both versions in sync.

### `reference/` — not read by either generator; background on how the data was derived
| File | What it is |
|---|---|
| `buildings.py` | Raw ground-truth list: number, name, printed grid reference — no coordinates |
| `need_fallback.json` | The original 19 approximate-placement building numbers (2 still unresolved — see above) |
| `residence_halls.json` | The 16 building numbers tagged as residence halls |

### What's not included

- The original source PNG (`Campus_Map_2025-07.png`, 37MB) — the user
  has this; needed only to redo extraction at a different resolution/crop
  or spot-check other buildings against the source image.
- Intermediate OCR/extraction debugging artifacts (raw tesseract output,
  per-blob crops, color-mask images). Working scratch files, not needed
  to regenerate either deliverable. The methodology section above
  documents the approach well enough to redo any of it if needed.

---

## Suggested next steps (not done, but well-scoped)

1. **Plot amenity icons** (Dining/Bookstore/Restroom/Admissions/Parking)
   as individual searchable points, not just static legend entries. Would
   need shape/color detection rather than OCR, since these are icons, not
   numerals.
2. **Real pathfinding** instead of straight-line distance — needs a
   sidewalk/path network that doesn't currently exist in the data.
   Nontrivial; straight-line is a reasonable, clearly-disclosed
   approximation for now.
3. **Cache-busting for the website version** — the `.htaccess` sets a
   1-year cache on `map.webp`. If the image or `buildings.json` ever
   change after the site is live, a returning visitor's browser won't
   know to re-fetch them unless the filename changes (or the cache
   headers are loosened). Worth a versioned filename (`map.v2.webp`) if
   this comes up.
4. Consider unifying the two generators' CSS/JS into one shared source
   with two output modes, per the note in "How to regenerate."

---

## Request history this session (chronological, for context)

1. Built the initial single-file interactive map: pan/zoom, search,
   category legend filtering, straight-line walking directions (2-point)
2. Added multi-stop directions (ordered list, reorder/remove, running
   total) + fixed a real bug where search-dropdown text was invisible
   (inherited white color from the header)
3. Answered a responsiveness question, which surfaced two real mobile UX
   issues on inspection (legend ate 69% of screen width; reorder buttons
   were 18×14px, under touch-target guidelines) — fixed both
4. Added auto-zoom behavior tied to route-building, and enlarged/recolored
   the stop-sequence badges
5. Replaced the dot-plus-offset-badge combo with proper map-pin icons for
   route stops specifically (normal buildings remain plain circles)
6. Requested a first handoff package (source data + generator + this
   summary doc) for continuity in Cowork/Claude Code
7. Added Hide Numbers and Edit Positions (drag-to-correct marker
   positions, export corrected data) — caught and fixed two real bugs
   along the way (edit-bar blocking clicks underneath it; a stuck
   click-suppression flag)
8. Clarified, on request, why "single HTML file" and "Edit Positions
   downloading a separate JSON" aren't a contradiction — browsers can't
   write back to their own source file; the download is how a correction
   becomes permanent
9. Walked through the exact terminal commands to feed a downloaded
   correction file back into the generator
10. User uploaded a regenerated `index.html` (built from an older
    handoff-package script) — diffed its embedded data against the
    known-good version, confirmed **21 buildings' positions** carried
    over correctly (4 of them buildings that hadn't even been flagged as
    approximate), then merged those corrected positions into the
    *current* generator so the result had both the fix and every feature
11. Tuned mouse-wheel zoom sensitivity (flat 15%-per-notch felt too
    fast) to scale proportionally with actual scroll input, ~7-8% per
    typical notch
12. Requested a multi-file "traditional website" version for faster
    mobile loading — rebuilt as five files (WebP image, async fetch for
    data, loading overlay, preload hints), cutting total size from
    3.8MB to 1.6MB, plus `.htaccess` and a hosting/README doc; verified
    under simulated slow-network conditions with a real local HTTP
    server
13. Answered how to test the multi-file version locally before
    uploading (`python3 -m http.server`, VS Code Live Server, `npx serve`)
14. Added a collapsible "Tools" menu to the footer (Hide Numbers + Edit
    Positions now hidden by default behind a toggle) and renamed
    "Reset view" to "Reset zoom" — applied to both the single-file and
    website versions
15. Recreated this summary document to reflect all of the above
16. Asked to organize the handoff package into clearly-scoped subfolders
    (`single-file/`, `website/`, `reference/`) instead of one flat file
    list — each of the first two made fully self-contained (own copy of
    `buildings_final.json`, no cross-folder path dependencies), verified
    both generators still run correctly from their new locations
17. Provided the exact file-to-folder list on request, for manual
    download organization
18. User attempted to submit corrected positions for #7, #112, and #117
    twice — both uploads turned out to be byte-for-byte identical to the
    existing data (confirmed via MD5, not just position diffing), so
    neither was applied; flagged this clearly rather than silently
    proceeding, and suggested concrete things to check (duplicate
    downloads, whether the drag actually registered, a DevTools
    console check). Third upload was genuine — diffed clean (exactly
    those 3 buildings changed, nothing else), merged into both
    generators, regenerated and re-verified both the single-file and
    website versions (including over a real local HTTP server for the
    latter), and updated this summary to reflect that all 19 originally
    flagged buildings now have real, user-verified positions

Each of these was verified with actual Playwright interaction tests
(not just visual inspection) before being called done — worth
continuing that habit, since several real bugs were only caught that
way.
