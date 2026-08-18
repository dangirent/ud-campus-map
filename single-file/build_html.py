import json
from datetime import datetime

with open('map_base64.txt') as f:
    img_b64 = f.read().strip()

with open('buildings_final.json') as f:
    buildings = json.load(f)

IMG_W, IMG_H = 6682, 10418
FT_PER_PX = 1.31

buildings_json = json.dumps(buildings, separators=(',', ':'))

html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>UD Campus Map</title>
<style>
  :root{
    --navy:#0f3d71;
    --navy-dark:#0a2c52;
    --crimson:#c8102e;
    --cream:#fffdcd;
    --residence:#5fae74;
    --residence-fill:#a7d7af;
    --ink:#1c2530;
    --paper:#f7f6f1;
    --line:#dcd8c8;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;height:100%;overflow:hidden;background:var(--navy-dark);color:var(--ink);}
  .app{position:fixed;inset:0;display:flex;flex-direction:column;}

  /* ---------- Toolbar ---------- */
  header{
    background:var(--navy);
    color:#fff;
    display:flex;
    align-items:center;
    gap:10px;
    padding:9px 12px;
    box-shadow:0 2px 8px rgba(0,0,0,.25);
    z-index:40;
    flex-wrap:wrap;
  }
  footer{
    background:var(--navy);
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    gap:10px;
    padding:9px 12px;
    box-shadow:0 -2px 8px rgba(0,0,0,.25);
    z-index:40;
    flex-wrap:wrap;
    position:relative;
  }
  .app-version{
    position:absolute;right:12px;top:50%;transform:translateY(-50%);
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    font-size:10px;letter-spacing:.4px;color:rgba(255,255,255,.8);
    white-space:nowrap;pointer-events:none;
  }
  .footer-menu{
    display:none;
    align-items:center;
    gap:10px;
    flex-wrap:wrap;
    justify-content:center;
  }
  .footer-menu.show{display:flex;}
  .brand{
    display:flex;align-items:baseline;gap:8px;margin-right:4px;white-space:nowrap;
  }
  .brand .mark{
    font-family:Georgia,'Iowan Old Style','Palatino Linotype',serif;
    font-weight:700;font-size:19px;letter-spacing:.3px;
  }
  .brand .mark small{
    display:block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    font-size:10px;font-weight:600;letter-spacing:1.5px;color:#ffd9a0;text-transform:uppercase;
  }
  .search-wrap{position:relative;flex:1 1 240px;min-width:140px;max-width:420px;}
  .search-wrap input{
    width:100%;padding:8px 34px 8px 12px;border-radius:20px;border:none;
    font-size:14px;background:#fff;color:var(--ink);outline:none;
  }
  .search-wrap .clear-btn{
    position:absolute;right:6px;top:50%;transform:translateY(-50%);
    width:22px;height:22px;border:none;background:transparent;color:#8a8578;
    font-size:16px;cursor:pointer;display:none;line-height:1;
  }
  .search-wrap.has-text .clear-btn{display:block;}
  .results{
    position:absolute;top:calc(100% + 6px);left:0;right:0;background:#fff;
    border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.25);max-height:320px;overflow-y:auto;
    display:none;z-index:50;color:var(--ink);
  }
  .results.show{display:block;}
  .result-item{
    padding:9px 12px;cursor:pointer;font-size:13.5px;display:flex;gap:8px;align-items:baseline;
    border-bottom:1px solid #f0efe8;
  }
  .result-item:last-child{border-bottom:none;}
  .result-item:hover,.result-item.active{background:var(--cream);}
  .result-item .num{color:var(--crimson);font-weight:700;min-width:34px;}
  .result-item .cat-tag{margin-left:auto;font-size:10px;color:#7a8a7c;text-transform:uppercase;letter-spacing:.5px;}
  .no-results{padding:14px 12px;font-size:13px;color:#888;}

  .toolbtn{
    background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#fff;
    border-radius:16px;padding:7px 13px;font-size:13px;cursor:pointer;white-space:nowrap;
    display:flex;align-items:center;gap:6px;transition:background .15s;
  }
  .toolbtn:hover{background:rgba(255,255,255,.22);}
  .toolbtn.active{background:var(--crimson);border-color:var(--crimson);}
  .zoomgroup{display:flex;align-items:center;background:rgba(255,255,255,.12);border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.25);}
  .zoomgroup button{
    background:transparent;border:none;color:#fff;width:32px;height:30px;font-size:16px;cursor:pointer;
  }
  .zoomgroup button:hover{background:rgba(255,255,255,.18);}
  .zoomgroup .pct{font-size:12px;min-width:42px;text-align:center;color:#e8e6da;}

  /* ---------- Body layout ---------- */
  .body{flex:1;position:relative;overflow:hidden;display:flex;}
  .viewport{
    flex:1;position:relative;overflow:hidden;cursor:grab;background:
      radial-gradient(ellipse at center, #123b66 0%, #0a2c52 100%);
    touch-action:none;
  }
  .viewport.grabbing{cursor:grabbing;}
  #world{position:absolute;top:0;left:0;transform-origin:0 0;will-change:transform;}
  #world.animate{transition:transform .45s cubic-bezier(.2,.7,.3,1);}

  .marker{cursor:pointer;}
  .marker circle.dot{
    fill:var(--navy);stroke:#fff;stroke-width:6;
    transition:fill .15s, r .15s;
  }
  .marker.residence circle.dot{fill:var(--residence);}
  .marker text{
    fill:#fff;font-weight:700;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
    text-anchor:middle;dominant-baseline:central;pointer-events:none;
  }
  .marker.dim{opacity:.28;}
  .marker.hidden-cat{display:none;}
  .marker.selected circle.dot{fill:var(--crimson);stroke:#fff;}
  .marker.hovered circle.dot{stroke:#ffd9a0;}
  .marker.start-point circle.dot,.marker.via-point circle.dot,.marker.end-point circle.dot{opacity:0;}

  .stop-badge{cursor:pointer;}
  .stop-badge .pin-shape{stroke:#fff;stroke-width:1.3;}
  .stop-badge.start .pin-shape{fill:#1f9e5c;}
  .stop-badge.via .pin-shape{fill:#d99a2b;}
  .stop-badge.end .pin-shape{fill:var(--crimson);}
  .stop-badge .pin-num{fill:#fff;font-weight:800;text-anchor:middle;dominant-baseline:central;pointer-events:none;}

  .route-line{stroke:var(--crimson);stroke-width:16;stroke-dasharray:38 26;fill:none;}
  .route-line.pulse{animation:dash 1.1s linear infinite;}
  @keyframes dash{to{stroke-dashoffset:-64;}}

  /* ---------- Legend panel ---------- */
  .legend{
    width:270px;background:var(--paper);border-left:1px solid var(--line);
    padding:16px 16px 20px;overflow-y:auto;flex-shrink:0;
    transform:translateX(0);transition:margin-right .25s ease;
  }
  .legend.closed{display:none;}
  .legend h2{
    font-family:Georgia,'Iowan Old Style',serif;font-size:17px;margin:0 0 3px;color:var(--navy-dark);
    border-bottom:2px solid var(--crimson);padding-bottom:8px;
  }
  .legend .sub{font-size:11px;color:#8a8577;margin:0 0 14px;letter-spacing:.3px;}
  .legend-section{margin-bottom:18px;}
  .legend-section h3{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:#6f6a5c;margin:0 0 8px;}
  .legend-row{display:flex;align-items:center;gap:10px;padding:6px 4px;border-radius:8px;font-size:13.5px;}
  .legend-row.toggleable{cursor:pointer;}
  .legend-row.toggleable:hover{background:#eeece2;}
  .swatch{width:20px;height:20px;border-radius:5px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;color:#fff;}
  .swatch.sw-residence{background:var(--residence-fill);border:2px solid var(--residence);}
  .swatch.sw-building{background:var(--navy);}
  .swatch.sw-admissions{background:#e8672c;}
  .swatch.sw-parking{background:#e8672c;}
  .swatch.sw-parking2{background:#b9bdbd;color:#0f3d71;border:1px solid #8d9191;}
  .swatch.sw-dining{background:#2f5fa8;}
  .toggle-check{
    margin-left:auto;width:17px;height:17px;border-radius:5px;border:2px solid #b7b19e;flex-shrink:0;
    display:flex;align-items:center;justify-content:center;
  }
  .toggle-check.checked{background:var(--navy);border-color:var(--navy);}
  .toggle-check.checked::after{content:'';width:8px;height:5px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg) translate(1px,-1px);}
  .legend-note{font-size:11.5px;color:#8a8577;line-height:1.5;margin-top:4px;}
  .count-badge{font-size:11px;color:#8a8577;margin-left:4px;}

  /* ---------- Info card ---------- */
  .info-card{
    position:absolute;left:16px;bottom:16px;background:#fff;border-radius:14px;
    box-shadow:0 10px 32px rgba(0,0,0,.28);padding:16px 18px;width:280px;
    display:none;z-index:30;
  }
  .info-card.show{display:block;}
  .info-card .close{position:absolute;top:8px;right:10px;border:none;background:none;font-size:18px;color:#999;cursor:pointer;}
  .info-card .num{color:var(--crimson);font-weight:800;font-size:13px;letter-spacing:.5px;}
  .info-card h3{margin:2px 0 4px;font-size:17px;font-family:Georgia,'Iowan Old Style',serif;color:var(--navy-dark);padding-right:14px;}
  .info-card .cat{font-size:11.5px;color:#6f6a5c;margin-bottom:12px;text-transform:uppercase;letter-spacing:.4px;}
  .info-card .actions{display:flex;gap:8px;flex-wrap:wrap;}
  .info-card button.act{
    border:1.5px solid var(--navy);background:#fff;color:var(--navy);border-radius:18px;
    padding:6px 12px;font-size:12.5px;cursor:pointer;font-weight:600;
  }
  .info-card button.act:hover{background:var(--navy);color:#fff;}
  .info-card button.act.start{border-color:#1f9e5c;color:#1f9e5c;}
  .info-card button.act.start:hover{background:#1f9e5c;color:#fff;}
  .info-card button.act.end{border-color:var(--crimson);color:var(--crimson);}
  .info-card button.act.end:hover{background:var(--crimson);color:#fff;}

  /* ---------- Directions panel ---------- */
  .directions-panel{
    position:absolute;top:14px;left:14px;background:#fff;border-radius:14px;
    box-shadow:0 10px 32px rgba(0,0,0,.28);padding:14px 16px;width:275px;display:none;z-index:30;
  }
  .directions-panel.show{display:block;}
  .directions-panel h3{margin:0 0 10px;display:flex;align-items:center;gap:8px;}
  .dp-toggle{flex:1;min-width:0;display:flex;align-items:center;gap:7px;background:none;border:none;padding:0;margin:0;cursor:pointer;text-align:left;font:inherit;-webkit-appearance:none;appearance:none;}
  .dp-toggle .tri{font-size:18px;line-height:1;color:var(--navy-dark);flex-shrink:0;transition:transform .15s ease;}
  .directions-panel:not(.collapsed) .dp-toggle .tri{transform:rotate(90deg);}
  .dp-toggle .dp-title{font-size:14px;font-weight:700;color:var(--navy-dark);white-space:nowrap;}
  .dp-toggle .dp-count{font-size:12.5px;font-weight:500;color:#8a8577;white-space:nowrap;}
  .dp-close-x{border:none;background:none;font-size:17px;color:#999;cursor:pointer;padding:0 2px;line-height:1;flex-shrink:0;-webkit-appearance:none;appearance:none;}
  .directions-panel.collapsed #dpStopsList{display:none;}
  .dp-stop{display:flex;align-items:center;gap:8px;font-size:13px;padding:7px 8px;border-radius:8px;background:#f7f6f1;margin-bottom:6px;}
  .dp-stop .dot{width:11px;height:11px;border-radius:50%;flex-shrink:0;}
  .dp-stop .dot.start{background:#1f9e5c;}
  .dp-stop .dot.via{background:#d99a2b;}
  .dp-stop .dot.end{background:var(--crimson);}
  .dp-stop .stop-info{flex:1;min-width:0;}
  .dp-stop .stop-name{color:var(--ink);line-height:1.35;}
  .dp-stop .stop-leg{font-size:11px;color:#8a8577;margin-top:2px;}
  .dp-stop .stop-actions{display:flex;flex-direction:row;gap:3px;flex-shrink:0;align-items:center;}
  .dp-stop .stop-actions button{
    border:none;background:transparent;color:#5f5a4c;cursor:pointer;font-size:11px;font-weight:700;
    width:22px;height:22px;line-height:1;padding:0;border-radius:5px;
    display:flex;align-items:center;justify-content:center;-webkit-appearance:none;appearance:none;
  }
  .dp-stop .stop-actions button:hover{background:#e8e5d8;color:var(--navy-dark);}
  .dp-stop .stop-actions button:disabled{opacity:.25;cursor:default;}
  .dp-stop .stop-actions button:disabled:hover{background:transparent;}
  .dp-stop .remove-btn{
    font-size:15px;font-weight:700;color:#c0a99a;flex-shrink:0;
    width:22px;height:22px;padding:0;line-height:1;border-radius:5px;
    display:flex;align-items:center;justify-content:center;
    border:none;background:transparent;cursor:pointer;-webkit-appearance:none;appearance:none;
  }
  .dp-stop .remove-btn:hover{color:var(--crimson);background:#fbe6e6;}
  .dp-empty-hint{font-size:12.5px;color:#a39d8a;font-style:italic;padding:8px 2px;}
  .dp-result{margin-top:10px;padding-top:10px;border-top:1px solid var(--line);font-size:13px;line-height:1.6;display:none;}
  .dp-result.show{display:block;}
  .dp-result b{color:var(--navy-dark);font-size:16px;}
  .dp-clear{margin-top:10px;width:100%;padding:7px;border-radius:8px;border:1px solid #d8d4c4;background:#fff;color:#6f6a5c;font-size:12.5px;cursor:pointer;-webkit-appearance:none;appearance:none;}
  .dp-clear:hover{background:#f0efe8;}
  .dp-share-btn{
    margin-top:10px;width:100%;padding:8px;border-radius:8px;border:1.5px solid var(--navy);
    background:#fff;color:var(--navy);font-size:12.5px;font-weight:600;cursor:pointer;
    -webkit-appearance:none;appearance:none;
  }
  .dp-share-btn:hover{background:var(--navy);color:#fff;}
  .dp-share-box{
    display:none;margin-top:8px;padding:10px;border-radius:8px;background:#f7f6f1;
    border:1px solid var(--line);
  }
  .dp-share-box.show{display:block;}
  .dp-share-box .row{display:flex;gap:6px;align-items:center;}
  .dp-share-label{font-size:11.5px;color:#6f6a5c;margin-bottom:6px;}
  .dp-share-box input{
    flex:1;min-width:0;font-size:11.5px;padding:6px 8px;border-radius:6px;
    border:1px solid #d8d4c4;background:#fff;color:var(--ink);-webkit-appearance:none;appearance:none;
  }
  .dp-share-box button.copy-btn{
    flex-shrink:0;border:1px solid var(--navy);background:var(--navy);color:#fff;
    border-radius:6px;padding:6px 10px;font-size:11.5px;cursor:pointer;-webkit-appearance:none;appearance:none;
  }
  .dp-share-box button.copy-btn:hover{background:var(--navy-dark);}
  .dp-share-msg{font-size:11px;color:#1f9e5c;font-weight:600;margin-top:6px;min-height:14px;}

  /* ---------- Edit mode ---------- */
  .edit-bar{
    position:absolute;top:14px;left:50%;transform:translateX(-50%);
    background:#1c2530;color:#fff;padding:9px 10px 9px 16px;border-radius:24px;
    display:none;align-items:center;gap:12px;font-size:13px;z-index:35;
    box-shadow:0 8px 24px rgba(0,0,0,.32);white-space:nowrap;
    pointer-events:none;
  }
  .edit-bar.show{display:flex;}
  .edit-bar button{border:1px solid rgba(255,255,255,.4);background:rgba(255,255,255,.12);color:#fff;border-radius:14px;padding:6px 12px;font-size:12px;cursor:pointer;pointer-events:auto;}
  .edit-bar button:hover{background:rgba(255,255,255,.24);}
  .edit-bar button:disabled{opacity:.4;cursor:default;}
  .edit-bar button:disabled:hover{background:rgba(255,255,255,.12);}
  .edit-bar .close-x{border:none;background:none;padding:0 2px;font-size:17px;line-height:1;}

  .viewport.edit-mode{cursor:default;}
  .viewport.edit-mode .marker,.viewport.edit-mode .stop-badge{cursor:grab;}
  .marker.dragging circle.dot{stroke:#ffd400;stroke-width:10;}
  .marker.edited circle.dot{stroke:#ffd400;stroke-width:7;stroke-dasharray:9 6;}
  .stop-badge.dragging .pin-shape{stroke:#ffd400;stroke-width:3;}

  /* ---------- Mobile ---------- */
  @media (max-width:760px){
    .brand .mark{font-size:16px;}
    .legend{
      position:fixed;left:0;right:0;bottom:0;top:auto;
      width:100%;max-height:72vh;z-index:45;
      border-left:none;border-radius:18px 18px 0 0;
      box-shadow:0 -10px 30px rgba(0,0,0,.35);
      padding-top:24px;
    }
    .legend::before{
      content:'';position:absolute;top:9px;left:50%;transform:translateX(-50%);
      width:38px;height:5px;border-radius:3px;background:#d3cebc;
    }
    .info-card,.directions-panel{width:calc(100vw - 32px);max-width:320px;}
    .zoomgroup .pct{display:none;}

    /* larger touch targets for the stop list */
    .dp-stop{gap:9px;padding:9px 8px;}
    .dp-stop .stop-actions{gap:4px;}
    .dp-stop .stop-actions button{width:32px;height:32px;font-size:13px;}
    .dp-stop .remove-btn{width:34px;height:34px;font-size:18px;}

    .edit-bar{
      white-space:normal;flex-wrap:wrap;justify-content:center;text-align:center;
      max-width:calc(100vw - 24px);top:8px;
    }
  }
</style>
</head>
<body>
<div class="app">
  <header>
    <div class="brand">
      <span class="mark">UD Campus Map<small>University of Delaware</small></span>
    </div>
    <div class="search-wrap" id="searchWrap">
      <input type="text" id="searchInput" placeholder="Search buildings by name or number..." autocomplete="off">
      <button class="clear-btn" id="clearSearch">&times;</button>
      <div class="results" id="results"></div>
    </div>
    <div class="zoomgroup">
      <button id="zoomOut" title="Zoom out">&minus;</button>
      <span class="pct" id="zoomPct">100%</span>
      <button id="zoomIn" title="Zoom in">+</button>
    </div>
    <button class="toolbtn" id="resetBtn">Reset zoom</button>
    <button class="toolbtn" id="directionsBtn">Directions</button>
    <button class="toolbtn" id="legendBtn">Legend</button>
  </header>

  <div class="body">
    <div class="viewport" id="viewport">
      <svg id="world" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 __IMG_W__ __IMG_H__" width="__IMG_W__" height="__IMG_H__">
        <image href="data:image/jpeg;base64,__IMG_B64__" x="0" y="0" width="__IMG_W__" height="__IMG_H__"></image>
        <path id="routePath" class="route-line" d="" style="display:none"></path>
        <g id="markers"></g>
        <g id="stopBadges"></g>
      </svg>
    </div>

    <div class="info-card" id="infoCard">
      <button class="close" id="infoClose">&times;</button>
      <div class="num" id="infoNum"></div>
      <h3 id="infoName"></h3>
      <div class="cat" id="infoCat"></div>
      <div class="actions">
        <button class="act start" id="addStopBtn">Add to route</button>
      </div>
    </div>

    <div class="directions-panel" id="directionsPanel">
      <h3>
        <button class="dp-toggle" id="dpCollapse" aria-expanded="true" title="Collapse or expand the stop list">
          <span class="tri">&#9656;</span>
          <span class="dp-title">Walking directions</span>
          <span class="dp-count" id="dpCount"></span>
        </button>
        <button class="dp-close-x" id="dpClose" title="Close">&times;</button>
      </h3>
      <div id="dpStopsList"></div>
      <div class="dp-result" id="dpResult"></div>
      <button class="dp-share-btn" id="dpShareBtn">Share route</button>
      <div class="dp-share-box" id="dpShareBox">
        <div class="dp-share-label">Copy this link:</div>
        <div class="row">
          <input type="text" id="shareUrlInput" readonly>
          <button class="copy-btn" id="shareCopyBtn">Copy</button>
        </div>
        <div class="dp-share-msg" id="shareMsg"></div>
      </div>
      <button class="dp-clear" id="dpClear">Clear all stops</button>
    </div>

    <div class="edit-bar" id="editBar">
      <span id="editBarText">Edit mode &mdash; drag any building marker or pin to move it.</span>
      <button id="downloadCorrections" disabled>Download corrected data</button>
      <button class="close-x" id="editBarClose" title="Exit edit mode">&times;</button>
    </div>

    <div class="legend closed" id="legendPanel">
      <h2>Campus Map</h2>
      <p class="sub">University of Delaware &middot; Office of Undergraduate Admissions</p>

      <div class="legend-section">
        <h3>Buildings <span class="count-badge" id="visibleCount"></span></h3>
        <div class="legend-row toggleable" id="toggleAll">
          <span class="swatch sw-building">174</span>
          <span>Academic &amp; other buildings</span>
          <span class="toggle-check checked" id="checkAll"></span>
        </div>
        <div class="legend-row toggleable" id="toggleResidence">
          <span class="swatch sw-residence">16</span>
          <span>Residence halls</span>
          <span class="toggle-check checked" id="checkResidence"></span>
        </div>
      </div>

      <div class="legend-section">
        <h3>Map key</h3>
        <div class="legend-row"><span class="swatch sw-admissions">A</span><span>Undergraduate Admissions Office</span></div>
        <div class="legend-row"><span class="swatch sw-parking">P</span><span>Visitor parking (pay to park)</span></div>
        <div class="legend-row"><span class="swatch sw-parking2">P</span><span>Newark municipal parking</span></div>
        <div class="legend-row"><span class="swatch sw-dining">&#127860;</span><span>Dining facilities</span></div>
        <div class="legend-row"><span class="swatch sw-dining">&#128214;</span><span>Bookstores</span></div>
        <div class="legend-row"><span class="swatch sw-dining">&#128702;</span><span>Restrooms</span></div>
        <p class="legend-note">These are shown as printed on the base map. Residence hall and building markers above are searchable and clickable; other map symbols are for reference.</p>
      </div>

      <div class="legend-section">
        <h3>Using this map</h3>
        <p class="legend-note">
          Drag to pan, scroll or pinch to zoom, or use the search box to jump to a building.
          Tap &ldquo;Directions&rdquo; in the toolbar, then click two buildings for a straight-line walking estimate.
        </p>
      </div>
    </div>
  </div>

  <footer>
    <button class="toolbtn" id="footerToggle">Tools &#9662;</button>
    <div class="footer-menu" id="footerMenu">
      <button class="toolbtn" id="hideNumbersBtn">Hide numbers</button>
      <button class="toolbtn" id="editModeBtn">Edit positions</button>
    </div>
    <span class="app-version" id="appVersion">__VERSION__</span>
  </footer>
</div>

<script>
const BUILDINGS = __BUILDINGS_JSON__;
const IMG_W = __IMG_W__, IMG_H = __IMG_H__;
const FT_PER_PX = __FT_PER_PX__;
const PIN_PATH = "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z";
const PIN_SCALE = 5.43;

const viewport = document.getElementById('viewport');
const world = document.getElementById('world');
const markersG = document.getElementById('markers');
const routePath = document.getElementById('routePath');
const stopBadgesG = document.getElementById('stopBadges');

let scale = 1, tx = 0, ty = 0;
let minScale = 0.05, maxScale = 3.5;

function fitToScreen(){
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  const s = Math.min(vw / IMG_W, vh / IMG_H) * 0.98;
  scale = s;
  minScale = s * 0.55;
  tx = (vw - IMG_W * s) / 2;
  ty = 24;
  applyTransform(false);
}

function applyTransform(animate){
  world.classList.toggle('animate', !!animate);
  world.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
  document.getElementById('zoomPct').textContent = Math.round(scale / initialScaleRef * 100) + '%';
  updateLabelVisibility();
}

let initialScaleRef = 1;

function zoomAt(factor, cx, cy){
  const newScale = Math.min(maxScale, Math.max(minScale, scale * factor));
  const ratio = newScale / scale;
  tx = cx - (cx - tx) * ratio;
  ty = cy - (cy - ty) * ratio;
  scale = newScale;
  applyTransform(false);
}

let numbersHidden = false;
function updateLabelVisibility(){
  const showLabels = !numbersHidden && scale > minScale * 2.2;
  markersG.classList.toggle('show-labels', showLabels);
  markersG.classList.toggle('hide-dots', numbersHidden);
}

// ---------- Build markers ----------
const markerEls = {};
BUILDINGS.forEach(b=>{
  const g = document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('class','marker' + (b.cat==='residence' ? ' residence' : ''));
  g.setAttribute('data-n', b.n);
  g.innerHTML = `<circle class="dot" cx="${b.x}" cy="${b.y}" r="34"></circle>
    <text x="${b.x}" y="${b.y}" font-size="30">${b.n}</text>`;
  markersG.appendChild(g);
  markerEls[b.n] = g;
});

const styleTag = document.createElement('style');
styleTag.textContent = `#markers .marker text{display:none;} #markers.show-labels .marker text{display:block;} #markers.hide-dots .marker circle.dot{opacity:0;}`;
document.head.appendChild(styleTag);

// ---------- Pan / zoom interaction ----------
let dragging = false, dragMoved=false, lastX=0, lastY=0, downPointerId=null;
let pointers = {};
let pinchStartDist = 0, pinchStartScale = 1;

// ---------- Edit mode (drag markers to fix positions) ----------
let editMode = false;
let draggingMarker = null;
let suppressNextClick = false;
let editedSet = new Set();

function screenToWorld(clientX, clientY){
  const r = viewport.getBoundingClientRect();
  return { x: (clientX - r.left - tx) / scale, y: (clientY - r.top - ty) / scale };
}
function updateMarkerDom(b){
  const g = markerEls[b.n];
  if (!g) return;
  const c = g.querySelector('circle.dot');
  const t = g.querySelector('text');
  c.setAttribute('cx', b.x); c.setAttribute('cy', b.y);
  t.setAttribute('x', b.x); t.setAttribute('y', b.y);
}
function startMarkerDrag(n, pointerId){
  draggingMarker = { n, moved:false, pointerId };
  try { viewport.setPointerCapture(pointerId); } catch(err) {}
  if (markerEls[n]) markerEls[n].classList.add('dragging');
  const pin = stopBadgesG.querySelector(`[data-n='${n}']`);
  if (pin) pin.classList.add('dragging');
}

markersG.addEventListener('pointerdown', e=>{
  if (!editMode) return;
  const g = e.target.closest('.marker');
  if (!g) return;
  e.stopPropagation();
  startMarkerDrag(parseInt(g.getAttribute('data-n')), e.pointerId);
});
stopBadgesG.addEventListener('pointerdown', e=>{
  if (!editMode) return;
  const g = e.target.closest('[data-n]');
  if (!g) return;
  e.stopPropagation();
  startMarkerDrag(parseInt(g.getAttribute('data-n')), e.pointerId);
});

viewport.addEventListener('pointerdown', e=>{
  pointers[e.pointerId] = {x:e.clientX, y:e.clientY};
  if (Object.keys(pointers).length === 1){
    dragging = true; dragMoved = false;
    lastX = e.clientX; lastY = e.clientY;
    downPointerId = e.pointerId;
  } else if (Object.keys(pointers).length === 2){
    dragging = false;
    if (downPointerId !== null && viewport.hasPointerCapture(downPointerId)){
      viewport.releasePointerCapture(downPointerId);
    }
    const pts = Object.values(pointers);
    pinchStartDist = Math.hypot(pts[0].x-pts[1].x, pts[0].y-pts[1].y);
    pinchStartScale = scale;
  }
});
viewport.addEventListener('pointermove', e=>{
  if (draggingMarker && draggingMarker.pointerId === e.pointerId){
    const wp = screenToWorld(e.clientX, e.clientY);
    const b = BUILDINGS.find(x=>x.n===draggingMarker.n);
    b.x = wp.x; b.y = wp.y;
    draggingMarker.moved = true;
    updateMarkerDom(b);
    if (stops.some(s=>s.n===b.n)) updateDirectionsUI();
    return;
  }
  if (pointers[e.pointerId]) pointers[e.pointerId] = {x:e.clientX, y:e.clientY};
  const n = Object.keys(pointers).length;
  if (n === 2){
    const pts = Object.values(pointers);
    const dist = Math.hypot(pts[0].x-pts[1].x, pts[0].y-pts[1].y);
    const rect = viewport.getBoundingClientRect();
    const cx = (pts[0].x+pts[1].x)/2 - rect.left;
    const cy = (pts[0].y+pts[1].y)/2 - rect.top;
    if (pinchStartDist > 0){
      const factor = dist / pinchStartDist;
      const targetScale = Math.min(maxScale, Math.max(minScale, pinchStartScale*factor));
      const ratio = targetScale/scale;
      tx = cx - (cx - tx) * ratio;
      ty = cy - (cy - ty) * ratio;
      scale = targetScale;
      applyTransform(false);
    }
  } else if (dragging){
    const dx = e.clientX - lastX, dy = e.clientY - lastY;
    if (!dragMoved && (Math.abs(dx)>3 || Math.abs(dy)>3)){
      dragMoved = true;
      if (downPointerId !== null){
        viewport.setPointerCapture(downPointerId);
      }
      viewport.classList.add('grabbing');
    }
    if (dragMoved){
      tx += dx; ty += dy;
      applyTransform(false);
    }
    lastX = e.clientX; lastY = e.clientY;
  }
});
function endPointer(e){
  if (draggingMarker && draggingMarker.pointerId === e.pointerId){
    const n = draggingMarker.n;
    if (markerEls[n]) markerEls[n].classList.remove('dragging');
    const pin = stopBadgesG.querySelector(`[data-n='${n}']`);
    if (pin) pin.classList.remove('dragging');
    if (draggingMarker.moved){
      editedSet.add(n);
      if (markerEls[n]) markerEls[n].classList.add('edited');
      suppressNextClick = true;
      setTimeout(()=>{ suppressNextClick = false; }, 250);
      updateEditBarText();
    }
    if (viewport.hasPointerCapture && viewport.hasPointerCapture(e.pointerId)){
      viewport.releasePointerCapture(e.pointerId);
    }
    draggingMarker = null;
    return;
  }
  delete pointers[e.pointerId];
  if (viewport.hasPointerCapture && viewport.hasPointerCapture(e.pointerId)){
    viewport.releasePointerCapture(e.pointerId);
  }
  if (Object.keys(pointers).length === 0){
    dragging = false;
    downPointerId = null;
    viewport.classList.remove('grabbing');
  }
}
viewport.addEventListener('pointerup', endPointer);
viewport.addEventListener('pointercancel', endPointer);
viewport.addEventListener('pointerleave', e=>{ if(Object.keys(pointers).length<=1) endPointer(e); });

viewport.addEventListener('wheel', e=>{
  e.preventDefault();
  const rect = viewport.getBoundingClientRect();
  const cx = e.clientX - rect.left, cy = e.clientY - rect.top;
  const delta = Math.max(-100, Math.min(100, e.deltaY));
  const factor = Math.exp(-delta * 0.00075);
  zoomAt(factor, cx, cy);
}, {passive:false});

document.getElementById('zoomIn').onclick = ()=>{
  const r = viewport.getBoundingClientRect();
  zoomAt(1.35, r.width/2, r.height/2);
};
document.getElementById('zoomOut').onclick = ()=>{
  const r = viewport.getBoundingClientRect();
  zoomAt(1/1.35, r.width/2, r.height/2);
};
document.getElementById('resetBtn').onclick = ()=>{ fitToScreen(); world.classList.add('animate'); setTimeout(()=>world.classList.remove('animate'),460); };

document.getElementById('footerToggle').onclick = ()=>{
  const menu = document.getElementById('footerMenu');
  const open = menu.classList.toggle('show');
  document.getElementById('footerToggle').innerHTML = open ? 'Tools &#9652;' : 'Tools &#9662;';
};

document.getElementById('hideNumbersBtn').onclick = ()=>{
  numbersHidden = !numbersHidden;
  const btn = document.getElementById('hideNumbersBtn');
  btn.classList.toggle('active', numbersHidden);
  btn.textContent = numbersHidden ? 'Show numbers' : 'Hide numbers';
  updateLabelVisibility();
};

const editBar = document.getElementById('editBar');
function setEditMode(on){
  editMode = on;
  const btn = document.getElementById('editModeBtn');
  btn.classList.toggle('active', editMode);
  btn.textContent = editMode ? 'Exit edit mode' : 'Edit positions';
  viewport.classList.toggle('edit-mode', editMode);
  editBar.classList.toggle('show', editMode);
  if (editMode){
    infoCard.classList.remove('show');
    if (selectedNum && markerEls[selectedNum]) markerEls[selectedNum].classList.remove('selected');
    selectedNum = null;
    if (directionsMode) toggleDirections(false);
    updateEditBarText();
  }
}
document.getElementById('editModeBtn').onclick = ()=> setEditMode(!editMode);
document.getElementById('editBarClose').onclick = ()=> setEditMode(false);

function updateEditBarText(){
  const n = editedSet.size;
  document.getElementById('editBarText').textContent = n===0
    ? 'Edit mode \u2014 drag any building marker or pin to move it.'
    : `Edit mode \u2014 ${n} building${n===1?'':'s'} moved.`;
  document.getElementById('downloadCorrections').disabled = n===0;
}

document.getElementById('downloadCorrections').onclick = ()=>{
  const data = BUILDINGS.map(b=>({
    n: b.n, name: b.name, cat: b.cat,
    x: Math.round(b.x*10)/10, y: Math.round(b.y*10)/10
  }));
  const blob = new Blob([JSON.stringify(data)], {type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'buildings_corrected.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

// ---------- Center on a building ----------
function centerOn(b, targetScale){
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  scale = targetScale;
  tx = vw/2 - b.x*scale;
  ty = vh/2 - b.y*scale;
  applyTransform(true);
}

// ---------- Fit the view to the current route stops ----------
function fitStopsView(){
  if (stops.length === 0) return;
  if (stops.length === 1){
    centerOn(stops[0], Math.max(scale, initialScaleRef*2.2));
    return;
  }
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  stops.forEach(s=>{
    minX=Math.min(minX,s.x); maxX=Math.max(maxX,s.x);
    minY=Math.min(minY,s.y); maxY=Math.max(maxY,s.y);
  });
  const bw = Math.max(maxX-minX, 300);
  const bh = Math.max(maxY-minY, 300);
  const vw = viewport.clientWidth, vh = viewport.clientHeight;
  let newScale = Math.min(vw/bw, vh/bh) * 0.8; // ~20% breathing room around the route
  newScale = Math.min(maxScale, Math.max(minScale, newScale));
  const cx = (minX+maxX)/2, cy = (minY+maxY)/2;
  scale = newScale;
  tx = vw/2 - cx*scale;
  ty = vh/2 - cy*scale;
  applyTransform(true);
}

// ---------- Marker click ----------
let selectedNum = null;
markersG.addEventListener('click', e=>{
  if (editMode || suppressNextClick){ suppressNextClick = false; return; }
  const g = e.target.closest('.marker');
  if (!g) return;
  const n = parseInt(g.getAttribute('data-n'));
  const b = BUILDINGS.find(x=>x.n===n);
  onBuildingChosen(b);
});

stopBadgesG.addEventListener('click', e=>{
  if (editMode || suppressNextClick){ suppressNextClick = false; return; }
  const g = e.target.closest('[data-n]');
  if (!g) return;
  const n = parseInt(g.getAttribute('data-n'));
  const b = BUILDINGS.find(x=>x.n===n);
  onBuildingChosen(b);
});

function onBuildingChosen(b){
  if (directionsMode){
    toggleStop(b);
  } else {
    showInfoCard(b);
    highlightSelected(b.n);
    const targetScale = Math.max(scale, initialScaleRef*2.2);
    centerOn(b, targetScale);
  }
}

function highlightSelected(n){
  if (selectedNum && markerEls[selectedNum]) markerEls[selectedNum].classList.remove('selected');
  selectedNum = n;
  if (markerEls[n]) markerEls[n].classList.add('selected');
}

// ---------- Info card ----------
const infoCard = document.getElementById('infoCard');
const addStopBtn = document.getElementById('addStopBtn');
function showInfoCard(b){
  document.getElementById('infoNum').textContent = '#' + b.n;
  document.getElementById('infoName').textContent = b.name;
  document.getElementById('infoCat').textContent = b.cat==='residence' ? 'Residence hall' : 'Campus building';
  infoCard.classList.add('show');
  infoCard.dataset.n = b.n;
  const inRoute = stops.some(s=>s.n===b.n);
  addStopBtn.textContent = inRoute ? 'Remove from route' : 'Add to route';
}
document.getElementById('infoClose').onclick = ()=>{
  infoCard.classList.remove('show');
  if (selectedNum && markerEls[selectedNum]) markerEls[selectedNum].classList.remove('selected');
  selectedNum = null;
};
addStopBtn.onclick = ()=>{
  const b = BUILDINGS.find(x=>x.n===parseInt(infoCard.dataset.n));
  if(!directionsMode) toggleDirections(true);
  toggleStop(b);
};

// ---------- Search ----------
const searchInput = document.getElementById('searchInput');
const resultsEl = document.getElementById('results');
const searchWrap = document.getElementById('searchWrap');

function runSearch(q){
  q = q.trim().toLowerCase();
  if (!q){ resultsEl.classList.remove('show'); return; }
  const matches = BUILDINGS.filter(b=>{
    return b.name.toLowerCase().includes(q) || String(b.n)===q;
  }).slice(0,10);
  resultsEl.innerHTML='';
  if (matches.length===0){
    resultsEl.innerHTML = '<div class="no-results">No buildings match &ldquo;'+escapeHtml(q)+'&rdquo;</div>';
  } else {
    matches.forEach(b=>{
      const div = document.createElement('div');
      div.className='result-item';
      div.innerHTML = `<span class="num">#${b.n}</span><span>${escapeHtml(b.name)}</span>` +
        (b.cat==='residence' ? '<span class="cat-tag">Residence</span>' : '');
      div.onclick = ()=>{
        searchInput.value = b.name;
        resultsEl.classList.remove('show');
        onBuildingChosen(b);
      };
      resultsEl.appendChild(div);
    });
  }
  resultsEl.classList.add('show');
}
function escapeHtml(s){ return s.replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

searchInput.addEventListener('input', e=>{
  searchWrap.classList.toggle('has-text', !!e.target.value);
  runSearch(e.target.value);
});
searchInput.addEventListener('focus', e=>{ if(e.target.value) runSearch(e.target.value); });
document.getElementById('clearSearch').onclick = ()=>{
  searchInput.value=''; searchWrap.classList.remove('has-text'); resultsEl.classList.remove('show'); searchInput.focus();
};
document.addEventListener('click', e=>{
  if (!searchWrap.contains(e.target)) resultsEl.classList.remove('show');
});

// ---------- Legend / filters ----------
const legendPanel = document.getElementById('legendPanel');
document.getElementById('legendBtn').onclick = ()=>{
  legendPanel.classList.toggle('closed');
  document.getElementById('legendBtn').classList.toggle('active');
};

let showBuildings = true, showResidence = true;
function refreshFilter(){
  let visible = 0;
  BUILDINGS.forEach(b=>{
    const el = markerEls[b.n];
    const shouldShow = b.cat==='residence' ? showResidence : showBuildings;
    el.classList.toggle('hidden-cat', !shouldShow);
    if (shouldShow) visible++;
  });
  document.getElementById('visibleCount').textContent = '(' + visible + ' shown)';
}
document.getElementById('toggleAll').onclick = ()=>{
  showBuildings = !showBuildings;
  document.getElementById('checkAll').classList.toggle('checked', showBuildings);
  refreshFilter();
};
document.getElementById('toggleResidence').onclick = ()=>{
  showResidence = !showResidence;
  document.getElementById('checkResidence').classList.toggle('checked', showResidence);
  refreshFilter();
};
refreshFilter();

// ---------- Directions ----------
let directionsMode = false;
let stops = [];
const dPanel = document.getElementById('directionsPanel');

function toggleDirections(forceOn){
  directionsMode = forceOn===true ? true : !directionsMode;
  document.getElementById('directionsBtn').classList.toggle('active', directionsMode);
  dPanel.classList.toggle('show', directionsMode);
  if (directionsMode){
    infoCard.classList.remove('show');
    if (editMode) setEditMode(false);
  }
}
document.getElementById('directionsBtn').onclick = ()=>toggleDirections();
document.getElementById('dpClose').onclick = ()=>toggleDirections(false);
document.getElementById('dpCollapse').onclick = ()=>{
  const collapsed = dPanel.classList.toggle('collapsed');
  document.getElementById('dpCollapse').setAttribute('aria-expanded', String(!collapsed));
};

function formatDist(feet){
  return feet < 1000 ? Math.round(feet)+' ft' : (feet/5280).toFixed(2)+' mi';
}
function formatWalk(feet){
  return Math.max(1, Math.round(feet/264)); // ~3 mph
}

function toggleStop(b){
  const idx = stops.findIndex(s=>s.n===b.n);
  if (idx >= 0){ stops.splice(idx,1); }
  else { stops.push(b); }
  updateDirectionsUI();
  fitStopsView();
}
function removeStop(n){
  const idx = stops.findIndex(s=>s.n===n);
  if (idx>=0){ stops.splice(idx,1); updateDirectionsUI(); fitStopsView(); }
}
function moveStop(n, dir){
  const idx = stops.findIndex(s=>s.n===n);
  const j = idx + dir;
  if (idx<0 || j<0 || j>=stops.length) return;
  [stops[idx], stops[j]] = [stops[j], stops[idx]];
  updateDirectionsUI();
}

function updateDirectionsUI(){
  const listEl = document.getElementById('dpStopsList');
  const resultEl = document.getElementById('dpResult');

  // the route just changed, so any previously copied/shown share link is stale
  document.getElementById('dpShareBox').classList.remove('show');
  clearTimeout(shareMsgTimer);
  document.getElementById('shareMsg').textContent = '';

  // stop count in the collapsible header
  document.getElementById('dpCount').textContent =
    stops.length ? '· ' + stops.length + ' stop' + (stops.length===1?'':'s') : '';

  if (stops.length === 0){
    listEl.innerHTML = `<div class="dp-empty-hint">Click buildings on the map (or search) to add stops to your route.</div>`;
  } else {
    listEl.innerHTML = stops.map((s,i)=>{
      const isFirst = i===0, isLast = i===stops.length-1;
      const dotClass = isFirst ? 'start' : (isLast ? 'end' : 'via');
      let leg = '';
      if (!isLast){
        const nxt = stops[i+1];
        const feet = Math.hypot(s.x-nxt.x, s.y-nxt.y) * FT_PER_PX;
        leg = `<div class="stop-leg">${formatDist(feet)} to next stop</div>`;
      }
      return `<div class="dp-stop">
        <div class="stop-actions">
          <button class="reorder" data-act="up" data-n="${s.n}" ${isFirst?'disabled':''} title="Move up">&#9650;</button>
          <button class="reorder" data-act="down" data-n="${s.n}" ${isLast?'disabled':''} title="Move down">&#9660;</button>
        </div>
        <span class="dot ${dotClass}"></span>
        <div class="stop-info">
          <div class="stop-name">${i+1}. #${s.n} ${escapeHtml(s.name)}</div>
          ${leg}
        </div>
        <button class="remove-btn" data-act="remove" data-n="${s.n}" title="Remove stop">&#10005;</button>
      </div>`;
    }).join('');
  }

  // marker highlighting
  Object.values(markerEls).forEach(el=>el.classList.remove('start-point','via-point','end-point'));
  stops.forEach((s,i)=>{
    const el = markerEls[s.n];
    if (!el) return;
    if (i===0) el.classList.add('start-point');
    else if (i===stops.length-1) el.classList.add('end-point');
    else el.classList.add('via-point');
  });

  // sequence pins (map-pin icon anchored at the building; number sits in the head)
  stopBadgesG.innerHTML = '';
  stops.forEach((s,i)=>{
    const isFirst = i===0, isLast = i===stops.length-1;
    const roleClass = isFirst ? 'start' : (isLast ? 'end' : 'via');
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','stop-badge ' + roleClass);
    g.setAttribute('data-n', s.n);
    g.innerHTML = `<g transform="translate(${s.x},${s.y}) scale(${PIN_SCALE}) translate(-12,-22)">
      <path class="pin-shape" d="${PIN_PATH}"></path>
      <text class="pin-num" x="12" y="9.4" font-size="6.3">${i+1}</text>
    </g>`;
    stopBadgesG.appendChild(g);
  });

  // total distance + route path
  if (stops.length >= 2){
    let totalFeet = 0;
    let d = `M ${stops[0].x} ${stops[0].y}`;
    for (let i=1;i<stops.length;i++){
      totalFeet += Math.hypot(stops[i-1].x-stops[i].x, stops[i-1].y-stops[i].y) * FT_PER_PX;
      d += ` L ${stops[i].x} ${stops[i].y}`;
    }
    resultEl.innerHTML = `<b>${formatDist(totalFeet)}</b> total straight-line &middot; about ${formatWalk(totalFeet)} min walk &middot; ${stops.length} stops`;
    resultEl.classList.add('show');
    routePath.setAttribute('d', d);
    routePath.style.display = 'block';
    routePath.classList.add('pulse');
  } else {
    resultEl.classList.remove('show');
    routePath.style.display = 'none';
    routePath.classList.remove('pulse');
  }
}

document.getElementById('dpStopsList').addEventListener('click', e=>{
  const btn = e.target.closest('button');
  if (!btn) return;
  const n = parseInt(btn.getAttribute('data-n'));
  const act = btn.getAttribute('data-act');
  if (act==='remove') removeStop(n);
  else if (act==='up') moveStop(n, -1);
  else if (act==='down') moveStop(n, 1);
});

document.getElementById('dpClear').onclick = ()=>{
  stops = []; updateDirectionsUI();
};

// ---------- Share route ----------
function buildShareUrl(){
  const base = location.href.split('?')[0].split('#')[0];
  return base + '?route=' + stops.map(s=>s.n).join(',');
}

let shareMsgTimer = null;
function showCopiedMessage(success){
  const msgEl = document.getElementById('shareMsg');
  clearTimeout(shareMsgTimer);
  if (success){
    msgEl.textContent = 'Copied';
    shareMsgTimer = setTimeout(()=>{ msgEl.textContent = ''; }, 2500);
  } else {
    msgEl.textContent = '';
  }
}

function fallbackCopy(url){
  const input = document.getElementById('shareUrlInput');
  input.value = url;
  input.focus();
  input.select();
  input.setSelectionRange(0, url.length);
  let ok = false;
  try { ok = document.execCommand('copy'); } catch(err) { ok = false; }
  return ok;
}

function copyToClipboard(url){
  const input = document.getElementById('shareUrlInput');
  input.value = url;
  input.focus();
  input.select();
  input.setSelectionRange(0, url.length);

  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(url)
      .then(()=> showCopiedMessage(true))
      .catch(()=> showCopiedMessage(fallbackCopy(url)));
  } else {
    showCopiedMessage(fallbackCopy(url));
  }
}

function revealShareBox(url){
  const input = document.getElementById('shareUrlInput');
  input.value = url;
  document.getElementById('dpShareBox').classList.add('show');
  input.focus();
  input.select();
  input.setSelectionRange(0, url.length);
}

document.getElementById('dpShareBtn').onclick = ()=>{
  if (stops.length === 0) return;
  const url = buildShareUrl();
  revealShareBox(url);
};
document.getElementById('shareCopyBtn').onclick = ()=>{
  const url = document.getElementById('shareUrlInput').value || buildShareUrl();
  copyToClipboard(url);
};

// ---------- Load a shared route from the URL, if present ----------
function loadRouteFromURL(){
  const params = new URLSearchParams(location.search);
  const routeParam = params.get('route');
  if (!routeParam) return false;
  const nums = routeParam.split(',').map(s=>parseInt(s.trim(),10)).filter(n=>!isNaN(n)).slice(0,50);
  const validStops = nums.map(n=>BUILDINGS.find(b=>b.n===n)).filter(Boolean);
  if (validStops.length === 0) return false;
  stops = validStops;
  toggleDirections(true);
  updateDirectionsUI();
  fitStopsView();
  return true;
}

// ---------- Init ----------
window.addEventListener('resize', ()=>{ fitToScreen(); });
fitToScreen();
initialScaleRef = scale;
document.getElementById('zoomPct').textContent = '100%';
loadRouteFromURL();
</script>
</body>
</html>
"""

version = datetime.now().strftime('v.%Y%m%d.%H%M')
html = html.replace('__IMG_W__', str(IMG_W)).replace('__IMG_H__', str(IMG_H))
html = html.replace('__FT_PER_PX__', str(FT_PER_PX))
html = html.replace('__BUILDINGS_JSON__', buildings_json)
html = html.replace('__IMG_B64__', img_b64)
html = html.replace('__VERSION__', version)

with open('index.html', 'w') as f:
    f.write(html)

print("HTML written, size (MB):", len(html)/1024/1024)
