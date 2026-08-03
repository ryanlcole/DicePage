import fs from "node:fs/promises";
import { createTabletopState, tabletopProjection } from "../js/tabletop/scene.js";
import { rollDie } from "../js/tabletop/dice.js";
import { resolveDiceBagAction } from "../js/tabletop/dice_bag.js";
import { drawTopCard, commanderHand } from "../js/tabletop/decks.js";
import { shareLoreCard } from "../js/tabletop/lore.js";
import { advanceInitiative } from "../js/tabletop/initiative.js";
import { pauseClock, resumeClock, clockProgress } from "../js/tabletop/clock.js";
import { sameTapTarget, snapRotationDeg } from "../js/tabletop/gestures.js";

const root = new URL("../", import.meta.url);

async function readJson(relativePath) {
  return JSON.parse(await fs.readFile(new URL(relativePath, root), "utf8"));
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const tabletop = createTabletopState({
  cards: await readJson("data/tabletop/card_definitions.json"),
  decks: await readJson("data/tabletop/deck_definitions.json"),
  dice: await readJson("data/tabletop/dice_profiles.json"),
  chips: await readJson("data/tabletop/chip_profiles.json"),
  initiative: await readJson("data/tabletop/initiative_profiles.json"),
  demoScene: await readJson("data/tabletop/demo_scene.json")
});

const gmProjection = tabletopProjection(tabletop, "gm", "player-a");
const playerProjection = tabletopProjection(tabletop, "player", "player-a");
assert(gmProjection.decks.some((deck) => deck.deckId === "deck-orcs-001"), "GM monster deck missing");
assert(!playerProjection.decks.some((deck) => deck.deckId === "deck-orcs-001"), "monster deck leaked to player");
assert(playerProjection.cards.some((card) => card.cardId === "card-player-lyra"), "owned player card missing");
assert(!playerProjection.cards.some((card) => card.cardId === "card-orc-commander"), "GM private commander leaked");
assert(gmProjection.dice.length === 9, "not all dice profiles loaded");

const d20 = rollDie(tabletop, "d20");
assert(d20.ok && d20.roll.result === 14, "deterministic D20 result mismatch");
const d6 = rollDie(tabletop, "d6");
assert(d6.ok && d6.roll.result === 1, "deterministic D6 result mismatch");

const fresh = createTabletopState({
  cards: await readJson("data/tabletop/card_definitions.json"),
  decks: await readJson("data/tabletop/deck_definitions.json"),
  dice: await readJson("data/tabletop/dice_profiles.json"),
  chips: await readJson("data/tabletop/chip_profiles.json"),
  initiative: await readJson("data/tabletop/initiative_profiles.json"),
  demoScene: await readJson("data/tabletop/demo_scene.json")
});
const bag = resolveDiceBagAction(fresh, "card-weapon-sword-001", "attack", { baseAttack: 3 });
assert(bag.ok, "Dice Bag action rejected");
assert(bag.result.attackRoll === 14, "Dice Bag attack die mismatch");
assert(bag.result.totalAttack === 17, "Dice Bag modifiers mismatch");
assert(bag.result.modifiers.some((chip) => chip.label === "+1 Attack"), "+1 attack chip not represented");
assert(bag.result.modifiers.some((chip) => chip.label === "-1 Repeat"), "penalty chip not represented");

const draw = drawTopCard(fresh, "deck-player-a-001");
assert(draw.ok && draw.card.cardId === "card-player-lyra", "player deck draw mismatch");
assert(commanderHand(fresh, "card-orc-commander").length === 2, "commander subordinate hand mismatch");

const lore = shareLoreCard(fresh);
assert(lore.ok, "lore share failed");
assert(tabletopProjection(fresh, "player", "player-a").cards.some((card) => card.cardId === "card-lore-tavern-warning"), "shared lore not visible to player");

assert(advanceInitiative(fresh).ok, "initiative did not advance");
assert(pauseClock(fresh).ok && clockProgress(fresh).paused, "clock did not pause");
assert(resumeClock(fresh).ok && !clockProgress(fresh).paused, "clock did not resume");

assert(snapRotationDeg(46) === 90 && snapRotationDeg(359) === 0, "rotation snap mismatch");
assert(sameTapTarget(
  { mapId: "map-world", cellId: "square:1,1", point: { x: 10, y: 10 }, time: 100 },
  { mapId: "map-world", cellId: "square:1,1", point: { x: 18, y: 16 }, time: 300 }
), "double-tap target rejected");
assert(!fresh.replayBoundary.authoritativeEvents.some((event) => event.type.startsWith("viewport_") || event.type === "menu_opened"), "local UI event entered tabletop replay boundary");

console.log(JSON.stringify({
  ok: true,
  dice: { d20: d20.roll.result, d6: d6.roll.result },
  diceBag: bag.result,
  tabletopEvents: fresh.replayBoundary.authoritativeEvents.length,
  gmDecks: gmProjection.decks.length,
  playerDecks: playerProjection.decks.length
}, null, 2));
