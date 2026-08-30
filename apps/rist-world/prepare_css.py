from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS_DIR = ROOT / "wwwroot" / "css"
OUTPUT = CSS_DIR / "rist.css"

SOURCES = [
    "app.css", "adaptive-grid.css", "spatial-surface.css", "hand-rail.css",
    "dice-geometry.css", "tabletop-dials-mobile.css", "character-console.css",
    "physical-controls-refinement.css", "character-card-pass.css", "tracks-pass.css",
    "character-families.css", "interaction-fixes.css", "shaelvien-cards.css",
    "intuitive-card-editor.css", "footer-uniform.css", "rail-final.css",
    "library-rails.css", "mobile-horizontal-rails.css", "character-native.css",
    "character-profile-alignment.css", "character-profile-tiles.css",
    "shaelvien-cursors.css", "info-legal.css", "grid-coordinate-system.css",
    "map-packets.css", "map-context-sidebar.css", "portrait-profile-geometry.css",
    "recursion-cockpit.css", "start-menu.css", "mmo-mode.css", "prelogin-visitor.css",
    "rist-tutorial.css", "discord-login.css", "mobile-history-fixes.css",
    "calforth-token-lite.css", "token-rail-visuals.css", "faux-depth.css",
    "home-viewport.css",
]

IMPORT_RE = re.compile(r"@import\s+url\((?:['\"])?([^)'\"]+)(?:['\"])?\)\s*;", re.I)

def archived(name: str) -> Path:
    return CSS_DIR / f"{name}.old"

def inline_imports(text: str, stack: tuple[str, ...]) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        if raw.startswith(("http://", "https://", "data:")):
            raise RuntimeError(f"External CSS import is not allowed: {raw}")
        name = raw.split("?", 1)[0].lstrip("./")
        if name in stack:
            raise RuntimeError(f"CSS import cycle: {' -> '.join(stack + (name,))}")
        path = archived(name)
        if not path.exists():
            raise FileNotFoundError(f"Missing archived CSS import: {path}")
        return inline_imports(path.read_text(encoding="utf-8"), stack + (name,))
    return IMPORT_RE.sub(replace, text)

FINAL_AUTHORITY = r'''
/* ========================================================================== */
/* RIST VISUAL AUTHORITY — 2026-08-30                                         */
/* Static artwork is one AWS object per control. Only functional spritesheets */
/* may use frame cropping. Container geometry owns size; artwork never does.  */
/* ========================================================================== */
:root{
 --rist-gold:#725d30;
 --rist-gold-bright:#d7be80;
 --rist-panel:#0d1319;
 --rist-control:#111920;
 --rist-icon-base:"https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons";
 --rist-header-h:54px!important;
 --rist-public-h:86px!important;
 --rist-private-h:86px!important;
 --rist-dice-h:60px!important;
 --rist-chat-h:58px!important;
 --rist-legal-h:14px!important;
 --rist-footer-h:132px!important;
}

/* ----- header rail -------------------------------------------------------- */
.rist #header-slider{overflow:hidden!important;background:var(--rist-panel)!important}
.rist #header-slider .header-circular-set{height:100%!important;align-items:center!important;gap:8px!important;padding:3px 8px!important}
.rist #header-slider .header-icon-button,
.rist #header-slider .control{
 box-sizing:border-box!important;flex:0 0 96px!important;width:96px!important;min-width:96px!important;max-width:96px!important;
 height:48px!important;min-height:48px!important;max-height:48px!important;margin:0!important;
 border:1px solid var(--rist-gold)!important;border-radius:10px!important;background:var(--rist-control)!important;overflow:hidden!important
}
.rist #header-slider .header-icon-button{display:grid!important;place-items:center!important;padding:4px!important}
.rist #header-slider .control{position:relative!important;display:grid!important;place-items:center!important;padding:3px!important}
.rist #header-slider .header-icon{
 display:block!important;width:34px!important;height:34px!important;min-width:34px!important;min-height:34px!important;max-width:34px!important;max-height:34px!important;
 margin:auto!important;background-color:transparent!important;background-position:center!important;background-repeat:no-repeat!important;background-size:contain!important;
 filter:none!important;transform:none!important;pointer-events:none!important
}
.rist #header-slider .header-icon::before,.rist #header-slider .header-icon::after{content:none!important}
.rist #header-slider .icon-exit{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/door.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-encounter{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/mode.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-assets{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/assets.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-browse{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/browse.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-role{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/role.svg?v=20260830-clean-1")!important}
.rist #header-slider [class*="icon-grid-"]{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/grid.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-scale{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/scale.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-save{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/save.svg?v=20260830-clean-1")!important}
.rist #header-slider .icon-load{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/load.svg?v=20260830-clean-1")!important}
.rist #header-slider .control select{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;opacity:0!important;cursor:pointer!important}
.rist #header-slider .scale-stack{box-sizing:border-box!important;flex:0 0 96px!important;width:96px!important;height:48px!important;display:grid!important;align-content:center!important;padding:4px!important;border:1px solid var(--rist-gold)!important;border-radius:10px!important;background:var(--rist-control)!important}

/* MMO is already a standalone static image pair. */
.rist .header-mmo-button .mmo-toggle-art{display:block!important;width:100%!important;height:100%!important;background:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/sandbox-toggle.webp?v=20260830-clean-1") center/contain no-repeat!important}
.rist .header-mmo-button.mmo-art-active .mmo-toggle-art{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/mmo-toggle.webp?v=20260830-clean-1")!important}
.rist .header-mmo-button .mmo-toggle-art>img{display:none!important}

/* ----- shared public/private asset rails --------------------------------- */
.rist>.public-assets-rail,.rist>.private-assets-rail{overflow:hidden!important;background:var(--rist-panel)!important}
.rist .public-assets-strip,.rist .private-assets-strip{display:block!important;width:100%!important;min-width:0!important;height:100%!important;overflow:hidden!important}
.rist .public-assets-items,.rist .private-assets-items{
 box-sizing:border-box!important;width:100%!important;min-width:0!important;height:100%!important;display:flex!important;align-items:center!important;gap:8px!important;
 overflow-x:auto!important;overflow-y:hidden!important;padding:5px 8px!important;scrollbar-width:none!important
}
.rist .public-assets-items::-webkit-scrollbar,.rist .private-assets-items::-webkit-scrollbar{display:none!important}
.rist .public-assets-strip>.rail-scroll-arrow,.rist .private-assets-strip>.rail-scroll-arrow{display:none!important}
.rist .public-assets-items>button,.rist .private-assets-items>button,.rist .private-assets-items .hand-card-wrap{
 box-sizing:border-box!important;flex:0 0 58px!important;width:58px!important;min-width:58px!important;max-width:58px!important
}
.rist .public-assets-items .public-asset-card,.rist .private-assets-items .compact-hand-card,.rist .private-assets-items .standard-hand-card{
 height:46px!important;min-height:46px!important;max-height:46px!important;display:grid!important;place-items:center!important;padding:3px!important;overflow:hidden!important;
 border:1px solid var(--rist-gold)!important;border-radius:8px!important;background:var(--rist-control)!important
}
.rist .public-assets-items .public-asset-card>img,.rist .private-assets-items .compact-hand-card>img,.rist .private-assets-items .standard-hand-card>img{
 display:block!important;width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important;object-fit:contain!important;object-position:center!important;margin:0!important
}
.rist .private-assets-items .hand-toggle-card-back{display:block!important;width:100%!important;height:100%!important;background-size:contain!important;background-position:center!important;background-repeat:no-repeat!important}

/* Map pin is one standalone AWS SVG. Never crop it as a sprite. */
.rist .public-assets-rail .token-pin-source,.rist .private-assets-rail .token-pin-source{
 box-sizing:border-box!important;flex:0 0 58px!important;width:58px!important;min-width:58px!important;max-width:58px!important;height:46px!important;min-height:46px!important;max-height:46px!important;
 display:grid!important;place-items:center!important;padding:5px!important;overflow:hidden!important;border:1px solid var(--rist-gold)!important;border-radius:8px!important;background:var(--rist-control)!important;box-shadow:none!important
}
.rist .public-assets-rail .map-pin-icon,.rist .private-assets-rail .map-pin-icon{
 display:block!important;width:30px!important;height:36px!important;min-width:30px!important;min-height:36px!important;max-width:30px!important;max-height:36px!important;margin:auto!important;
 border:0!important;border-radius:0!important;box-shadow:none!important;transform:none!important;background:transparent url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/map-pin.svg?v=20260830-clean-1") center/contain no-repeat!important;pointer-events:none!important
}
.rist .map-pin-icon::before,.rist .map-pin-icon::after{content:none!important}
.rist .piece.pin{background:transparent!important;border:0!important;box-shadow:none!important}.rist .piece.pin::after{content:none!important}

/* True sprites retain frame math. */
.rist .die-sprite,.rist .rolled-die,.rist .magic-coin-sprite,.rist .mixer-sprite,.rist .sprite-sheet,.rist [class*="sprite-"]{max-width:none}
.rist .elemental-token-selector{height:46px!important;display:flex!important;align-items:center!important}.rist .elemental-token-active{width:58px!important;height:46px!important;min-width:58px!important;min-height:46px!important;padding:3px!important}.rist .elemental-token-active .magic-coin-sprite{width:38px!important;height:38px!important}

/* ----- footer/legal ------------------------------------------------------- */
.rist .home-footer-stack{box-sizing:border-box!important;height:var(--rist-footer-h)!important;min-height:var(--rist-footer-h)!important;max-height:var(--rist-footer-h)!important;grid-template-rows:var(--rist-dice-h) var(--rist-chat-h) var(--rist-legal-h)!important;overflow:hidden!important}
.rist .home-footer-stack #footer-slider{height:var(--rist-dice-h)!important;min-height:var(--rist-dice-h)!important;max-height:var(--rist-dice-h)!important}
.rist .home-inline-chat{height:var(--rist-chat-h)!important;min-height:var(--rist-chat-h)!important;max-height:var(--rist-chat-h)!important}
.rist .site-copyright-notice{display:flex!important;align-items:center!important;justify-content:center!important;height:var(--rist-legal-h)!important;min-height:var(--rist-legal-h)!important;padding:0 6px!important;color:#d2b873!important;background:#071118!important;border-top:1px solid #4d4023!important;font:600 7px/1 system-ui,-apple-system,sans-serif!important;opacity:1!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}

@media(orientation:landscape){
 :root{--rist-header-h:50px!important;--rist-public-h:72px!important;--rist-private-h:72px!important;--rist-dice-h:54px!important;--rist-chat-h:54px!important;--rist-legal-h:10px!important;--rist-footer-h:64px!important}
 .rist .home-footer-stack{height:64px!important;min-height:64px!important;max-height:64px!important;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr)!important;grid-template-rows:54px 10px!important}
 .rist .home-inline-chat{grid-column:1!important;grid-row:1!important}.rist .home-footer-stack #footer-slider{grid-column:2!important;grid-row:1!important}.rist .site-copyright-notice{grid-column:1/-1!important;grid-row:2!important;height:10px!important;min-height:10px!important}
}
'''

def main() -> None:
    sections = ["/* AUTO-GENERATED by apps/rist-world/prepare_css.py. */", "/* rist.css is the only runtime stylesheet. */"]
    for name in SOURCES:
        path = archived(name)
        if not path.exists():
            raise FileNotFoundError(f"Missing archived CSS source: {path}")
        body = inline_imports(path.read_text(encoding="utf-8"), (name,))
        sections.append(f"\n/* SOURCE: {name}.old */\n{body}")
    sections.append(FINAL_AUTHORITY)
    output = "\n".join(sections).rstrip() + "\n"
    if "@import" in output:
        raise RuntimeError("rist.css still contains @import")
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT} from {len(SOURCES)} archived sources")

if __name__ == "__main__":
    main()
