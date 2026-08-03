import { recordTabletopEvent } from "./scene.js";

export function selectDeck(tabletop, deckId) {
  if (!tabletop.decks[deckId]) return { ok: false, message: "Unknown deck." };
  tabletop.layout.activeDeckId = deckId;
  return { ok: true, deck: tabletop.decks[deckId] };
}

export function selectCard(tabletop, cardId) {
  if (!tabletop.cards[cardId]) return { ok: false, message: "Unknown card." };
  tabletop.layout.selectedCardId = cardId;
  return { ok: true, card: tabletop.cards[cardId] };
}

export function drawTopCard(tabletop, deckId) {
  const deck = tabletop.decks[deckId];
  const cardId = deck?.cards?.[0];
  if (!deck || !cardId) return { ok: false, message: "Deck is empty." };
  tabletop.layout.activeDeckId = deckId;
  tabletop.layout.selectedCardId = cardId;
  recordTabletopEvent(tabletop, "card_draw", { deckId, cardId, drawMode: deck.drawMode });
  return { ok: true, card: tabletop.cards[cardId] };
}

export function commanderHand(tabletop, commanderCardId) {
  const commander = tabletop.cards[commanderCardId];
  return (commander?.handCardIds || []).map((cardId) => tabletop.cards[cardId]).filter(Boolean);
}
