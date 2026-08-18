let BUILDINGS = [];
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
function buildMarkers(){
  BUILDINGS.forEach(b=>{
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class','marker' + (b.cat==='residence' ? ' residence' : ''));
    g.setAttribute('data-n', b.n);
    g.innerHTML = `<circle class="dot" cx="${b.x}" cy="${b.y}" r="34"></circle>
      <text x="${b.x}" y="${b.y}" font-size="30">${b.n}</text>`;
    markersG.appendChild(g);
    markerEls[b.n] = g;
  });
}

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
        <span class="dot ${dotClass}"></span>
        <div class="stop-info">
          <div class="stop-name">${i+1}. #${s.n} ${escapeHtml(s.name)}</div>
          ${leg}
        </div>
        <div class="stop-actions">
          <button class="reorder" data-act="up" data-n="${s.n}" ${isFirst?'disabled':''} title="Move up">&#8593;</button>
          <button class="reorder" data-act="down" data-n="${s.n}" ${isLast?'disabled':''} title="Move down">&#8595;</button>
        </div>
        <button class="remove-btn" data-act="remove" data-n="${s.n}" title="Remove stop">&times;</button>
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
window.addEventListener('resize', ()=>{ if (BUILDINGS.length) fitToScreen(); });

function imageReady(){
  return new Promise(resolve=>{
    const img = document.getElementById('mapImage');
    if (window.__mapImgLoaded) { resolve(); return; }
    img.addEventListener('load', ()=>resolve(), {once:true});
    img.addEventListener('error', ()=>resolve(), {once:true});
  });
}

async function boot(){
  const overlay = document.getElementById('loadingOverlay');
  try {
    const [resp] = await Promise.all([fetch('buildings.json'), imageReady()]);
    BUILDINGS = await resp.json();
  } catch (err) {
    console.error('Failed to load campus map data:', err);
    if (overlay) overlay.querySelector('.loading-text').textContent =
      'Could not load the map data. Please check your connection and refresh.';
    return;
  }
  buildMarkers();
  refreshFilter();
  fitToScreen();
  initialScaleRef = scale;
  document.getElementById('zoomPct').textContent = '100%';
  loadRouteFromURL();
  if (overlay) overlay.classList.add('hidden');
}
boot();
