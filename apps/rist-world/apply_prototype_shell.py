from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "wwwroot" / "css" / "rist.css"

AUTHORITY = r'''

/* ========================================================================== */
/* RIST PROTOTYPE SHELL AUTHORITY — generated after the legacy compatibility  */
/* bundle. WORLD is the canonical single-screen shell.                        */
/* ========================================================================== */
:root{
 --proto-context:28px;
 --proto-header:56px;
 --proto-public:72px;
 --proto-private:72px;
 --proto-footer:118px;
 --proto-bg:#080d11;
 --proto-panel:#0d151b;
 --proto-panel-2:#111b22;
 --proto-edge:#725d30;
 --proto-edge-soft:#40371f;
 --proto-gold:#d7be80;
 --proto-text:#eee6d3;
 --proto-muted:#938a78;
}
html,body,#app{width:100%;height:100%;margin:0;overflow:hidden;background:var(--proto-bg);color:var(--proto-text)}
body{overscroll-behavior:none;touch-action:manipulation}

.world-context-strip{
 box-sizing:border-box!important;height:var(--proto-context)!important;min-height:var(--proto-context)!important;
 display:flex!important;align-items:center!important;gap:3px!important;padding:2px max(5px,env(safe-area-inset-left))!important;
 overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;
 background:#070c10!important;border-bottom:1px solid var(--proto-edge-soft)!important;
}
.world-context-strip::-webkit-scrollbar{display:none!important}
.world-context-strip>*{flex:0 0 auto!important;height:22px!important;box-sizing:border-box!important;margin:0!important;padding:0 7px!important;border:1px solid #3c3525!important;border-radius:6px!important;background:#0d151b!important;color:#cfc2a0!important;font:700 9px/20px system-ui!important;white-space:nowrap!important}
.world-context-strip strong{color:var(--proto-gold)!important}

.rist.prototype-shell{
 position:relative!important;box-sizing:border-box!important;width:100%!important;height:calc(100dvh - var(--proto-context))!important;
 min-height:0!important;overflow:hidden!important;background:var(--proto-bg)!important;
}
.rist.prototype-shell>.rist-primary-shell{
 position:relative!important;z-index:1!important;box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;
 display:grid!important;grid-template-rows:var(--proto-header) var(--proto-public) minmax(0,1fr) var(--proto-private) var(--proto-footer)!important;
 grid-template-columns:minmax(0,1fr)!important;overflow:hidden!important;
}
.rist-primary-shell>#header-slider{grid-row:1!important}
.rist-primary-shell>.public-assets-rail{grid-row:2!important}
.rist-primary-shell>.table-workspace{grid-row:3!important}
.rist-primary-shell>.private-assets-rail{grid-row:4!important}
.rist-primary-shell>.home-footer-stack{grid-row:5!important}
.rist-primary-shell>*{min-width:0!important;min-height:0!important}

/* Main menu: one finite viewport, real inner scrolling, arrows always usable. */
.rist.prototype-shell #header-slider{
 position:relative!important;box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;
 display:grid!important;grid-template-columns:30px minmax(0,1fr) 30px!important;align-items:stretch!important;
 overflow:hidden!important;padding:0!important;border:0!important;border-bottom:1px solid var(--proto-edge)!important;background:var(--proto-panel)!important;
}
.rist.prototype-shell #header-slider>.rail-scroll-arrow{display:grid!important;place-items:center!important;position:relative!important;inset:auto!important;width:30px!important;height:100%!important;z-index:8!important;padding:0!important;margin:0!important;border:0!important;border-radius:0!important;background:#0a1117!important;color:var(--proto-gold)!important;font:700 24px/1 system-ui!important}
.rist.prototype-shell #header-slider>.rail-scroll-prev{grid-column:1!important}.rist.prototype-shell #header-slider>.header-circular-set{grid-column:2!important}.rist.prototype-shell #header-slider>.rail-scroll-next{grid-column:3!important}
.rist.prototype-shell #header-slider .header-circular-set{
 box-sizing:border-box!important;min-width:0!important;width:auto!important;max-width:none!important;height:100%!important;display:flex!important;flex-wrap:nowrap!important;align-items:center!important;gap:6px!important;
 padding:4px 6px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;scroll-snap-type:x proximity!important;touch-action:pan-x!important;overscroll-behavior-x:contain!important;
}
.rist.prototype-shell #header-slider .header-circular-set::-webkit-scrollbar{display:none!important}
.rist.prototype-shell #header-slider .header-circular-set>*{flex-shrink:0!important;scroll-snap-align:start!important}
.rist.prototype-shell #header-slider .header-icon-button,.rist.prototype-shell #header-slider .control,.rist.prototype-shell #header-slider .scale-stack{
 flex:0 0 74px!important;width:74px!important;min-width:74px!important;max-width:74px!important;height:44px!important;min-height:44px!important;max-height:44px!important;
 border:1px solid var(--proto-edge)!important;border-radius:8px!important;background:var(--proto-panel-2)!important;box-shadow:inset 0 0 0 1px #0008!important;
}
.rist.prototype-shell #header-slider .header-icon{width:30px!important;height:30px!important;min-width:30px!important;min-height:30px!important}
.rist.prototype-shell #header-slider .header-info-button,.rist.prototype-shell #header-slider .header-settings-button{color:var(--proto-gold)!important;font-size:22px!important;text-decoration:none!important}

/* Public/private asset rows use the same physical grammar and slider behavior. */
.rist.prototype-shell .public-assets-rail,.rist.prototype-shell .private-assets-rail{
 box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;
 display:grid!important;grid-template-rows:26px minmax(0,1fr)!important;overflow:hidden!important;
 background:var(--proto-panel)!important;border:0!important;
}
.rist.prototype-shell .public-assets-rail{border-bottom:1px solid var(--proto-edge-soft)!important}
.rist.prototype-shell .private-assets-rail{border-top:1px solid var(--proto-edge-soft)!important}
.rist.prototype-shell .asset-rail-header{height:26px!important;min-height:26px!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;gap:7px!important;padding:2px 6px!important;overflow:hidden!important;border:0!important;border-bottom:1px solid #2c291f!important;background:#0a1116!important}
.rist.prototype-shell .asset-rail-header>strong{font:800 9px/1 system-ui!important;letter-spacing:.11em!important;color:var(--proto-gold)!important;white-space:nowrap!important}
.rist.prototype-shell .asset-type-tabs{min-width:0!important;height:22px!important;display:flex!important;align-items:center!important;gap:3px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important}
.rist.prototype-shell .asset-type-tabs::-webkit-scrollbar{display:none!important}
.rist.prototype-shell .asset-type-tabs button{height:20px!important;min-height:20px!important;padding:0 8px!important;border-radius:6px!important;font:700 8px/18px system-ui!important;white-space:nowrap!important}
.rist.prototype-shell .public-assets-strip,.rist.prototype-shell .private-assets-strip{
 box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;
 display:grid!important;grid-template-columns:28px minmax(0,1fr) 28px!important;align-items:stretch!important;overflow:hidden!important;
}
.rist.prototype-shell .public-assets-strip>.rail-scroll-arrow,.rist.prototype-shell .private-assets-strip>.rail-scroll-arrow{
 display:grid!important;place-items:center!important;position:relative!important;inset:auto!important;width:28px!important;height:100%!important;z-index:8!important;padding:0!important;margin:0!important;border:0!important;border-radius:0!important;background:#0a1117!important;color:var(--proto-gold)!important;font:700 22px/1 system-ui!important;
}
.rist.prototype-shell .public-assets-items,.rist.prototype-shell .private-assets-items{
 grid-column:2!important;box-sizing:border-box!important;min-width:0!important;width:auto!important;max-width:none!important;height:100%!important;
 display:flex!important;flex-wrap:nowrap!important;align-items:center!important;gap:6px!important;padding:3px 6px!important;
 overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;touch-action:pan-x!important;overscroll-behavior-x:contain!important;scroll-snap-type:x proximity!important;
}
.rist.prototype-shell .public-assets-items::-webkit-scrollbar,.rist.prototype-shell .private-assets-items::-webkit-scrollbar{display:none!important}
.rist.prototype-shell .public-assets-items>* ,.rist.prototype-shell .private-assets-items>*{flex-shrink:0!important;scroll-snap-align:start!important}
.rist.prototype-shell .public-assets-items>button,.rist.prototype-shell .private-assets-items>button,.rist.prototype-shell .private-assets-items .hand-card-wrap{flex-basis:54px!important;width:54px!important;min-width:54px!important;max-width:54px!important}
.rist.prototype-shell .public-assets-items .public-asset-card,.rist.prototype-shell .private-assets-items .compact-hand-card,.rist.prototype-shell .private-assets-items .standard-hand-card,.rist.prototype-shell .public-assets-rail .token-pin-source,.rist.prototype-shell .private-assets-rail .token-pin-source{height:40px!important;min-height:40px!important;max-height:40px!important;border-radius:7px!important}
.rist.prototype-shell .public-assets-rail .map-pin-icon,.rist.prototype-shell .private-assets-rail .map-pin-icon{width:27px!important;height:33px!important;min-width:27px!important;min-height:33px!important}

/* The map is the dominant workspace. It alone absorbs remaining viewport size. */
.rist.prototype-shell .table-workspace{position:relative!important;box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;overflow:hidden!important;background:#0b151a!important}
.rist.prototype-shell .table-workspace>.map-shell{position:absolute!important;inset:0!important;box-sizing:border-box!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important}
.rist.prototype-shell .table-workspace .map{width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;margin:0!important;border:0!important;border-radius:0!important;box-shadow:none!important}
.rist.prototype-shell .table-workspace>.staging-tray{position:absolute!important;z-index:35!important;left:8px!important;right:8px!important;top:8px!important;width:auto!important;max-width:none!important;height:46px!important;min-height:46px!important;display:flex!important;align-items:center!important;overflow:hidden!important;border:1px solid #725d3088!important;border-radius:9px!important;background:#071016dc!important;backdrop-filter:blur(4px)!important}
.rist.prototype-shell .table-workspace>.staging-tray .rail-scroll-arrow{height:100%!important}
.rist.prototype-shell .desktop-map-zoom{right:8px!important;bottom:8px!important;top:auto!important}

/* Footer is three rows from the WORLD prototype: character/dice, chat, legal. */
.rist.prototype-shell .home-footer-stack{
 box-sizing:border-box!important;width:100%!important;height:100%!important;min-height:0!important;display:grid!important;
 grid-template-rows:58px minmax(42px,1fr) 14px!important;overflow:hidden!important;background:#080f14!important;border-top:1px solid var(--proto-edge)!important;
}
.rist.prototype-shell #footer-slider{
 box-sizing:border-box!important;width:100%!important;height:58px!important;min-width:0!important;display:grid!important;grid-template-columns:30px minmax(0,1fr) 30px!important;overflow:hidden!important;border:0!important;background:var(--proto-panel)!important;
}
.rist.prototype-shell #footer-slider>.rail-scroll-arrow{display:grid!important;place-items:center!important;position:relative!important;inset:auto!important;width:30px!important;height:100%!important;padding:0!important;margin:0!important;border:0!important;border-radius:0!important;background:#0a1117!important;color:var(--proto-gold)!important;font:700 24px/1 system-ui!important}
.rist.prototype-shell #footer-slider>.dice-circular-set{grid-column:2!important;box-sizing:border-box!important;min-width:0!important;width:auto!important;max-width:none!important;height:100%!important;display:flex!important;flex-wrap:nowrap!important;align-items:center!important;gap:5px!important;padding:4px 6px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;touch-action:pan-x!important;overscroll-behavior-x:contain!important}
.rist.prototype-shell #footer-slider>.dice-circular-set::-webkit-scrollbar{display:none!important}
.rist.prototype-shell #footer-slider>.dice-circular-set>*{flex-shrink:0!important}
.rist.prototype-shell .footer-character-button{box-sizing:border-box!important;flex:0 0 86px!important;width:86px!important;height:48px!important;border:1px solid var(--proto-edge)!important;border-radius:8px!important;background:var(--proto-panel-2)!important;color:var(--proto-gold)!important;font:800 9px/1 system-ui!important;letter-spacing:.08em!important;text-transform:uppercase!important}
.rist.prototype-shell #footer-slider .die-button,.rist.prototype-shell #footer-slider .die-control,.rist.prototype-shell #footer-slider .sum,.rist.prototype-shell #footer-slider .clear-dice,.rist.prototype-shell #footer-slider .history-scroll-button{height:48px!important;min-height:48px!important;max-height:48px!important}
.rist.prototype-shell .home-inline-chat{box-sizing:border-box!important;min-height:0!important;height:100%!important;display:grid!important;grid-template-columns:38px minmax(0,1fr) 62px!important;gap:5px!important;align-items:center!important;padding:3px 6px!important;border:0!important;border-top:1px solid #2d291f!important;background:#0a1116!important}
.rist.prototype-shell .home-chat-compose{height:100%!important;min-height:0!important;display:grid!important;grid-template-columns:auto minmax(0,1fr)!important;align-items:center!important;gap:5px!important}
.rist.prototype-shell .home-chat-compose textarea{box-sizing:border-box!important;width:100%!important;height:34px!important;min-height:34px!important;max-height:34px!important;resize:none!important;overflow:auto!important;border:1px solid #4c4129!important;border-radius:7px!important;background:#071017!important;color:var(--proto-text)!important;padding:6px!important}
.rist.prototype-shell .site-copyright-notice{height:14px!important;min-height:14px!important;display:flex!important;align-items:center!important;justify-content:center!important;overflow:hidden!important;background:#05090c!important;color:#766f62!important;font:600 8px/1 system-ui!important;white-space:nowrap!important}

/* Overlay interfaces remain above the canonical shell and do not consume rows. */
.rist.prototype-shell>.asset-slider-stack,.rist.prototype-shell>.character-mixer,.rist.prototype-shell>.recursion-cockpit,.rist.prototype-shell>.mmo-zone-actions,.rist.prototype-shell>.rist-welcome-tutorial{z-index:120!important}

@media (max-height:540px) and (orientation:landscape){
 :root{--proto-context:22px;--proto-header:46px;--proto-public:54px;--proto-private:54px;--proto-footer:74px}
 .world-context-strip>*{height:18px!important;font-size:8px!important;line-height:16px!important}
 .rist.prototype-shell #header-slider .header-icon-button,.rist.prototype-shell #header-slider .control,.rist.prototype-shell #header-slider .scale-stack{height:38px!important;min-height:38px!important;max-height:38px!important;flex-basis:66px!important;width:66px!important;min-width:66px!important;max-width:66px!important}
 .rist.prototype-shell .public-assets-rail,.rist.prototype-shell .private-assets-rail{grid-template-rows:20px minmax(0,1fr)!important}
 .rist.prototype-shell .asset-rail-header{height:20px!important;min-height:20px!important;padding-block:0!important}
 .rist.prototype-shell .asset-type-tabs{height:18px!important}.rist.prototype-shell .asset-type-tabs button{height:17px!important;min-height:17px!important;line-height:15px!important}
 .rist.prototype-shell .public-assets-items .public-asset-card,.rist.prototype-shell .private-assets-items .compact-hand-card,.rist.prototype-shell .private-assets-items .standard-hand-card,.rist.prototype-shell .public-assets-rail .token-pin-source,.rist.prototype-shell .private-assets-rail .token-pin-source{height:30px!important;min-height:30px!important;max-height:30px!important}
 .rist.prototype-shell .home-footer-stack{grid-template-rows:42px 22px 10px!important}
 .rist.prototype-shell #footer-slider{height:42px!important}.rist.prototype-shell #footer-slider .die-button,.rist.prototype-shell #footer-slider .die-control,.rist.prototype-shell #footer-slider .sum,.rist.prototype-shell #footer-slider .clear-dice,.rist.prototype-shell #footer-slider .history-scroll-button,.rist.prototype-shell .footer-character-button{height:34px!important;min-height:34px!important;max-height:34px!important}
 .rist.prototype-shell .home-inline-chat{grid-template-columns:28px minmax(0,1fr) 48px!important;padding:1px 4px!important}.rist.prototype-shell .home-chat-compose textarea{height:19px!important;min-height:19px!important;max-height:19px!important;padding:2px 4px!important}.rist.prototype-shell .site-copyright-notice{height:10px!important;min-height:10px!important;font-size:7px!important}
 .rist.prototype-shell .table-workspace>.staging-tray{height:38px!important;min-height:38px!important;top:5px!important;left:5px!important;right:5px!important}
}
'''

text = CSS.read_text(encoding="utf-8")
marker = "/* RIST PROTOTYPE SHELL AUTHORITY"
if marker in text:
    text = text[:text.index(marker)].rstrip() + "\n"
CSS.write_text(text.rstrip() + AUTHORITY + "\n", encoding="utf-8")
