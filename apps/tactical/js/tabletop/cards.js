import { recordTabletopEvent } from "./scene.js";

export function revealCard(tabletop, cardId) {
  if (!tabletop.cards[cardId]) return { ok: false, message: "Unknown card." };
  if (!tabletop.sceneState.revealedCardIds.includes(cardId)) tabletop.sceneState.revealedCardIds.push(cardId);
  recordTabletopEvent(tabletop, "card_reveal", { cardId });
  return { ok: true, card: tabletop.cards[cardId] };
}

export function shareCard(tabletop, cardId, audience = "scene") {
  const card = tabletop.cards[cardId];
  if (!card) return { ok: false, message: "Unknown card." };
  if (!tabletop.sceneState.sharedCardIds.includes(cardId)) tabletop.sceneState.sharedCardIds.push(cardId);
  tabletop.sceneState.cardShareState[cardId] = audience;
  recordTabletopEvent(tabletop, "card_share", { cardId, audience });
  return { ok: true, card };
}

export function cardStackRemaining(tabletop, cardId) {
  const card = tabletop.cards[cardId];
  const used = Number(tabletop.sceneState.cardUseCounts[cardId] || 0);
  return Math.max(0, Number(card?.stackCount || 0) - used);
}
