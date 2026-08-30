from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSS = ROOT / "wwwroot" / "css" / "rist.css"

AUTHORITY = r'''

/* ========================================================================== */
/* RIST RELEASE WORLD AUTHORITY                                                */
/* WORLD is a fixed recursive tabletop: context -> root menu -> public assets */
/* -> map -> private assets -> character/dice -> chat -> legal.                */
/* ========================================================================== */
:root{
 --rw-context:28px;
 --rw-menu:58px;
 --rw-public:66px;
 --rw-private:66px;
 --rw-footer:112px;
 --rw-dice:58px;
 --rw-chat:42px;
 --rw-legal:12px;
 --rw-bg:#070c10;
 --rw-panel:#0b1217;
 --rw-panel2:#111a20;
 --rw-border:#725d30;
 --rw-border-soft:#3d3423;
 --rw-gold:#d7be80;
 --rw-text:#eee6d3;
 --rw-muted:#918875;
}

html,body,#app{width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;margin:0!important;overflow:hidden!important;background:var(--rw-bg)!important;color:var(--rw-text)!important}
body{overscroll-behavior:none!important}

.world-context-strip{
 box-sizing:border-box!important;width:100%!important;height:var(--rw-context)!important;min-height:var(--rw-context)!important;max-height:var(--rw-context)!important;
 display:flex!important;align-items:center!important;gap:4px!important;padding:2px max(6px,env(safe-area-inset-left))!important;
 overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;white-space:nowrap!important;
 border:0!important;border-bottom:1px solid var(--rw-border-soft)!important;background:#060a0d!important;
}
.world-context-strip::-webkit-scrollbar{display:none!important}
.world-context-strip>*{box-sizing:border-box!important;flex:0 0 auto!important;height:22px!important;min-height:22px!important;margin:0!important;padding:0 8px!important;border:1px solid #504326!important;border-radius:7px!important;background:#0d151a!important;color:#c7b98f!important;font:700 9px/20px system-ui,-apple-system,sans-serif!important;white-space:nowrap!important}
.world-context-strip strong{color:var(--rw-gold)!important}

.rist.release-world{
 box-sizing:border-box!important;position:relative!important;width:100%!important;height:calc(100dvh - var(--rw-context))!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
 display:block!important;overflow:hidden!important;padding:0!important;margin:0!important;background:var(--rw-bg)!important;
}
.release-world-shell{
 box-sizing:border-box!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;
 display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:var(--rw-menu) var(--rw-public) minmax(0,1fr) var(--rw-private) var(--rw-footer)!important;
 gap:0!important;padding:0!important;margin:0!important;overflow:hidden!important;background:var(--rw-bg)!important;
}
.release-region{box-sizing:border-box!important;position:relative!important;inset:auto!important;width:100%!important;min-width:0!important;max-width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;margin:0!important;padding:0!important;overflow:hidden!important}
.release-menu-region{grid-row:1!important;z-index:80!important;overflow:visible!important;background:var(--rw-panel)!important}
.release-public-region{grid-row:2!important;z-index:20!important}
.release-map-region{grid-row:3!important;z-index:1!important;background:#071116!important}
.release-private-region{grid-row:4!important;z-index:20!important}
.release-footer-region{grid-row:5!important;z-index:30!important}
.release-region>*,.release-region>*>*{min-width:0!important}

/* Root rails: arrows live inside the border, never outside the page. */
.release-world .release-root-rail,
.release-world .public-assets-strip,
.release-world .private-assets-strip{
 box-sizing:border-box!important;position:relative!important;inset:auto!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:100%!important;
 display:grid!important;grid-template-columns:30px minmax(0,1fr) 30px!important;align-items:stretch!important;
 overflow:hidden!important;margin:0!important;padding:0!important;border:1px solid var(--rw-border)!important;border-radius:0!important;background:var(--rw-panel)!important;
}
.release-world .release-root-rail>.rail-scroll-arrow,
.release-world .public-assets-strip>.rail-scroll-arrow,
.release-world .private-assets-strip>.rail-scroll-arrow{
 box-sizing:border-box!important;display:grid!important;place-items:center!important;position:relative!important;inset:auto!important;z-index:12!important;width:30px!important;height:100%!important;min-width:30px!important;min-height:0!important;margin:0!important;padding:0!important;
 border:0!important;border-radius:0!important;background:#091015!important;color:var(--rw-gold)!important;font:800 24px/1 system-ui!important;opacity:1!important;filter:none!important;pointer-events:auto!important;
}
.release-world .release-root-rail>.rail-scroll-prev,.release-world .public-assets-strip>.rail-scroll-prev,.release-world .private-assets-strip>.rail-scroll-prev{grid-column:1!important;border-right:1px solid var(--rw-border-soft)!important}
.release-world .release-root-rail>.rail-scroll-next,.release-world .public-assets-strip>.rail-scroll-next,.release-world .private-assets-strip>.rail-scroll-next{grid-column:3!important;border-left:1px solid var(--rw-border-soft)!important}

.release-world .header-circular-set,
.release-world .public-assets-items,
.release-world .private-assets-items,
.release-world .dice-circular-set{
 box-sizing:border-box!important;grid-column:2!important;min-width:0!important;width:100%!important;max-width:100%!important;height:100%!important;min-height:0!important;
 display:flex!important;flex-wrap:nowrap!important;align-items:center!important;gap:6px!important;
 overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;-webkit-overflow-scrolling:touch!important;touch-action:pan-x!important;overscroll-behavior-x:contain!important;scroll-snap-type:x proximity!important;
}
.release-world .header-circular-set::-webkit-scrollbar,.release-world .public-assets-items::-webkit-scrollbar,.release-world .private-assets-items::-webkit-scrollbar,.release-world .dice-circular-set::-webkit-scrollbar{display:none!important}
.release-world .header-circular-set>* ,.release-world .public-assets-items>* ,.release-world .private-assets-items>* ,.release-world .dice-circular-set>*{flex-shrink:0!important;scroll-snap-align:start!important}

/* Main menu is a root browser, not a row of hidden selects. */
.release-world #header-slider{overflow:visible!important;border-width:0 0 1px!important}
.release-world .release-root-track{padding:4px 6px!important}
.release-world .root-menu-button{
 box-sizing:border-box!important;position:relative!important;flex:0 0 74px!important;width:74px!important;min-width:74px!important;max-width:74px!important;height:48px!important;min-height:48px!important;max-height:48px!important;
 display:grid!important;grid-template-rows:minmax(0,1fr) 12px!important;place-items:center!important;gap:0!important;margin:0!important;padding:2px!important;overflow:hidden!important;
 border:1px solid #5f4d29!important;border-radius:8px!important;background:var(--rw-panel2)!important;color:var(--rw-text)!important;text-decoration:none!important;box-shadow:inset 0 0 0 1px #0007!important;
}
.release-world .root-menu-button.active{border-color:#d2aa51!important;background:#17242c!important;box-shadow:inset 0 0 0 1px #d2aa5133!important}
.release-world .root-menu-button small{display:block!important;width:100%!important;overflow:hidden!important;color:#c6b88d!important;font:800 7px/10px system-ui!important;letter-spacing:.08em!important;text-align:center!important;text-transform:uppercase!important;text-overflow:ellipsis!important;white-space:nowrap!important}
.release-world .root-menu-art{display:block!important;width:30px!important;height:30px!important;background-position:center!important;background-repeat:no-repeat!important;background-size:contain!important;pointer-events:none!important}
.release-world .root-menu-button .icon-exit{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/door.svg?v=release-1")!important}
.release-world .root-menu-button .icon-encounter{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/mode.svg?v=release-1")!important}
.release-world .root-menu-button .icon-assets{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/assets.svg?v=release-1")!important}
.release-world .root-menu-button .icon-browse{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/browse.svg?v=release-1")!important}
.release-world .root-menu-button .icon-role{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/role.svg?v=release-1")!important}
.release-world .root-menu-button .icon-grid{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/grid.svg?v=release-1")!important}
.release-world .root-menu-button .icon-scale{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/scale.svg?v=release-1")!important}
.release-world .root-menu-button .icon-save{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/save.svg?v=release-1")!important}
.release-world .root-menu-button .icon-load{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/icons/load.svg?v=release-1")!important}
.release-world .root-menu-text strong{color:var(--rw-gold)!important;font:900 14px/1 system-ui!important}
.release-world .header-card-back{display:block!important;width:31px!important;height:31px!important;margin:0!important;background-position:center!important;background-repeat:no-repeat!important;background-size:contain!important}
.release-world .header-mmo-button .mmo-toggle-art{display:block!important;width:34px!important;height:31px!important;background:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/sandbox-toggle.webp?v=release-1") center/contain no-repeat!important}
.release-world .header-mmo-button.mmo-art-active .mmo-toggle-art{background-image:url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/mmo-toggle.webp?v=release-1")!important}

.release-world .root-menu-panel,.release-world .release-action-menu{
 box-sizing:border-box!important;position:absolute!important;z-index:500!important;left:31px!important;top:calc(100% + 4px)!important;width:min(520px,calc(100dvw - 62px))!important;max-height:min(55dvh,420px)!important;overflow:auto!important;
 display:grid!important;gap:8px!important;padding:10px!important;border:1px solid #9b7c36!important;border-radius:10px!important;background:#071017f2!important;color:var(--rw-text)!important;box-shadow:0 14px 38px #000d!important;backdrop-filter:blur(8px)!important;
}
.release-world .root-menu-panel>strong,.release-world .release-action-menu>strong{color:var(--rw-gold)!important;font:900 11px/1 system-ui!important;letter-spacing:.11em!important;text-transform:uppercase!important}
.release-world .root-choice-grid{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(100px,1fr))!important;gap:6px!important}
.release-world .root-choice-grid button,.release-world .release-action-menu button,.release-world .release-action-menu label,.release-world .release-action-menu a{
 box-sizing:border-box!important;min-height:36px!important;padding:7px 9px!important;border:1px solid #554829!important;border-radius:7px!important;background:#111b22!important;color:#ded3b4!important;font:700 10px/1.2 system-ui!important;text-decoration:none!important;text-align:center!important;
}
.release-world .root-choice-grid button.selected{border-color:#d2aa51!important;background:#20313a!important;color:#ffe8aa!important}
.release-world .scale-root-panel label{display:grid!important;grid-template-columns:auto minmax(90px,1fr)!important;align-items:center!important;gap:8px!important;color:#bfb18b!important;font:700 10px/1 system-ui!important}
.release-world .scale-root-panel input{box-sizing:border-box!important;width:100%!important;height:34px!important;border:1px solid #5c4d2a!important;border-radius:6px!important;background:#0d171d!important;color:#fff3d0!important;padding:4px 7px!important}
.release-world .scale-root-panel output{color:#d6c497!important;font:700 10px/1 system-ui!important}

/* Public/private rails are compact root shelves above/below the map. */
.release-world .release-public-region>.public-assets-rail,.release-world .release-private-region>.private-assets-rail{
 box-sizing:border-box!important;position:relative!important;inset:auto!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:100%!important;max-height:none!important;
 display:grid!important;grid-template-rows:24px minmax(0,1fr)!important;margin:0!important;padding:0!important;overflow:hidden!important;background:var(--rw-panel)!important;border:0!important;
}
.release-world .release-public-region>.public-assets-rail{border-bottom:1px solid var(--rw-border-soft)!important}
.release-world .release-private-region>.private-assets-rail{border-top:1px solid var(--rw-border-soft)!important}
.release-world .asset-rail-header{box-sizing:border-box!important;height:24px!important;min-height:24px!important;max-height:24px!important;display:flex!important;align-items:center!important;gap:6px!important;padding:2px 6px!important;overflow:hidden!important;border:0!important;border-bottom:1px solid #29251c!important;background:#080f13!important}
.release-world .asset-rail-header>strong{flex:0 0 auto!important;color:var(--rw-gold)!important;font:900 8px/1 system-ui!important;letter-spacing:.11em!important;text-transform:uppercase!important;white-space:nowrap!important}
.release-world .asset-type-tabs{min-width:0!important;height:20px!important;display:flex!important;align-items:center!important;gap:3px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important}
.release-world .asset-type-tabs::-webkit-scrollbar{display:none!important}
.release-world .asset-type-tabs button{box-sizing:border-box!important;flex:0 0 auto!important;height:19px!important;min-height:19px!important;margin:0!important;padding:0 7px!important;border:1px solid #463d28!important;border-radius:5px!important;background:#10181d!important;color:#9d947f!important;font:700 7px/17px system-ui!important;text-transform:uppercase!important;white-space:nowrap!important}
.release-world .asset-type-tabs button.active{border-color:#b58c34!important;color:#f0d58f!important;background:#172229!important}
.release-world .public-assets-strip,.release-world .private-assets-strip{border-width:0!important}
.release-world .public-assets-items,.release-world .private-assets-items{padding:3px 5px!important;gap:5px!important}
.release-world .public-assets-items>button,.release-world .private-assets-items>button,.release-world .private-assets-items .hand-card-wrap{flex-basis:50px!important;width:50px!important;min-width:50px!important;max-width:50px!important}
.release-world .public-assets-items .public-asset-card,.release-world .private-assets-items .compact-hand-card,.release-world .private-assets-items .standard-hand-card,.release-world .public-assets-rail .token-pin-source,.release-world .private-assets-rail .token-pin-source{box-sizing:border-box!important;height:36px!important;min-height:36px!important;max-height:36px!important;border-radius:6px!important}
.release-world .public-assets-rail .map-pin-icon,.release-world .private-assets-rail .map-pin-icon{width:24px!important;height:30px!important;min-width:24px!important;min-height:30px!important;background:transparent url("https://d2d6rnm6fnsp89.cloudfront.net/assets/ui/map-pin.svg?v=release-1") center/contain no-repeat!important}

/* Map owns every pixel left by fixed rails. Old page geometry cannot resize it. */
.release-world .release-map-region>.table-workspace{
 box-sizing:border-box!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
 display:block!important;margin:0!important;padding:0!important;overflow:hidden!important;background:#071116!important;
}
.release-world .release-map-region>.table-workspace>.map-shell{
 box-sizing:border-box!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
 display:block!important;margin:0!important;padding:0!important;overflow:hidden!important;
}
.release-world .release-map-region>.table-workspace>.map-shell>.map{
 box-sizing:border-box!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
 display:block!important;margin:0!important;padding:0!important;aspect-ratio:auto!important;overflow:hidden!important;border:0!important;border-radius:0!important;box-shadow:none!important;
}
.release-world .release-map-region>.table-workspace>.staging-tray{position:absolute!important;z-index:35!important;left:8px!important;right:8px!important;top:8px!important;width:auto!important;max-width:none!important;height:42px!important;min-height:42px!important;margin:0!important;border:1px solid #725d3099!important;border-radius:8px!important;background:#071016df!important;backdrop-filter:blur(5px)!important}
.release-world .release-map-region>.table-workspace>.staging-tray.pallet:empty{display:none!important}
.release-world .desktop-map-zoom{right:8px!important;bottom:8px!important;top:auto!important;left:auto!important}
.release-world .map-context-sidebar{display:none!important;width:0!important}
.release-world .map-shell.map-context-ready{grid-template-columns:minmax(0,1fr)!important}

/* Footer is never allowed to collapse or become a landscape side column. */
.release-world .release-footer-region>.home-footer-stack{
 box-sizing:border-box!important;position:absolute!important;inset:0!important;width:100%!important;height:100%!important;min-width:0!important;min-height:0!important;max-width:none!important;max-height:none!important;
 display:grid!important;grid-template-columns:minmax(0,1fr)!important;grid-template-rows:var(--rw-dice) var(--rw-chat) var(--rw-legal)!important;gap:0!important;margin:0!important;padding:0!important;overflow:hidden!important;background:#080f14!important;border-top:1px solid var(--rw-border)!important;
}
.release-world #footer-slider{grid-row:1!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;border-width:0 0 1px!important}
.release-world #footer-slider>.dice-circular-set{padding:4px 5px!important;gap:5px!important}
.release-world .footer-character-button{box-sizing:border-box!important;flex:0 0 104px!important;width:104px!important;min-width:104px!important;height:48px!important;min-height:48px!important;max-height:48px!important;display:grid!important;grid-template-columns:38px minmax(0,1fr)!important;align-items:center!important;gap:5px!important;padding:3px!important;border:1px solid var(--rw-border)!important;border-radius:8px!important;background:#111a20!important;color:#e7d39a!important;overflow:hidden!important}
.release-world .footer-character-button img{display:block!important;width:38px!important;height:38px!important;border-radius:50%!important;object-fit:cover!important}
.release-world .footer-character-button span{min-width:0!important;display:grid!important;text-align:left!important}
.release-world .footer-character-button strong,.release-world .footer-character-button small{overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}
.release-world .footer-character-button strong{font:800 9px/1.1 system-ui!important}.release-world .footer-character-button small{color:#9e947d!important;font:700 7px/1.1 system-ui!important;text-transform:uppercase!important}
.release-world #footer-slider .die-button,.release-world #footer-slider .die-control,.release-world #footer-slider .sum,.release-world #footer-slider .clear-dice,.release-world #footer-slider .history-scroll-button{height:48px!important;min-height:48px!important;max-height:48px!important}
.release-world .home-inline-chat{box-sizing:border-box!important;grid-row:2!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;display:grid!important;grid-template-columns:34px minmax(0,1fr) 56px!important;gap:4px!important;align-items:center!important;margin:0!important;padding:3px 5px!important;border:0!important;background:#080f13!important}
.release-world .home-inline-chat .chat-history-toggle{box-sizing:border-box!important;width:34px!important;height:34px!important;min-height:34px!important}
.release-world .home-chat-compose{box-sizing:border-box!important;min-width:0!important;height:34px!important;display:grid!important;grid-template-columns:auto minmax(0,1fr)!important;align-items:center!important;gap:5px!important;margin:0!important}
.release-world .home-chat-compose>span{color:#c7b98e!important;font:700 8px/1 system-ui!important;white-space:nowrap!important}
.release-world .home-chat-compose textarea{box-sizing:border-box!important;width:100%!important;height:34px!important;min-height:34px!important;max-height:34px!important;resize:none!important;overflow:auto!important;margin:0!important;padding:5px 7px!important;border:1px solid #4b4028!important;border-radius:6px!important;background:#050c10!important;color:#eee6d3!important;font-size:16px!important}
.release-world .home-chat-send{box-sizing:border-box!important;width:56px!important;height:34px!important;min-height:34px!important;margin:0!important;border:1px solid #5b4b29!important;border-radius:6px!important;background:#111a20!important;color:#e3cc8f!important;font:800 9px/1 system-ui!important}
.release-world .site-copyright-notice{box-sizing:border-box!important;grid-row:3!important;width:100%!important;height:100%!important;min-height:0!important;display:flex!important;align-items:center!important;justify-content:center!important;margin:0!important;padding:0 5px!important;overflow:hidden!important;border:0!important;background:#05090c!important;color:#736d60!important;font:600 7px/1 system-ui!important;white-space:nowrap!important;text-overflow:ellipsis!important}

/* Overlay products float above WORLD instead of consuming WORLD rows. */
.release-world>.asset-slider-stack,.release-world>.character-mixer,.release-world>.recursion-cockpit,.release-world>.mmo-zone-actions,.release-world>.rist-welcome-tutorial,.release-world .card-library-overlay,.release-world .tile-browser{z-index:300!important}

@media (max-height:560px) and (orientation:landscape){
 :root{--rw-context:22px;--rw-menu:48px;--rw-public:54px;--rw-private:54px;--rw-footer:94px;--rw-dice:46px;--rw-chat:38px;--rw-legal:10px}
 .world-context-strip>*{height:18px!important;min-height:18px!important;font-size:8px!important;line-height:16px!important}
 .release-world .root-menu-button{flex-basis:66px!important;width:66px!important;min-width:66px!important;max-width:66px!important;height:40px!important;min-height:40px!important;max-height:40px!important;grid-template-rows:minmax(0,1fr) 9px!important}
 .release-world .root-menu-art{width:25px!important;height:25px!important}.release-world .header-card-back{width:26px!important;height:26px!important}.release-world .header-mmo-button .mmo-toggle-art{width:29px!important;height:26px!important}
 .release-world .asset-rail-header{height:19px!important;min-height:19px!important;max-height:19px!important}.release-world .release-public-region>.public-assets-rail,.release-world .release-private-region>.private-assets-rail{grid-template-rows:19px minmax(0,1fr)!important}
 .release-world .public-assets-items .public-asset-card,.release-world .private-assets-items .compact-hand-card,.release-world .private-assets-items .standard-hand-card,.release-world .public-assets-rail .token-pin-source,.release-world .private-assets-rail .token-pin-source{height:30px!important;min-height:30px!important;max-height:30px!important}
 .release-world #footer-slider .die-button,.release-world #footer-slider .die-control,.release-world #footer-slider .sum,.release-world #footer-slider .clear-dice,.release-world #footer-slider .history-scroll-button,.release-world .footer-character-button{height:38px!important;min-height:38px!important;max-height:38px!important}
 .release-world .footer-character-button{flex-basis:92px!important;width:92px!important;min-width:92px!important;grid-template-columns:30px minmax(0,1fr)!important}.release-world .footer-character-button img{width:30px!important;height:30px!important}
 .release-world .home-inline-chat{grid-template-columns:30px minmax(0,1fr) 50px!important}.release-world .home-inline-chat .chat-history-toggle,.release-world .home-chat-compose,.release-world .home-chat-compose textarea,.release-world .home-chat-send{height:30px!important;min-height:30px!important;max-height:30px!important}
}
'''

text = CSS.read_text(encoding="utf-8")
marker = "/* RIST RELEASE WORLD AUTHORITY"
if marker in text:
    text = text.split("/* ========================================================================== */\n/* RIST RELEASE WORLD AUTHORITY", 1)[0].rstrip() + "\n"
CSS.write_text(text.rstrip() + AUTHORITY + "\n", encoding="utf-8")
