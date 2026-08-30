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
/* RIST FINAL VISUAL AUTHORITY                                                 */
/* ========================================================================== */

/* The containing row owns size. Artwork never resizes a control. */
.rist .header-circular-set > .header-icon-button,
.rist .header-circular-set > .control {
  box-sizing:border-box!important;
  flex:0 0 96px!important;
  width:96px!important;
  min-width:96px!important;
  max-width:96px!important;
  height:48px!important;
  min-height:48px!important;
  max-height:48px!important;
  margin:0!important;
  overflow:hidden!important;
}
.rist .header-circular-set > .header-icon-button {
  display:grid!important;
  place-items:center!important;
  padding:4px!important;
  border:1px solid #725d30!important;
  border-radius:10px!important;
  background:#111920!important;
}
.rist .header-circular-set .header-icon {
  width:38px!important;
  height:38px!important;
  max-width:38px!important;
  max-height:38px!important;
  margin:auto!important;
  background-size:contain!important;
  background-position:center!important;
  background-repeat:no-repeat!important;
  pointer-events:none!important;
}

/* MMO toggle uses AWS artwork as the background, avoiding broken-image glyphs. */
.rist .header-mmo-button .mmo-toggle-art {
  display:block!important;
  width:100%!important;
  height:100%!important;
  background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/sandbox-toggle.webp?v=20260830-rail-2")!important;
  background-position:center!important;
  background-repeat:no-repeat!important;
  background-size:contain!important;
}
.rist .header-mmo-button.mmo-art-active .mmo-toggle-art {
  background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/mmo-toggle.webp?v=20260830-rail-2")!important;
}
.rist .header-mmo-button .mmo-toggle-art > img {display:none!important}

/* Public/private rail buttons fit the ~52px artwork row instead of overflowing it. */
.rist .public-assets-items > button,
.rist .private-assets-items > button,
.rist .private-assets-items .compact-hand-card,
.rist .private-assets-items .standard-hand-card,
.rist .private-assets-items .hand-card-wrap {
  box-sizing:border-box!important;
  flex:0 0 54px!important;
  width:54px!important;
  min-width:54px!important;
  max-width:54px!important;
}
.rist .public-assets-items .public-asset-card,
.rist .private-assets-items .compact-hand-card,
.rist .private-assets-items .standard-hand-card {
  height:44px!important;
  min-height:44px!important;
  max-height:44px!important;
  padding:3px!important;
  display:grid!important;
  place-items:center!important;
  overflow:hidden!important;
  border:1px solid #725d30!important;
  border-radius:8px!important;
  background:#111920!important;
}
.rist .public-assets-items .public-asset-card > img,
.rist .private-assets-items .compact-hand-card > img,
.rist .private-assets-items .standard-hand-card > img {
  display:block!important;
  width:100%!important;
  height:100%!important;
  max-width:100%!important;
  max-height:100%!important;
  object-fit:contain!important;
  object-position:center!important;
  margin:0!important;
}

/* Map pin has the same framed-button grammar in both rails. */
.rist .public-assets-rail .token-pin-source,
.rist .private-assets-rail .token-pin-source {
  box-sizing:border-box!important;
  flex:0 0 54px!important;
  width:54px!important;
  min-width:54px!important;
  max-width:54px!important;
  height:44px!important;
  min-height:44px!important;
  max-height:44px!important;
  display:grid!important;
  place-items:center!important;
  padding:4px!important;
  overflow:hidden!important;
  border:1px solid #725d30!important;
  border-radius:8px!important;
  background:#111920!important;
  box-shadow:none!important;
}
.rist .public-assets-rail .map-pin-icon,
.rist .private-assets-rail .map-pin-icon {
  display:block!important;
  width:28px!important;
  height:36px!important;
  min-width:28px!important;
  min-height:36px!important;
  max-width:28px!important;
  max-height:36px!important;
  margin:auto!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  transform:none!important;
  background-color:transparent!important;
  background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/map-pin.svg?v=20260830-rail-2")!important;
  background-position:center!important;
  background-repeat:no-repeat!important;
  background-size:contain!important;
  pointer-events:none!important;
}
.rist .map-pin-icon::before,.rist .map-pin-icon::after{content:none!important}
.rist .piece.pin{background:transparent!important;border:0!important;box-shadow:none!important}
.rist .piece.pin::after{content:none!important}

/* Elemental coin selector also stays inside the asset row. */
.rist .elemental-token-selector{height:44px!important;display:flex!important;align-items:center!important}
.rist .elemental-token-active{width:54px!important;height:44px!important;min-width:54px!important;min-height:44px!important;padding:3px!important}
.rist .elemental-token-active .magic-coin-sprite{width:38px!important;height:38px!important}

/* Copyright gets a real readable row instead of a clipped 10px sliver. */
:root{
  --rist-legal-h:16px!important;
  --rist-footer-h:138px!important;
}
.rist .home-footer-stack{
  grid-template-rows:var(--rist-dice-h) var(--rist-chat-h) var(--rist-legal-h)!important;
  height:var(--rist-footer-h)!important;
  min-height:var(--rist-footer-h)!important;
  max-height:var(--rist-footer-h)!important;
}
.rist .site-copyright-notice{
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  height:var(--rist-legal-h)!important;
  min-height:var(--rist-legal-h)!important;
  padding:0 8px!important;
  color:#d2b873!important;
  background:#071118!important;
  border-top:1px solid #4d4023!important;
  font:600 8px/1 system-ui,-apple-system,sans-serif!important;
  letter-spacing:.025em!important;
  opacity:1!important;
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
}

@media(orientation:landscape){
  :root{--rist-footer-h:70px!important}
  .rist .home-footer-stack{height:70px!important;min-height:70px!important;max-height:70px!important;grid-template-rows:54px 16px!important}
  .rist .site-copyright-notice{height:16px!important;min-height:16px!important}
}

/* Deliberate sprite/crop systems retain their own math. */
.rist .tile-image-crop > img,.rist .die-sprite,.rist .mixer-sprite,.rist .sprite-sheet,.rist [class*="sprite-"]{max-width:none}
'''


def main() -> None:
    sections = [
        "/* AUTO-GENERATED by apps/rist-world/prepare_css.py. */",
        "/* rist.css is the only runtime stylesheet. */",
    ]
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
