from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "wwwroot" / "css" / "rist.css"

AUTHORITY = r'''

/* ========================================================================== */
/* RIST MAP VIEWER AUTHORITY                                                   */
/* The recursive map is the bounded viewer for every open workspace/menu.      */
/* ========================================================================== */
.release-world .map-viewer-region{position:relative!important;isolation:isolate!important;overflow:hidden!important}
.release-world .map-viewer-region>.table-workspace{position:absolute!important;inset:0!important;z-index:1!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;overflow:hidden!important}
.release-world .map-viewer-overlays{box-sizing:border-box!important;position:absolute!important;inset:0!important;z-index:200!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;overflow:hidden!important;pointer-events:none!important}

.release-world .map-viewer-region .card-browser,
.release-world .map-viewer-overlays>.asset-slider-stack,
.release-world .map-viewer-overlays>.native-character-modal,
.release-world .map-viewer-overlays>.rist-tutorial-shell,
.release-world .map-viewer-overlays>.map-account-viewer{
 box-sizing:border-box!important;position:absolute!important;inset:6px!important;z-index:230!important;width:auto!important;height:auto!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;margin:0!important;overflow:hidden!important;border-radius:10px!important;pointer-events:auto!important
}
.release-world .map-viewer-region .card-browser,
.release-world .map-viewer-overlays>.asset-slider-stack,
.release-world .map-viewer-overlays>.rist-tutorial-shell,
.release-world .map-viewer-overlays>.map-account-viewer{background:#071017f8!important;border:1px solid var(--rw-border)!important;box-shadow:0 12px 34px #000c!important}

/* Account access uses the map as its viewer. Chat output occupies the lower area. */
.release-world .map-viewer-overlays>.map-account-viewer{display:grid!important;grid-template-rows:38px minmax(0,1fr)!important;padding:0!important}
.release-world .map-account-viewer>.map-viewer-header{box-sizing:border-box!important;position:relative!important;display:flex!important;align-items:center!important;min-height:38px!important;padding:0 46px 0 12px!important;border-bottom:1px solid var(--rw-border-soft)!important;background:#091116!important;color:var(--rw-gold)!important}
.release-world .map-account-body{box-sizing:border-box!important;display:grid!important;grid-template-rows:minmax(0,2fr) minmax(82px,1fr)!important;gap:7px!important;min-width:0!important;min-height:0!important;padding:7px!important;overflow:hidden!important}
.release-world .map-account-card,.release-world .map-chat-output{box-sizing:border-box!important;min-width:0!important;min-height:0!important;overflow:auto!important;border:1px solid #554829!important;border-radius:8px!important;background:#0b141a!important}
.release-world .map-account-card{padding:9px!important}
.release-world .map-auth-tabs{display:flex!important;gap:6px!important;margin:0 0 9px!important}
.release-world .map-auth-tabs button,.release-world .map-plan-picker button,.release-world .map-auth-form>button{min-height:34px!important;border:1px solid #5f4d29!important;border-radius:7px!important;background:#111b22!important;color:#ded3b4!important}
.release-world .map-auth-tabs button.active,.release-world .map-plan-picker button.selected{border-color:#d2aa51!important;background:#20313a!important;color:#ffe8aa!important}
.release-world .map-auth-form{display:grid!important;gap:8px!important;max-width:640px!important;margin:0 auto!important}
.release-world .map-auth-form h2{margin:0!important;color:var(--rw-gold)!important;font-size:17px!important}
.release-world .map-auth-form label{display:grid!important;gap:4px!important;color:#c9bb97!important;font-size:10px!important}
.release-world .map-auth-form input:not([type="checkbox"]){box-sizing:border-box!important;width:100%!important;min-height:34px!important;border:1px solid #554829!important;border-radius:6px!important;background:#071017!important;color:#fff3d0!important;padding:6px 8px!important}
.release-world .map-plan-picker{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important;margin:0!important;padding:7px!important;border:1px solid #3f3726!important;border-radius:7px!important}
.release-world .map-plan-picker legend{padding:0 4px!important;color:#c9bb97!important;font-size:9px!important}
.release-world .map-plan-picker button{display:grid!important;gap:2px!important;padding:6px!important;text-align:left!important}
.release-world .map-plan-picker span{font-size:9px!important;color:#a99c7b!important}
.release-world .map-terms{grid-template-columns:auto minmax(0,1fr)!important;align-items:start!important}
.release-world .map-chat-output{display:grid!important;grid-template-rows:auto minmax(0,1fr)!important}
.release-world .map-chat-output>header{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:7px!important;padding:4px 7px!important;border-bottom:1px solid #3f3726!important}
.release-world .map-chat-slide{overflow:auto!important;padding:6px 8px!important}
.release-world .map-chat-slide article p{margin:3px 0 0!important}
.release-world .map-chat-empty{margin:0!important;color:#817866!important;font-size:9px!important}
.release-world .chat-playback-controls{display:flex!important;align-items:center!important;gap:4px!important}
.release-world .chat-playback-controls button,.release-world .chat-playback-controls select{height:25px!important;min-height:25px!important;border:1px solid #514426!important;border-radius:5px!important;background:#0e181e!important;color:#d7c9a6!important;font-size:8px!important}
.release-world .chat-playback-controls label{display:flex!important;align-items:center!important;gap:4px!important;color:#998e74!important;font-size:8px!important}

/* Character sheet and libraries consume the same map viewer and scroll internally. */
.release-world .map-viewer-overlays>.native-character-modal{display:grid!important;place-items:stretch!important;padding:0!important;background:#03070ac7!important}
.release-world .map-viewer-overlays .native-character-sheet{box-sizing:border-box!important;position:relative!important;inset:auto!important;width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important;min-width:0!important;min-height:0!important;margin:0!important;overflow:auto!important}
.release-world .map-viewer-region .card-browser{display:grid!important;grid-template-rows:auto minmax(0,1fr)!important}
.release-world .map-viewer-region .card-library-workspace,.release-world .map-viewer-region .card-library-results,.release-world .map-viewer-overlays .asset-slider-stack,.release-world .map-viewer-overlays .asset-horizontal-rail{min-width:0!important;min-height:0!important;max-width:100%!important;max-height:100%!important}
.release-world .map-viewer-region .card-library-workspace,.release-world .map-viewer-region .card-library-results{overflow:auto!important}
.release-world .map-viewer-overlays>.asset-slider-stack{display:grid!important;grid-template-rows:auto minmax(0,1fr)!important}

/* Root menus also occupy exactly the map rectangle. */
.release-world .root-menu-panel,.release-world .release-action-menu{box-sizing:border-box!important;position:fixed!important;z-index:950!important;top:calc(var(--rw-context) + var(--rw-menu) + var(--rw-public) + 6px)!important;right:6px!important;bottom:calc(var(--rw-private) + var(--rw-footer) + 6px)!important;left:6px!important;width:auto!important;height:auto!important;max-width:none!important;max-height:none!important;margin:0!important;overflow:auto!important;padding:44px 12px 12px!important;border:1px solid var(--rw-border)!important;border-radius:10px!important;background:#071017f8!important;box-shadow:0 12px 34px #000c!important;backdrop-filter:blur(7px)!important}

.release-world .map-viewer-overlays>.recursion-cockpit{box-sizing:border-box!important;position:absolute!important;z-index:210!important;top:8px!important;right:8px!important;left:auto!important;bottom:auto!important;max-width:min(360px,calc(100% - 16px))!important;max-height:calc(100% - 16px)!important;overflow:auto!important;pointer-events:auto!important}
.release-world .map-viewer-overlays>.mmo-zone-actions:not([hidden]){box-sizing:border-box!important;position:absolute!important;z-index:220!important;inset:8px!important;overflow:auto!important;pointer-events:auto!important}

/* Every map viewer owns its close button. */
.map-viewer-close,.root-panel-close{box-sizing:border-box!important;position:absolute!important;z-index:1200!important;top:7px!important;right:7px!important;width:32px!important;height:32px!important;min-width:32px!important;min-height:32px!important;display:grid!important;place-items:center!important;margin:0!important;padding:0!important;border:1px solid #9b7c36!important;border-radius:8px!important;background:#0b1319f5!important;color:#f0d58f!important;font:900 22px/28px system-ui,-apple-system,sans-serif!important;box-shadow:0 3px 10px #0009!important;cursor:pointer!important;pointer-events:auto!important}
.map-viewer-close:active,.root-panel-close:active{background:#24313a!important;color:#fff4cf!important}
.release-world .root-menu-panel>.root-panel-close,.release-world .release-action-menu>.root-panel-close{position:fixed!important;top:calc(var(--rw-context) + var(--rw-menu) + var(--rw-public) + 13px)!important;right:13px!important}

/* Login is discoverable before interaction. */
.release-world.auth-visitor .door-button.login-pulse{animation:rist-login-glow 1.7s ease-in-out infinite!important;border-color:#d7be80!important}
@keyframes rist-login-glow{0%,100%{box-shadow:inset 0 0 0 1px #0007,0 0 3px #d7be8055}50%{box-shadow:inset 0 0 0 1px #d7be8088,0 0 14px #f0d58fcc,0 0 24px #d7be8066}}
@media (prefers-reduced-motion:reduce){.release-world.auth-visitor .door-button.login-pulse{animation:none!important;box-shadow:inset 0 0 0 1px #d7be8088,0 0 10px #d7be8088!important}}

/* Natural gestures need no instructional status strip. */
.release-world .map .status{display:none!important}

@media (max-height:600px) and (orientation:landscape){
 .release-world .root-menu-panel,.release-world .release-action-menu{padding-top:38px!important}
 .map-viewer-close,.root-panel-close{width:28px!important;height:28px!important;min-width:28px!important;min-height:28px!important;font-size:19px!important}
 .release-world .map-account-body{grid-template-rows:minmax(0,2.2fr) minmax(70px,.8fr)!important;gap:5px!important;padding:5px!important}
 .release-world .map-auth-form{gap:5px!important}
 .release-world .map-plan-picker{padding:4px!important}
}
'''

text = CSS.read_text(encoding="utf-8")
marker = "/* RIST MAP VIEWER AUTHORITY"
if marker in text:
    text = text[:text.index(marker)].rstrip() + "\n"
CSS.write_text(text.rstrip() + "\n" + AUTHORITY.strip() + "\n", encoding="utf-8")
print("Applied RIST map viewer authority")
