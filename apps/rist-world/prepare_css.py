from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS_DIR = ROOT / "wwwroot" / "css"
OUTPUT = CSS_DIR / "rist.css"

# This order is the former browser cascade order. Keeping it here makes the
# migration deterministic while rist.css becomes the only active stylesheet.
SOURCES = [
    "app.css",
    "adaptive-grid.css",
    "spatial-surface.css",
    "hand-rail.css",
    "dice-geometry.css",
    "tabletop-dials-mobile.css",
    "character-console.css",
    "physical-controls-refinement.css",
    "character-card-pass.css",
    "tracks-pass.css",
    "character-families.css",
    "interaction-fixes.css",
    "shaelvien-cards.css",
    "intuitive-card-editor.css",
    "footer-uniform.css",
    "rail-final.css",
    "library-rails.css",
    "mobile-horizontal-rails.css",
    "character-native.css",
    "character-profile-alignment.css",
    "character-profile-tiles.css",
    "shaelvien-cursors.css",
    "info-legal.css",
    "grid-coordinate-system.css",
    "map-packets.css",
    "map-context-sidebar.css",
    "portrait-profile-geometry.css",
    "recursion-cockpit.css",
    "start-menu.css",
    "mmo-mode.css",
    "prelogin-visitor.css",
    "rist-tutorial.css",
    "discord-login.css",
    "mobile-history-fixes.css",
    "calforth-token-lite.css",
    "token-rail-visuals.css",
    "faux-depth.css",
    "home-viewport.css",
]

# button-artwork-fit.css is intentionally NOT included. It resized buttons from
# image intrinsic dimensions and is the cascade that caused slider controls to
# collapse/disappear.

IMPORT_RE = re.compile(r"@import\s+url\((?:['\"])?([^)'\"]+)(?:['\"])?\)\s*;", re.I)


def archived(name: str) -> Path:
    return CSS_DIR / f"{name}.old"


def inline_imports(text: str, stack: tuple[str, ...]) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        if raw.startswith(("http://", "https://", "data:")):
            raise RuntimeError(f"External CSS import is not allowed in unified rist.css: {raw}")
        name = raw.split("?", 1)[0].lstrip("./")
        if name in stack:
            raise RuntimeError(f"CSS import cycle: {' -> '.join(stack + (name,))}")
        path = archived(name)
        if not path.exists():
            raise FileNotFoundError(f"Missing archived CSS import: {path}")
        imported = inline_imports(path.read_text(encoding="utf-8"), stack + (name,))
        return f"\n/* ===== inlined import: {name}.old ===== */\n{imported}\n/* ===== end import: {name}.old ===== */\n"

    return IMPORT_RE.sub(replace, text)


CONTROL_CONTRACT = r'''

/* ========================================================================== */
/* RIST CONTROL CONTRACT — final authority                                     */
/* ========================================================================== */
/* Frames own geometry. Artwork never determines button width or height. */
.rist .header-circular-set > .header-icon-button,
.rist .header-circular-set > .control,
.rist .private-assets-items > button,
.rist .private-assets-items .compact-hand-card,
.rist .private-assets-items .standard-hand-card,
.rist .asset-category-button,
.rist .asset-folder-button,
.rist .asset-item-button {
  box-sizing:border-box!important;
  flex-shrink:0!important;
}

/* Header slider: one stable frame size; content is centered inside it. */
.rist .header-circular-set > .header-icon-button,
.rist .header-circular-set > .control {
  flex:0 0 96px!important;
  width:96px!important;
  min-width:96px!important;
  max-width:96px!important;
  height:58px!important;
  min-height:58px!important;
  max-height:58px!important;
  margin:0!important;
  overflow:hidden!important;
}
.rist .header-circular-set > .header-icon-button {
  display:grid!important;
  place-items:center!important;
  padding:5px!important;
  border:1px solid #725d30!important;
  border-radius:10px!important;
  background:#111920!important;
}
.rist .header-circular-set > .header-icon-button > .header-icon,
.rist .header-circular-set > .control > .header-icon {
  margin:auto!important;
  pointer-events:none!important;
}

/* MMO artwork follows the frame instead of resizing it. */
.rist .header-mmo-button .mmo-toggle-art {
  width:100%!important;
  height:100%!important;
  min-width:0!important;
  min-height:0!important;
  display:grid!important;
  place-items:center!important;
  overflow:hidden!important;
  background:transparent!important;
}
.rist .header-mmo-button .mmo-toggle-art > img {
  display:block!important;
  width:100%!important;
  height:100%!important;
  max-width:100%!important;
  max-height:100%!important;
  object-fit:contain!important;
  object-position:center!important;
  margin:0!important;
}
.rist .header-mmo-button .mmo-art-mmo{display:none!important}
.rist .header-mmo-button.mmo-art-active .mmo-art-sandbox{display:none!important}
.rist .header-mmo-button.mmo-art-active .mmo-art-mmo{display:block!important}

/* Private cards: wider portrait frames, full art visible. */
.rist .private-assets-items .hand-card-wrap {
  flex:0 0 60px!important;
  width:60px!important;
  min-width:60px!important;
  max-width:60px!important;
}
.rist .private-assets-items .compact-hand-card,
.rist .private-assets-items .standard-hand-card {
  flex:0 0 60px!important;
  width:60px!important;
  min-width:60px!important;
  max-width:60px!important;
  height:64px!important;
  min-height:64px!important;
  max-height:64px!important;
  padding:4px!important;
  overflow:hidden!important;
  border:1px solid #725d30!important;
  border-radius:9px!important;
  background:#111920!important;
}
.rist .private-assets-items .compact-hand-card > img,
.rist .private-assets-items .standard-hand-card > img {
  display:block!important;
  width:100%!important;
  height:100%!important;
  min-width:0!important;
  min-height:0!important;
  max-width:100%!important;
  max-height:100%!important;
  object-fit:contain!important;
  object-position:center!important;
  margin:0!important;
}

/* Map pin: transparent artwork, themed frame, no white/circular spill. */
.rist .private-assets-rail .token-pin-source {
  box-sizing:border-box!important;
  flex:0 0 60px!important;
  width:60px!important;
  min-width:60px!important;
  max-width:60px!important;
  height:64px!important;
  min-height:64px!important;
  max-height:64px!important;
  display:grid!important;
  place-items:center!important;
  padding:7px!important;
  overflow:hidden!important;
  border:1px solid #725d30!important;
  border-radius:9px!important;
  background:transparent!important;
  box-shadow:none!important;
}
.rist .private-assets-rail .token-pin-source .map-pin-icon {
  display:block!important;
  width:34px!important;
  height:44px!important;
  min-width:34px!important;
  min-height:44px!important;
  max-width:34px!important;
  max-height:44px!important;
  margin:auto!important;
  border:0!important;
  border-radius:0!important;
  box-shadow:none!important;
  transform:none!important;
  background-color:transparent!important;
  background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/map-pin.svg?v=20260830-unified-css-1")!important;
  background-position:center!important;
  background-repeat:no-repeat!important;
  background-size:contain!important;
  pointer-events:none!important;
}
.rist .private-assets-rail .token-pin-source .map-pin-icon::before,
.rist .private-assets-rail .token-pin-source .map-pin-icon::after {content:none!important}
.rist .piece.pin {
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.rist .piece.pin::after {content:none!important}

/* Sprite/crop renderers are deliberate exceptions and retain their own math. */
.rist .tile-image-crop > img,
.rist .die-sprite,
.rist .mixer-sprite,
.rist .sprite-sheet,
.rist [class*="sprite-"] {max-width:none}
'''


def main() -> None:
    sections: list[str] = [
        "/* AUTO-GENERATED by apps/rist-world/prepare_css.py. */",
        "/* Edit source archives only during migration; rist.css is the sole runtime stylesheet. */",
    ]
    for name in SOURCES:
        path = archived(name)
        if not path.exists():
            raise FileNotFoundError(f"Missing archived CSS source: {path}")
        body = inline_imports(path.read_text(encoding="utf-8"), (name,))
        sections.append(f"\n/* ========================================================================== */\n/* SOURCE: {name}.old */\n/* ========================================================================== */\n{body}")
    sections.append(CONTROL_CONTRACT)
    output = "\n".join(sections).rstrip() + "\n"
    if "@import" in output:
        raise RuntimeError("rist.css still contains @import; runtime must load one CSS file only")
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT} from {len(SOURCES)} archived sources")


if __name__ == "__main__":
    main()
