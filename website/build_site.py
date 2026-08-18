"""
Builds the multi-file website version of the UD Campus Map.

Reads:
  buildings_final.json  - building dataset
  map.webp               - campus map image (WebP)
  site_style.css         - extracted/edited CSS
  site_app.js             - extracted/edited JS (async data loading)
  site_body.html          - extracted/edited body markup

Writes into ./site/:
  index.html
  style.css
  app.js
  buildings.json
  map.webp
"""
import json, os, shutil
from datetime import datetime

IMG_W, IMG_H = 6682, 10418
FT_PER_PX = 1.31

OUT = 'site'
os.makedirs(OUT, exist_ok=True)

# ---- buildings.json (just a clean copy of the dataset) ----
with open('buildings_final.json') as f:
    buildings = json.load(f)
with open(f'{OUT}/buildings.json', 'w') as f:
    json.dump(buildings, f, separators=(',', ':'))

# ---- map.webp ----
shutil.copyfile('map.webp', f'{OUT}/map.webp')

# ---- style.css ----
css = open('site_style.css').read()
with open(f'{OUT}/style.css', 'w') as f:
    f.write(css)

# ---- app.js ----
js = open('site_app.js').read()
js = js.replace('__IMG_W__', str(IMG_W)).replace('__IMG_H__', str(IMG_H))
js = js.replace('__FT_PER_PX__', str(FT_PER_PX))
with open(f'{OUT}/app.js', 'w') as f:
    f.write(js)

# ---- index.html ----
version = datetime.now().strftime('v.%Y%m%d.%H%M')
body = open('site_body.html').read()
body = body.replace('__IMG_W__', str(IMG_W)).replace('__IMG_H__', str(IMG_H))
body = body.replace('__VERSION__', version)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>UD Campus Map</title>
<link rel="preload" as="image" href="map.webp">
<link rel="preload" as="fetch" href="buildings.json" crossorigin>
<link rel="stylesheet" href="style.css">
</head>
{body}
<script src="app.js"></script>
</body>
</html>
"""

with open(f'{OUT}/index.html', 'w') as f:
    f.write(html)

sizes = {}
for fn in ['index.html', 'style.css', 'app.js', 'buildings.json', 'map.webp']:
    sizes[fn] = os.path.getsize(f'{OUT}/{fn}')

total = sum(sizes.values())
for fn, sz in sizes.items():
    print(f"{fn:16} {sz/1024:8.1f} KB")
print(f"{'TOTAL':16} {total/1024:8.1f} KB  ({total/1024/1024:.2f} MB)")
