from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "wwwroot" / "css" / "rist.css"

AUTHORITY = r'''

/* ========================================================================== */
/* RIST MAP VIEWER AUTHORITY                                                   */
/* The recursive map is also the bounded viewer for every open workspace.      */
/* ========================================================================== */
.release-world .map-viewer-region{
 position:relative!important;
 isolation:isolate!important;
 overflow:hidden!important;
}
.release-world .map-viewer-region>.table-workspace{
 position:absolute!important;
 inset:0!important;
 z-index:1!important;
 width:100%!important;
 height:100%!important;
 min-width:0!important;
 min-height:0!important;
 overflow:hidden!important;
}
.release-world .map-viewer-overlays{
 box-sizing:border-box!important;
 position:absolute!important;
 inset:0!important;
 z-index:200!important;
 width:100%!important;
 height:100%!important;
 min-width:0!important;
 min-height:0!important;
 overflow:hidden!important;
 pointer-events:none!important;
}

/* Full viewer workspaces: never escape the map rectangle. */
.release-world .map-viewer-region .card-browser,
.release-world .map-viewer-overlays>.asset-slider-stack,
.release-world .map-viewer-overlays>.native-character-modal,
.release-world .map-viewer-overlays>.rist-tutorial-shell{
 box-sizing:border-box!important;
 position:absolute!important;
 inset:6px!important;
 z-index:230!important;
 width:auto!important;
 height:auto!important;
 min-width:0!important;
 min-height:0!important;
 max-width:none!important;
 max-height:none!important;
 margin:0!important;
 overflow:hidden!important;
 border-radius:10px!important;
 pointer-events:auto!important;
}
.release-world .map-viewer-region .card-browser,
.release-world .map-viewer-overlays>.asset-slider-stack,
.release-world .map-viewer-overlays>.rist-tutorial-shell{
 background:#071017f8!important;
 border:1px solid var(--rw-border)!important;
 box-shadow:0 12px 34px #000c!important;
}

/* Character sheet becomes a contained viewer rather than a viewport modal. */
.release-world .map-viewer-overlays>.native-character-modal{
 display:grid!important;
 place-items:stretch!important;
 padding:0!important;
 background:#03070ac7!important;
}
.release-world .map-viewer-overlays .native-character-sheet{
 box-sizing:border-box!important;
 position:relative!important;
 inset:auto!important;
 width:100%!important;
 height:100%!important;
 max-width:100%!important;
 max-height:100%!important;
 min-width:0!important;
 min-height:0!important;
 margin:0!important;
 overflow:auto!important;
}

/* Card and asset library internals consume the viewer, then scroll internally. */
.release-world .map-viewer-region .card-browser{
 display:grid!important;
 grid-template-rows:auto minmax(0,1fr)!important;
}
.release-world .map-viewer-region .card-library-workspace,
.release-world .map-viewer-region .card-library-results,
.release-world .map-viewer-overlays .asset-slider-stack,
.release-world .map-viewer-overlays .asset-horizontal-rail{
 min-width:0!important;
 min-height:0!important;
 max-width:100%!important;
 max-height:100%!important;
}
.release-world .map-viewer-region .card-library-workspace,
.release-world .map-viewer-region .card-library-results{
 overflow:auto!important;
}
.release-world .map-viewer-overlays>.asset-slider-stack{
 display:grid!important;
 grid-template-rows:auto minmax(0,1fr)!important;
}

/* Header root panels render over the map, never beneath the root rail. */
.release-world .root-menu-panel,
.release-world .release-action-menu{
 box-sizing:border-box!important;
 position:fixed!important;
 z-index:950!important;
 top:calc(var(--rw-context) + var(--rw-menu) + var(--rw-public) + 6px)!important;
 right:6px!important;
 bottom:calc(var(--rw-private) + var(--rw-footer) + 6px)!important;
 left:6px!important;
 width:auto!important;
 height:auto!important;
 max-width:none!important;
 max-height:none!important;
 margin:0!important;
 overflow:auto!important;
 padding:44px 12px 12px!important;
 border:1px solid var(--rw-border)!important;
 border-radius:10px!important;
 background:#071017f8!important;
 box-shadow:0 12px 34px #000c!important;
 backdrop-filter:blur(7px)!important;
}

/* Persistent recursion controls stay a compact map tool, not a full menu. */
.release-world .map-viewer-overlays>.recursion-cockpit{
 box-sizing:border-box!important;
 position:absolute!important;
 z-index:210!important;
 top:8px!important;
 right:8px!important;
 left:auto!important;
 bottom:auto!important;
 max-width:min(360px,calc(100% - 16px))!important;
 max-height:calc(100% - 16px)!important;
 overflow:auto!important;
 pointer-events:auto!important;
}
.release-world .map-viewer-overlays>.mmo-zone-actions:not([hidden]){
 box-sizing:border-box!important;
 position:absolute!important;
 z-index:220!important;
 inset:8px!important;
 overflow:auto!important;
 pointer-events:auto!important;
}

/* Every opened viewer gets a consistent close control in its own top-right edge. */
.map-viewer-close{
 box-sizing:border-box!important;
 position:absolute!important;
 z-index:1200!important;
 top:7px!important;
 right:7px!important;
 width:34px!important;
 height:34px!important;
 min-width:34px!important;
 min-height:34px!important;
 display:grid!important;
 place-items:center!important;
 margin:0!important;
 padding:0!important;
 border:1px solid #9b7c36!important;
 border-radius:8px!important;
 background:#0b1319f5!important;
 color:#f0d58f!important;
 font:900 23px/30px system-ui,-apple-system,sans-serif!important;
 box-shadow:0 3px 10px #0009!important;
 cursor:pointer!important;
 pointer-events:auto!important;
}
.map-viewer-close:active{background:#24313a!important;color:#fff4cf!important}
.release-world .root-menu-panel>.map-viewer-close,
.release-world .release-action-menu>.map-viewer-close{position:fixed!important;top:calc(var(--rw-context) + var(--rw-menu) + var(--rw-public) + 13px)!important;right:13px!important}

@media (max-height:600px) and (orientation:landscape){
 .release-world .root-menu-panel,
 .release-world .release-action-menu{padding-top:38px!important}
 .map-viewer-close{width:30px!important;height:30px!important;min-width:30px!important;min-height:30px!important;font-size:20px!important}
}
'''

text = CSS.read_text(encoding="utf-8")
marker = "/* RIST MAP VIEWER AUTHORITY"
if marker in text:
    text = text[:text.index(marker)].rstrip() + "\n"
CSS.write_text(text.rstrip() + "\n" + AUTHORITY.strip() + "\n", encoding="utf-8")
print("Applied RIST map viewer authority")
