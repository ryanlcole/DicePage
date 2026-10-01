#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import shutil
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "earth-truth-pack-v1"
CACHE = ROOT / "build" / "earth-truth-source-cache"
ARTIFACTS = ROOT / "build" / "artifacts"
WIDTH = 2048
HEIGHT = 1024
PACK_ID = "earth-truth-asset-pack-v1"

SOURCES = {
    "natural_earth_land": {
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson",
        "license": "Public domain",
        "credit": "Natural Earth",
    },
    "natural_earth_landmarks": {
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_geography_regions_points.geojson",
        "license": "Public domain",
        "credit": "Natural Earth",
    },
    "natural_earth_peaks": {
        "url": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_geography_regions_elevation_points.geojson",
        "license": "Public domain",
        "credit": "Natural Earth",
    },
    "tectonic_boundaries": {
        "url": "https://raw.githubusercontent.com/fraxen/tectonicplates/master/GeoJSON/PB2002_boundaries.json",
        "license": "Open Data Commons Attribution License",
        "credit": "Peter Bird; Hugo Ahlenius / Nordpil; fraxen dataset conversion",
    },
    "hyg_stars": {
        "url": "https://raw.githubusercontent.com/astronexus/HYG-Database/main/hyg/CURRENT/hygdata_v41.csv",
        "license": "CC BY-SA 4.0",
        "credit": "Astronexus HYG Database",
    },
}

def ensure_dirs():
    for p in [
        BUILD,
        CACHE,
        ARTIFACTS,
        BUILD / "world" / "layers",
        BUILD / "characters" / "lomekwi3",
        BUILD / "beliefs",
        BUILD / "manifests",
        BUILD / "sources",
        BUILD / "history",
    ]:
        p.mkdir(parents=True, exist_ok=True)

def download(name, meta):
    target = CACHE / Path(meta["url"]).name
    if target.exists() and target.stat().st_size > 100:
        return target
    req = urllib.request.Request(meta["url"], headers={"User-Agent": "Shaelvien-Earth-Truth-Pack/1.0"})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as response, target.open("wb") as out:
                shutil.copyfileobj(response, out)
            if target.stat().st_size <= 100:
                raise RuntimeError(f"Downloaded source {name} is unexpectedly small")
            return target
        except Exception as exc:
            last = exc
            time.sleep(2 + attempt)
    raise RuntimeError(f"Unable to download {name}: {last}")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def project(lon, lat):
    return ((float(lon) + 180.0) / 360.0 * WIDTH, (90.0 - float(lat)) / 180.0 * HEIGHT)

def fmt(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")

def ring_path(coords):
    pts = [project(p[0], p[1]) for p in (coords or []) if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not pts:
        return ""
    return "M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + " Z"

def polygon_path(geometry):
    if not geometry:
        return ""
    typ = geometry.get("type")
    c = geometry.get("coordinates") or []
    parts = []
    if typ == "Polygon":
        for ring in c:
            p = ring_path(ring)
            if p:
                parts.append(p)
    elif typ == "MultiPolygon":
        for poly in c:
            for ring in poly:
                p = ring_path(ring)
                if p:
                    parts.append(p)
    return " ".join(parts)

def line_paths(geometry):
    if not geometry:
        return []
    typ = geometry.get("type")
    c = geometry.get("coordinates") or []
    lines = []
    if typ == "LineString":
        lines = [c]
    elif typ == "MultiLineString":
        lines = c
    elif typ == "Polygon":
        lines = c
    elif typ == "MultiPolygon":
        for poly in c:
            lines.extend(poly)
    result = []
    for line in lines:
        pts = [project(p[0], p[1]) for p in line if isinstance(p, (list, tuple)) and len(p) >= 2]
        if pts:
            result.append("M " + " L ".join(f"{fmt(x)} {fmt(y)}" for x, y in pts))
    return result

def svg_wrap(title, description, body, bg=None, metadata=None):
    bg_rect = f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{bg}"/>' if bg else ""
    md = html.escape(json.dumps(metadata or {}, separators=(",", ":")))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<title>{html.escape(title)}</title>
<desc>{html.escape(description)}</desc>
<metadata>{md}</metadata>
{bg_rect}
{body}
</svg>
'''

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_text(rel, text):
    path = BUILD / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path

def render_sea_level(land_path):
    data = load_json(land_path)
    parts = []
    for feature in data.get("features", []):
        p = polygon_path(feature.get("geometry"))
        if p:
            parts.append(f'<path d="{p}" fill="#86765b" stroke="#c7b894" stroke-width="0.7" fill-rule="evenodd"/>')
    return svg_wrap(
        "Earth sea-level terrain",
        "Natural Earth land geometry over a global ocean field. Geometry is factual cartographic source data; visual styling is representation.",
        "\n".join(parts),
        bg="#173a56",
        metadata={
            "classification": "FACT_GEOMETRY",
            "semanticBand": "SEA_LEVEL",
            "projection": "equirectangular",
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def render_tectonics(path):
    data = load_json(path)
    paths = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        label = html.escape(str(props.get("Type") or props.get("type") or props.get("Name") or "plate boundary"))
        for p in line_paths(feature.get("geometry")):
            paths.append(
                f'<path d="{p}" fill="none" stroke="#b08a62" stroke-width="1.2" stroke-opacity="0.75"><title>{label}</title></path>'
            )
    return svg_wrap(
        "Earth underground geology context",
        "Generalized tectonic plate boundaries used as a world-scale subsurface/geology cue. This is not a literal depth slice.",
        "\n".join(paths),
        metadata={
            "classification": "FACT_CONTEXT",
            "semanticBand": "UNDERGROUND",
            "literalDepth": False,
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def property_ci(props, *names):
    lower = {str(k).lower(): v for k, v in (props or {}).items()}
    for name in names:
        if name.lower() in lower and lower[name.lower()] not in (None, ""):
            return lower[name.lower()]
    return None

def point_from_geometry(geometry):
    if not geometry or geometry.get("type") != "Point":
        return None
    c = geometry.get("coordinates") or []
    if len(c) < 2:
        return None
    return project(c[0], c[1])

def render_landmarks(path):
    data = load_json(path)
    marks = []
    for feature in data.get("features", []):
        pt = point_from_geometry(feature.get("geometry"))
        if not pt:
            continue
        props = feature.get("properties") or {}
        name = str(property_ci(props, "name", "nameascii", "name_en") or "physical landmark")
        x, y = pt
        marks.append(
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="2.1" fill="#efd89a" stroke="#6b5a38" stroke-width="0.6"><title>{html.escape(name)}</title></circle>'
        )
    return svg_wrap(
        "Earth physical landmarks",
        "Natural Earth geographic-region point features. Cultural and historical landmarks belong to time-sliced history packs rather than this timeless physical layer.",
        "\n".join(marks),
        metadata={
            "classification": "FACT_GEOGRAPHY",
            "semanticBand": "LANDMARKS",
            "timeSlicedCulturalLandmarks": True,
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def render_peaks(path):
    data = load_json(path)
    marks = []
    for feature in data.get("features", []):
        pt = point_from_geometry(feature.get("geometry"))
        if not pt:
            continue
        props = feature.get("properties") or {}
        name = str(property_ci(props, "name", "nameascii", "name_en") or "mountain peak")
        elev_raw = property_ci(props, "elevation", "elev", "elev_m", "elevation_m")
        try:
            elev = float(elev_raw)
        except Exception:
            elev = 0.0
        size = max(2.3, min(7.5, 2.5 + max(elev, 0.0) / 1800.0))
        x, y = pt
        pts = f"{fmt(x)},{fmt(y-size)} {fmt(x-size)},{fmt(y+size)} {fmt(x+size)},{fmt(y+size)}"
        title = name + (f" — {int(elev)} m" if elev > 0 else "")
        marks.append(
            f'<polygon points="{pts}" fill="#d7d2c7" stroke="#6d6a64" stroke-width="0.7"><title>{html.escape(title)}</title></polygon>'
        )
    return svg_wrap(
        "Earth mountain peaks",
        "Natural Earth elevation-point geometry. Marker size is perceptual and is not a literal vertical scale.",
        "\n".join(marks),
        metadata={
            "classification": "FACT_GEOGRAPHY",
            "semanticBand": "MOUNTAIN_PEAKS",
            "markerScale": "PERCEPTUAL_ONLY",
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def render_sky():
    body = '''<defs>
<linearGradient id="sky" x1="0" y1="1" x2="0" y2="0">
<stop offset="0%" stop-color="#9ecbe3" stop-opacity="0.12"/>
<stop offset="55%" stop-color="#507fa8" stop-opacity="0.20"/>
<stop offset="100%" stop-color="#1f365a" stop-opacity="0.28"/>
</linearGradient>
</defs>
<rect width="2048" height="1024" fill="url(#sky)"/>'''
    return svg_wrap(
        "Sky perception layer",
        "Atmospheric color veil for readable depth. This is a perceptual representation, not a global simultaneous sky-state claim.",
        body,
        metadata={
            "classification": "PERCEPTUAL_REPRESENTATION",
            "semanticBand": "SKY",
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def render_stars(path):
    circles = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                mag = float(row.get("mag") or "")
                ra = float(row.get("ra") or "")
                dec = float(row.get("dec") or "")
            except Exception:
                continue
            if mag > 5.0:
                continue
            x = (ra % 24.0) / 24.0 * WIDTH
            y = (90.0 - dec) / 180.0 * HEIGHT
            radius = max(0.55, min(2.8, 0.65 + (5.0 - mag) * 0.36))
            name = row.get("proper") or row.get("bf") or row.get("gl") or row.get("hip") or "catalog star"
            circles.append(
                f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="{fmt(radius)}" fill="#fff" fill-opacity="0.88"><title>{html.escape(str(name))}; mag {mag:.2f}</title></circle>'
            )
    return svg_wrap(
        "Bright stars J2000",
        "HYG bright-star positions in an equirectangular celestial projection. Alignment to the Earth map is perceptual until transformed for observer location and time.",
        "\n".join(circles),
        metadata={
            "classification": "FACT_CATALOG",
            "semanticBand": "STARS",
            "epoch": "J2000",
            "earthAlignment": "PERCEPTUAL_UNTIL_TIME_LOCATION_TRANSFORM",
            "parallaxDistance": "PERCEPTUAL_ONLY",
        },
    )

def belief_fx_svg():
    frames = []
    frames.append('<g transform="translate(0 0)"><ellipse cx="32" cy="31" rx="23" ry="14" fill="none" stroke="#d9d9d9" stroke-width="3"/><circle cx="32" cy="31" r="6" fill="#d9d9d9"/></g>')
    frames.append('<g transform="translate(64 0)"><path d="M12 38 C8 21 24 12 39 20 C50 14 60 24 54 36 C60 47 44 54 33 49 C20 55 9 49 12 38 Z" fill="none" stroke="#d9d9d9" stroke-width="3"/><circle cx="19" cy="55" r="3" fill="#d9d9d9"/></g>')
    frames.append('<g transform="translate(128 0)"><path d="M32 8 C18 8 14 21 16 34 L12 54 L22 48 L32 54 L42 48 L52 54 L48 34 C50 21 46 8 32 8 Z" fill="none" stroke="#d9d9d9" stroke-width="3"/><circle cx="26" cy="28" r="2" fill="#d9d9d9"/><circle cx="38" cy="28" r="2" fill="#d9d9d9"/></g>')
    frames.append('<g transform="translate(192 0)"><path d="M32 7 L37 24 L55 24 L40 34 L46 52 L32 41 L18 52 L24 34 L9 24 L27 24 Z" fill="none" stroke="#d9d9d9" stroke-width="3"/></g>')
    frames.append('<g transform="translate(256 0)"><circle cx="32" cy="32" r="10" fill="none" stroke="#d9d9d9" stroke-width="3"/><path d="M32 5 V16 M32 48 V59 M5 32 H16 M48 32 H59 M12 12 L20 20 M44 44 L52 52 M52 12 L44 20 M20 44 L12 52" stroke="#d9d9d9" stroke-width="3"/></g>')
    frames.append('<g transform="translate(320 0)"><path d="M10 42 Q26 16 52 22 Q39 34 28 35 Q20 36 10 42 Z" fill="none" stroke="#d9d9d9" stroke-width="3"/><path d="M28 35 L49 49" stroke="#d9d9d9" stroke-width="3"/></g>')
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="384" height="64" viewBox="0 0 384 64" shape-rendering="crispEdges">
<title>Belief manifestation effects</title>
<desc>Generic effects for source-bound attested beliefs. They do not assert that a specific supernatural claim is empirically verified.</desc>
''' + "".join(frames) + "\n</svg>\n"

def preview_html():
    layers = [
        ("UNDERGROUND", "layers/00_underground_geology_context.svg", -45),
        ("SEA LEVEL", "layers/10_sea_level_terrain.svg", 0),
        ("LANDMARKS", "layers/20_landmarks_physical.svg", 12),
        ("MOUNTAIN PEAKS", "layers/30_mountain_peaks.svg", 22),
        ("SKY", "layers/40_sky_perception.svg", 36),
        ("STARS", "layers/50_stars_j2000.svg", 52),
    ]
    imgs = "\n".join(
        f'<img class="layer" data-z="{z}" data-band="{name}" src="{src}" alt="{name}"/>'
        for name, src, z in layers
    )
    checks = "\n".join(
        f'<label><input type="checkbox" data-toggle="{name}" checked> {name}</label>'
        for name, _, _ in layers
    )
    return '''<!doctype html>
<meta charset="utf-8">
<title>Earth Truth Pack World Stack</title>
<style>
html,body{margin:0;background:#101218;color:#eee;font:14px system-ui;height:100%;overflow:hidden}
#stage{position:absolute;inset:0;display:grid;place-items:center;perspective:1200px;overflow:hidden}
#stack{position:relative;width:min(96vw,1400px);aspect-ratio:2/1;transform-style:preserve-3d}
.layer{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;pointer-events:none;transition:transform .12s ease,opacity .12s ease}
#panel{position:fixed;left:12px;top:12px;z-index:5;padding:10px;background:#000b;border:1px solid #7778;border-radius:8px;max-width:520px}
#panel label{display:inline-block;margin:3px 8px 3px 0}
button{margin:4px 6px 4px 0}
.small{opacity:.78;font-size:12px}
</style>
<div id="stage"><div id="stack">''' + imgs + '''</div></div>
<div id="panel"><b>EARTH TRUTH WORLD STACK</b><br>
<button id="all">ALL WORLD BANDS</button><button id="sea">SEA LEVEL ONLY</button><br>
''' + checks + '''
<div class="small">Geometry/data truth and presentation are separate. World-scale Z spacing is perceptual only. Zoom handoff target: WORLD → REGION → LOCAL; LOCAL Tier/Layer Z may become literal.</div></div>
<script>
const stage=document.querySelector("#stage"), layers=[...document.querySelectorAll(".layer")];
function apply(px,py){for(const el of layers){const z=Number(el.dataset.z)||0;el.style.transform="translate("+(px*z*.002)+"px,"+(py*z*.002)+"px) translateZ("+(z*2)+"px)";}}
stage.addEventListener("pointermove",e=>{const r=stage.getBoundingClientRect();apply(e.clientX-r.width/2,e.clientY-r.height/2);});
document.querySelector("#all").onclick=()=>layers.forEach(x=>x.style.opacity=1);
document.querySelector("#sea").onclick=()=>layers.forEach(x=>x.style.opacity=x.dataset.band==="SEA LEVEL"?1:0);
document.querySelectorAll("[data-toggle]").forEach(box=>box.onchange=()=>{const n=box.dataset.toggle;layers.find(x=>x.dataset.band===n).style.opacity=box.checked?1:0;});
</script>
'''

def build_manifests(source_hashes):
    world = {
        "schema": "shaelvien.earth.world-stack.v1",
        "identity": {"world": "Geonaph", "physicalReferent": "Earth"},
        "worldScaleBands": [
            {"id":"UNDERGROUND","asset":"world/layers/00_underground_geology_context.svg","truth":"FACT_CONTEXT","displayZ":-45},
            {"id":"SEA_LEVEL","asset":"world/layers/10_sea_level_terrain.svg","truth":"FACT_GEOMETRY","displayZ":0,"mmoSurfaceCandidate":True},
            {"id":"LANDMARKS","asset":"world/layers/20_landmarks_physical.svg","truth":"FACT_GEOGRAPHY","displayZ":12},
            {"id":"MOUNTAIN_PEAKS","asset":"world/layers/30_mountain_peaks.svg","truth":"FACT_GEOGRAPHY","displayZ":22},
            {"id":"SKY","asset":"world/layers/40_sky_perception.svg","truth":"PERCEPTUAL_REPRESENTATION","displayZ":36},
            {"id":"STARS","asset":"world/layers/50_stars_j2000.svg","truth":"FACT_CATALOG_WITH_PERCEPTUAL_ALIGNMENT","displayZ":52},
        ],
        "laws": [
            "Geonaph is Earth. Geography must remain source-grounded.",
            "Representation is not semantic truth.",
            "World-scale parallax spacing is permitted fiction for perception and must not be interpreted as measured altitude or depth.",
            "MMO deed-map optimization may use only the sea-level representation without deleting higher world-view bands.",
            "Zoom hands representation from WORLD to REGION to LOCAL.",
            "At LOCAL scope, Tier/Layer structure may represent literal internal spatial design when backed by the local source model."
        ],
        "sourceHashes": source_hashes,
    }
    install = {
        "schema":"shaelvien.earth.install-manifest.v1",
        "targetWorld":"shaelvien-geonaph-alpha-001",
        "worldViewer":{"defaultMode":"ALL_WORLD_BANDS","seaLevelMode":"SEA_LEVEL","zMode":"PERCEPTUAL"},
        "mmoViewer":{"mode":"SEA_LEVEL_ONLY","resourcePolicy":"LIGHTWEIGHT"},
        "handoff":["WORLD","REGION","LOCAL"],
        "localTierLayerMode":"LITERAL_WHEN_SOURCE_BACKED",
        "doNotInstallAsTruth":["belief manifestation effects","parallax distances","reconstruction body morphology"],
    }
    beliefs = {
        "schema":"shaelvien.earth.belief-sprites.v1",
        "campaignRule":"Historically attested beliefs may manifest as true within the playable campaign.",
        "historicalTruthRule":"The historical record may establish that a belief, vision, miracle report, prophecy, deity, spirit, or myth was attested; that is distinct from empirical verification of the supernatural claim.",
        "activationRule":"Do not activate a named belief entity before a source-backed attestation appropriate to the culture, place, and chronology.",
        "lomekwi3":{"attestedBeliefs":[],"status":"NO_BELIEF_SYSTEM_ATTESTED_AT_THIS_NODE"},
        "effectsSheet":"beliefs/manifestation_fx.svg",
        "effects":[
            {"frame":0,"id":"VISION"},
            {"frame":1,"id":"DREAM"},
            {"frame":2,"id":"APPARITION"},
            {"frame":3,"id":"CELESTIAL_SIGN"},
            {"frame":4,"id":"SACRED_PRESENCE"},
            {"frame":5,"id":"OMEN"},
        ],
        "futureHistoricalCharacterClasses":["PROPHET","SEER","CULTURAL_PROTAGONIST","RULER","TEACHER","REFORMER"],
        "namedCharacterRule":"Create named sprites from era-specific evidence and iconographic sources. When appearance is unknown, label the sprite RECONSTRUCTION.",
    }
    character = {
        "schema":"shaelvien.earth.characters.v1",
        "openingPlayablePopulation":{
            "displayLabel":"Earliest Playable Ancestral Population",
            "site":"Lomekwi 3",
            "date":"~3.3 Ma",
            "taxonomicIdentity":"UNRESOLVED",
            "sheet":"characters/lomekwi3/lom3-toolmaker-actions.svg",
            "manifest":"characters/lomekwi3/sprite-set.json",
            "classification":"RECONSTRUCTION",
            "factBoundary":[
                "Stone artefacts at Lomekwi 3 date to about 3.3 Ma.",
                "Core reduction and battering/percussive activity are reported.",
                "The taxonomic identity of the toolmakers is unresolved."
            ],
        },
        "evolutionRule":"Morphology, species identity, technology, language, and migration behavior change only when the next verified historical/evolutionary node supports the change.",
        "migrationRule":"Use the strongest current evidence for population movement; preserve competing routes as uncertainty rather than forcing false certainty.",
    }
    history = {
        "schema":"shaelvien.earth.history-play.v1",
        "loop":["FACT","PLAYER_ACTION","RESOLUTION","FICTIONAL_BRIDGE","NEXT_VERIFIED_FACT"],
        "beliefExperience":"Attested beliefs are playable as manifested reality inside the campaign without rewriting the provenance record.",
        "prophetSeerRule":"When a source-backed prophet, seer, protagonist, or reported supernatural encounter enters the chronology, players may experience the interaction directly. The asset record must retain what is historically attested versus reconstructed for play.",
        "openingNode":{"region":"West Turkana","local":"Lomekwi 3","instance":"LOM3 Tool-Making Locality","date":"~3.3 Ma"},
    }
    write_text("manifests/world-stack.json", json.dumps(world, indent=2))
    write_text("manifests/install-manifest.json", json.dumps(install, indent=2))
    write_text("characters/manifest.json", json.dumps(character, indent=2))
    write_text("beliefs/manifest.json", json.dumps(beliefs, indent=2))
    write_text("history/play-rules.json", json.dumps(history, indent=2))

def build_readme():
    return """# Earth Truth Asset Pack v1

Geonaph is Earth.

This package separates what the source data says from how Shaelvien presents it.

## World-scale bands

1. UNDERGROUND — generalized tectonic/geology context.
2. SEA LEVEL — Earth oceans and continental land geometry.
3. LANDMARKS — source-grounded physical geographic points.
4. MOUNTAIN PEAKS — source-grounded elevation points.
5. SKY — perceptual atmosphere overlay.
6. STARS — HYG J2000 bright-star positions.

The visual distance between these bands is not literal physical Z. It exists to make the world readable in parallax.

## Spatial handoff

WORLD → REGION → LOCAL.

At WORLD scale, band spacing is perceptual. REGION replaces the world representation as the player zooms. LOCAL can use literal Tier/Layer structure for internal design when supported by the local source model.

## Player origin

The first installed playable node remains Lomekwi 3 (~3.3 Ma). The toolmaker's taxonomic identity is unresolved. The character sprite is therefore a bounded reconstruction, not a named species claim.

## Beliefs, myths, prophets, and seers

The campaign may let historically attested beliefs manifest as true to the players. The data record still distinguishes the historical fact that a belief/report/person/text is attested from reconstruction needed for play and from the campaign manifestation of the belief.

No belief system is invented for Lomekwi 3 because none is attested there. Named deities, spirits, prophets, seers, miracles, and protagonists are added at the correct source-backed chronological node.

Open world/preview.html to inspect the world bands and switch to SEA LEVEL ONLY.
"""

def build_sources_md(source_hashes):
    return """# Sources and licenses

## Natural Earth
Used for global land geometry, physical landmark points, and elevation points.
Natural Earth data is public domain.
https://www.naturalearthdata.com/

## PB2002 tectonic plate boundaries
Peter Bird, An updated digital model of plate boundaries, Geochemistry, Geophysics, Geosystems (2003).
GeoJSON distribution used here is from fraxen/tectonicplates and carries the Open Data Commons Attribution License.
https://github.com/fraxen/tectonicplates

## HYG Database v4.1
Used for bright-star J2000 positions. HYG v4.x is CC BY-SA 4.0.
https://github.com/astronexus/HYG-Database

## Lomekwi 3
Harmand, S. et al. 3.3-million-year-old stone tools from Lomekwi 3, West Turkana, Kenya. Nature 521, 310–315 (2015). DOI: 10.1038/nature14464.
https://www.nature.com/articles/nature14464

## Source hashes used for this build

""" + json.dumps(source_hashes, indent=2) + """

The HYG-derived star layer remains subject to CC BY-SA 4.0. Other layers retain their source-specific terms above.
"""

def copy_project_assets():
    src_svg = ROOT / "apps" / "rist-world" / "wwwroot" / "assets" / "geonaph" / "history" / "lomekwi3" / "sprites" / "lom3-toolmaker-actions.svg"
    src_manifest = src_svg.with_name("sprite-set.json")
    campaign = ROOT / "apps" / "rist-world" / "wwwroot" / "data" / "geonaph" / "history" / "campaign-v1.json"
    if not src_svg.exists() or not src_manifest.exists() or not campaign.exists():
        raise RuntimeError("Required current Lomekwi project assets are missing")
    shutil.copy2(src_svg, BUILD / "characters" / "lomekwi3" / src_svg.name)
    shutil.copy2(src_manifest, BUILD / "characters" / "lomekwi3" / src_manifest.name)
    shutil.copy2(campaign, BUILD / "history" / "campaign-v1.json")

def validate_pack():
    required = [
        "world/layers/00_underground_geology_context.svg",
        "world/layers/10_sea_level_terrain.svg",
        "world/layers/20_landmarks_physical.svg",
        "world/layers/30_mountain_peaks.svg",
        "world/layers/40_sky_perception.svg",
        "world/layers/50_stars_j2000.svg",
        "world/preview.html",
        "characters/lomekwi3/lom3-toolmaker-actions.svg",
        "characters/lomekwi3/sprite-set.json",
        "beliefs/manifestation_fx.svg",
        "beliefs/manifest.json",
        "manifests/world-stack.json",
        "manifests/install-manifest.json",
        "history/play-rules.json",
        "sources/SOURCES.md",
        "README.md",
    ]
    missing = [p for p in required if not (BUILD / p).exists()]
    if missing:
        raise RuntimeError("Pack missing required files: " + ", ".join(missing))
    world = json.loads((BUILD / "manifests" / "world-stack.json").read_text())
    bands = [x["id"] for x in world["worldScaleBands"]]
    if bands != ["UNDERGROUND","SEA_LEVEL","LANDMARKS","MOUNTAIN_PEAKS","SKY","STARS"]:
        raise RuntimeError("World band order changed unexpectedly")
    chars = json.loads((BUILD / "characters" / "manifest.json").read_text())
    if chars["openingPlayablePopulation"]["taxonomicIdentity"] != "UNRESOLVED":
        raise RuntimeError("Lomekwi toolmaker taxonomy was overclaimed")
    beliefs = json.loads((BUILD / "beliefs" / "manifest.json").read_text())
    if beliefs["lomekwi3"]["attestedBeliefs"] != []:
        raise RuntimeError("Prehistoric belief system was invented for Lomekwi 3")

def make_zip():
    zip_path = ARTIFACTS / f"{PACK_ID}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(BUILD.rglob("*")):
            if path.is_file():
                z.write(path, Path(PACK_ID) / path.relative_to(BUILD))
    return zip_path

def main():
    ensure_dirs()
    downloaded = {name: download(name, meta) for name, meta in SOURCES.items()}
    hashes = {name: {"sha256": sha256(path), **SOURCES[name]} for name, path in downloaded.items()}

    write_text("world/layers/00_underground_geology_context.svg", render_tectonics(downloaded["tectonic_boundaries"]))
    write_text("world/layers/10_sea_level_terrain.svg", render_sea_level(downloaded["natural_earth_land"]))
    write_text("world/layers/20_landmarks_physical.svg", render_landmarks(downloaded["natural_earth_landmarks"]))
    write_text("world/layers/30_mountain_peaks.svg", render_peaks(downloaded["natural_earth_peaks"]))
    write_text("world/layers/40_sky_perception.svg", render_sky())
    write_text("world/layers/50_stars_j2000.svg", render_stars(downloaded["hyg_stars"]))
    write_text("world/preview.html", preview_html())
    write_text("beliefs/manifestation_fx.svg", belief_fx_svg())

    copy_project_assets()
    build_manifests(hashes)
    write_text("README.md", build_readme())
    write_text("sources/SOURCES.md", build_sources_md(hashes))
    validate_pack()
    zip_path = make_zip()
    print(json.dumps({"pack": str(zip_path), "size": zip_path.stat().st_size, "sha256": sha256(zip_path)}, indent=2))

if __name__ == "__main__":
    main()
