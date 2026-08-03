import { shareCard } from "./cards.js";

export function toggleLoreScroll(tabletop) {
  tabletop.layout.ancientScrollOpen = !tabletop.layout.ancientScrollOpen;
  tabletop.layout.activeDeckId = tabletop.layout.ancientScrollOpen ? "deck-lore-tavern-001" : "deck-player-a-001";
  return { ok: true, open: tabletop.layout.ancientScrollOpen };
}

export function shareLoreCard(tabletop, cardId = "card-lore-tavern-warning", audience = "scene_shared") {
  const result = shareCard(tabletop, cardId, audience);
  if (result.ok) {
    tabletop.sceneState.cardDiscoveryState[cardId] = "discovered";
  }
  return result;
}
