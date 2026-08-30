const TABLETOP_SCHEMA = "shaelvien.tabletop.state.v1";

export const TABLETOP_CATEGORIES = Object.freeze([
  "map",
  "scene",
  "objects",
  "entities",
  "decks",
  "cards",
  "dice",
  "initiative",
  "effects",
  "lore",
  "replay",
  "settings"
]);

export function clone(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

export function byKey(items, key) {
  return Object.fromEntries((items || []).map((item) => [item[key], clone(item)]));
}

export function createTabletopState(bundle = {}, persisted = null) {
  const cards = byKey(bundle.cards?.cards, "cardId");
  const decks = byKey(bundle.decks?.decks, "deckId");
  const dice = byKey(bundle.dice?.dice, "dieId");
  const chips = byKey(bundle.chips?.chips, "chipId");
  const initiativeProfiles = byKey(bundle.initiative?.profiles, "initiativeId");
  const scenes = byKey(bundle.demoScene?.scenes, "sceneId");
  const activeSceneId = Object.keys(scenes)[0] || "scene-tavern-ambush-001";
  const scene = scenes[activeSceneId] || {};
  const initiative = initiativeProfiles[scene.initiativeId] || { entries: [], clockSeconds: 90 };
  const activeEntryId = initiative.entries?.[0]?.entryId || null;
  const base = {
    schemaVersion: TABLETOP_SCHEMA,
    activeSceneId,
    cards,
    decks,
    dice,
    chips,
    initiativeProfiles,
    scenes,
    overlay: {
      open: false,
      category: "scene",
      detailCardId: null,
      detailDeckId: null
    },
    layout: {
      ancientScrollOpen: false,
      activeDeckId: "deck-player-a-001",
      selectedCardId: "card-player-lyra",
      selectedDieId: "d20",
      reducedMotion: false,
      menuDimmed: true
    },
    sceneState: {
      sharedCardIds: [],
      revealedCardIds: [],
      cardShareState: {},
      cardDiscoveryState: {},
      activeChipIds: clone(scene.activeChipIds || []),
      diceResults: [],
      cardUseCounts: {},
      drag: null
    },
    initiative: {
      profileId: scene.initiativeId || null,
      activeEntryId,
      round: 1,
      paused: false,
      turnSeconds: Number(initiative.clockSeconds) || 90,
      remainingSeconds: Number(initiative.clockSeconds) || 90
    },
    replayBoundary: {
      authoritativeEvents: [],
      nextSequence: 1,
      excludedLocalEvents: ["menu_opened", "viewport_pan", "viewport_zoom", "viewport_rotate", "tray_moved"]
    }
  };
  if (!persisted || persisted.schemaVersion !== TABLETOP_SCHEMA) return base;
  return {
    ...base,
    overlay: { ...base.overlay, ...(persisted.overlay || {}), open: false },
    layout: { ...base.layout, ...(persisted.layout || {}) },
    sceneState: { ...base.sceneState, ...(persisted.sceneState || {}) },
    initiative: { ...base.initiative, ...(persisted.initiative || {}) },
    replayBoundary: {
      ...base.replayBoundary,
      authoritativeEvents: Array.isArray(persisted.replayBoundary?.authoritativeEvents) ? persisted.replayBoundary.authoritativeEvents : [],
      nextSequence: Number.isInteger(persisted.replayBoundary?.nextSequence) ? persisted.replayBoundary.nextSequence : 1
    }
  };
}

export function serializableTabletopState(tabletop) {
  return {
    schemaVersion: TABLETOP_SCHEMA,
    activeSceneId: tabletop.activeSceneId,
    overlay: clone({ ...tabletop.overlay, open: false }),
    layout: clone(tabletop.layout),
    sceneState: clone(tabletop.sceneState),
    initiative: clone(tabletop.initiative),
    replayBoundary: clone(tabletop.replayBoundary)
  };
}

export function activeScene(tabletop) {
  return tabletop.scenes[tabletop.activeSceneId] || null;
}

export function recordTabletopEvent(tabletop, type, payload = {}) {
  const event = {
    sequence: tabletop.replayBoundary.nextSequence++,
    type,
    sceneId: tabletop.activeSceneId,
    payload: clone(payload)
  };
  tabletop.replayBoundary.authoritativeEvents.push(event);
  return event;
}

export function canSeeVisibility(visibility, role = "gm", playerId = "player-a", ownerPlayerId = null, shared = false) {
  if (role === "gm") return true;
  if (shared) return true;
  if (visibility === "public" || visibility === "scene_shared" || visibility === "party_shared") return true;
  if (visibility === "player_private") return ownerPlayerId === playerId;
  return false;
}

export function tabletopProjection(tabletop, role = "gm", playerId = "player-a") {
  const sharedCards = new Set(tabletop.sceneState.sharedCardIds || []);
  const cards = Object.values(tabletop.cards).filter((card) => canSeeVisibility(card.visibility, role, playerId, card.ownerPlayerId, sharedCards.has(card.cardId)));
  const cardIds = new Set(cards.map((card) => card.cardId));
  const decks = Object.values(tabletop.decks).filter((deck) => {
    if (!canSeeVisibility(deck.visibility, role, playerId, deck.ownerPlayerId, false)) return false;
    return (deck.cards || []).some((cardId) => cardIds.has(cardId));
  }).map((deck) => ({
    ...clone(deck),
    cards: (deck.cards || []).filter((cardId) => cardIds.has(cardId))
  }));
  const initiativeProfile = tabletop.initiativeProfiles[tabletop.initiative.profileId] || { entries: [] };
  const initiativeEntries = (initiativeProfile.entries || []).filter((entry) => canSeeVisibility(entry.visibility, role, playerId, null, false));
  return {
    scene: activeScene(tabletop),
    cards,
    decks,
    chips: Object.values(tabletop.chips).filter((chip) => canSeeVisibility(chip.visibility, role, playerId, null, true)),
    dice: Object.values(tabletop.dice),
    initiativeEntries,
    sharedCards: cards.filter((card) => sharedCards.has(card.cardId))
  };
}

export function openOverlay(tabletop, category = "scene", detail = {}) {
  tabletop.overlay.open = true;
  tabletop.overlay.category = TABLETOP_CATEGORIES.includes(category) ? category : "scene";
  tabletop.overlay.detailCardId = detail.cardId || null;
  tabletop.overlay.detailDeckId = detail.deckId || null;
}

export function closeOverlay(tabletop) {
  tabletop.overlay.open = false;
  tabletop.overlay.detailCardId = null;
  tabletop.overlay.detailDeckId = null;
}
