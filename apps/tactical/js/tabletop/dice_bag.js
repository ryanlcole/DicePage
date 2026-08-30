import { rollDie } from "./dice.js";
import { modifierTotal, visibleModifierRows } from "./chips.js";
import { recordTabletopEvent } from "./scene.js";

export function resolveDiceBagAction(tabletop, cardId, actionId = "attack", context = {}) {
  const card = tabletop.cards[cardId];
  const action = card?.actionProfiles?.find((item) => item.actionId === actionId);
  if (!card || !action) return { ok: false, message: "Card has no matching Dice Bag action." };
  const attackRoll = rollDie(tabletop, "d20", { source: `dice_bag:${cardId}:attack` });
  const damageRoll = rollDie(tabletop, "d6", { source: `dice_bag:${cardId}:damage` });
  if (!attackRoll.ok || !damageRoll.ok) return { ok: false, message: "Dice Bag roll failed." };
  const baseAttack = Number(context.baseAttack ?? 3);
  const attackModifiers = modifierTotal(tabletop, "attack");
  const totalAttack = attackRoll.roll.result + baseAttack + attackModifiers;
  const result = {
    cardId,
    actionId,
    attackRoll: attackRoll.roll.result,
    damageRoll: damageRoll.roll.result,
    baseAttack,
    modifiers: visibleModifierRows(tabletop, "attack"),
    totalAttack,
    damageTotal: damageRoll.roll.result,
    authoritative: true,
    visualSeed: `${attackRoll.roll.result}:${damageRoll.roll.result}:${tabletop.replayBoundary.nextSequence}`
  };
  tabletop.sceneState.cardUseCounts[cardId] = Number(tabletop.sceneState.cardUseCounts[cardId] || 0) + 1;
  recordTabletopEvent(tabletop, "card_used", { cardId, actionId });
  recordTabletopEvent(tabletop, "dice_bag_resolved", result);
  return { ok: true, result };
}
