from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "wwwroot" / "css" / "rist.css"

AUTHORITY = r'''

/* RIST ASSET DROP PROMPTS: prompts belong to their sliders, never the map. */
.release-world .public-assets-items::after,
.release-world .private-assets-items::after{
 box-sizing:border-box!important;
 flex:0 0 auto!important;
 align-self:center!important;
 display:grid!important;
 place-items:center!important;
 height:36px!important;
 min-height:36px!important;
 margin:0 4px!important;
 padding:0 12px!important;
 border:1px dashed #5d5137!important;
 border-radius:6px!important;
 background:#0a1116!important;
 color:#95896d!important;
 font:700 8px/1 system-ui,-apple-system,sans-serif!important;
 letter-spacing:.04em!important;
 white-space:nowrap!important;
 pointer-events:none!important;
}
.release-world .public-assets-items::after{content:"Drag public assets here"!important}
.release-world .private-assets-items::after{content:"Drag private assets here"!important}
.release-world .rail-drop-prompt{display:none!important}
'''

text = CSS.read_text(encoding="utf-8")
marker = "/* RIST ASSET DROP PROMPTS"
if marker in text:
    text = text[:text.index(marker)].rstrip() + "\n"
CSS.write_text(text.rstrip() + "\n" + AUTHORITY.strip() + "\n", encoding="utf-8")
print("Applied RIST asset drop prompts")
