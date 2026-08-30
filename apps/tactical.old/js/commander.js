import { deepClone, recordEvent, pushMessage } from "./state.js";
import { bestStepToward, canCombatantMoveTo, chooseAttackTarget, livingCombatants, nearestEnemy, recordEncounterEvent } from "./encounter.js";

export const COMMANDER_ORDERS = Object.freeze([
  "hold_position",
  "attack_nearest",
  "focus_target",
  "defend_target",
  "block_exit",
  "surround_target",
  "retreat"
]);

export function issueCommanderOrder(state, actor, orderType, options = {}) {
  const encounter = state.activeEncounter;
  if (!encounter || encounter.status !== "active") return { ok: false, message: "No active encounter." };
  if (actor.role !== "gm") {
    recordEvent(state, "commander_order_issued", { orderType, reason: "unauthorized" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Only the GM can issue commander orders." };
  }
  if (!COMMANDER_ORDERS.includes(orderType)) return { ok: false, message: "Unknown commander order." };
  const commander = livingCombatants(state, "monsters").find((entity) => entity.role === "commander");
  if (!commander) return { ok: false, message: "Monster commander is unavailable." };
  const controlled = livingCombatants(state, "monsters")
    .filter((entity) => entity.role !== "commander")
    .sort((a, b) => b.initiative - a.initiative || a.id.localeCompare(b.id));
  const orderId = `order-${encounter.commandHistory.length + 1}`;
  const order = {
    orderId,
    orderType,
    commanderId: commander.id,
    targetId: options.targetId || null,
    controlledIds: controlled.map((entity) => entity.id)
  };
  encounter.commandHistory.push(deepClone(order));
  recordEvent(state, "commander_order_issued", { encounterId: encounter.encounterId, ...order });
  recordEncounterEvent(state, "commander_order_issued", order);

  controlled.forEach((entity) => {
    const action = generateMonsterAction(state, entity, orderType, options);
    if (!action) return;
    encounter.pendingCommanderActions = encounter.pendingCommanderActions.filter((item) => item.entityId !== entity.id);
    const queuedAction = {
      orderId,
      entityId: entity.id,
      source: "commander",
      action
    };
    encounter.pendingCommanderActions.push(queuedAction);
    recordEvent(state, "commander_action_generated", { encounterId: encounter.encounterId, queuedAction: deepClone(queuedAction) });
    recordEncounterEvent(state, "commander_action_generated", { queuedAction: deepClone(queuedAction) });
  });
  pushMessage(state, `Commander order: ${orderType}`);
  return { ok: true, order, queued: encounter.pendingCommanderActions.filter((item) => item.orderId === orderId) };
}

export function directMonsterOverride(state, actor, monsterId, actionType) {
  const encounter = state.activeEncounter;
  if (!encounter || encounter.status !== "active") return { ok: false, message: "No active encounter." };
  if (actor.role !== "gm") {
    recordEvent(state, "direct_gm_override", { monsterId, reason: "unauthorized" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Only the GM can directly control monsters." };
  }
  const monster = livingCombatants(state, "monsters").find((entity) => entity.id === monsterId);
  if (!monster) return { ok: false, message: "Monster is unavailable." };
  const previous = encounter.pendingCommanderActions.find((item) => item.entityId === monster.id) || null;
  encounter.pendingCommanderActions = encounter.pendingCommanderActions.filter((item) => item.entityId !== monster.id);
  const queuedAction = {
    orderId: previous?.orderId || "direct",
    entityId: monster.id,
    source: "direct_gm",
    action: normalizeDirectAction(state, monster, actionType)
  };
  encounter.pendingCommanderActions.push(queuedAction);
  const payload = {
    encounterId: encounter.encounterId,
    entityId: monster.id,
    previousCommanderOrder: previous ? deepClone(previous) : null,
    queuedAction: deepClone(queuedAction),
    controller: "gm"
  };
  recordEvent(state, "direct_gm_override", payload);
  recordEncounterEvent(state, "direct_gm_override", payload);
  pushMessage(state, `Direct override: ${monster.name}`);
  return { ok: true, queuedAction };
}

function generateMonsterAction(state, entity, orderType, options) {
  if (orderType === "hold_position" || orderType === "defend_target") return { type: "defend", entityId: entity.id };
  if (orderType === "retreat") return retreatAction(state, entity);
  if (orderType === "block_exit") return moveTowardPoint(state, entity, { x: 1, y: 4 }) || { type: "defend", entityId: entity.id };
  if (orderType === "surround_target") return attackOrMoveNearest(state, entity, options.targetId, true);
  if (orderType === "focus_target") return attackOrMoveNearest(state, entity, options.targetId, false);
  return attackOrMoveNearest(state, entity, null, false);
}

function attackOrMoveNearest(state, entity, targetId, flank) {
  const adjacent = chooseAttackTarget(state, entity, targetId);
  if (adjacent) return { type: "basic_attack", entityId: entity.id, targetId: adjacent.id };
  const target = targetId ? livingCombatants(state, "players").find((item) => item.id === targetId) : nearestEnemy(state, entity);
  if (!target) return { type: "wait", entityId: entity.id };
  const step = flank ? flankStep(state, entity, target) : bestStepToward(state, entity, target);
  if (step) return { type: "move", entityId: entity.id, direction: step.direction };
  return { type: "defend", entityId: entity.id };
}

function flankStep(state, entity, target) {
  const candidates = [
    { direction: "up", dx: 0, dy: -1 },
    { direction: "down", dx: 0, dy: 1 },
    { direction: "left", dx: -1, dy: 0 },
    { direction: "right", dx: 1, dy: 0 }
  ]
    .map((step) => ({ ...step, x: entity.x + step.dx, y: entity.y + step.dy }))
    .filter((step) => canCombatantMoveTo(state, entity, step.x, step.y))
    .map((step) => ({ ...step, score: Math.abs(step.x - target.x) + Math.abs(step.y - target.y) + (step.y === target.y ? 1 : 0) }))
    .sort((a, b) => a.score - b.score || a.direction.localeCompare(b.direction));
  return candidates[0] || null;
}

function moveTowardPoint(state, entity, point) {
  const target = { x: point.x, y: point.y };
  return bestStepToward(state, entity, target);
}

function retreatAction(state, entity) {
  const enemies = livingCombatants(state, "players");
  const candidates = [
    { direction: "left", dx: -1, dy: 0 },
    { direction: "right", dx: 1, dy: 0 },
    { direction: "up", dx: 0, dy: -1 },
    { direction: "down", dx: 0, dy: 1 }
  ]
    .map((step) => ({ ...step, x: entity.x + step.dx, y: entity.y + step.dy }))
    .filter((step) => canCombatantMoveTo(state, entity, step.x, step.y))
    .map((step) => ({
      ...step,
      distance: enemies.reduce((total, enemy) => total + Math.abs(step.x - enemy.x) + Math.abs(step.y - enemy.y), 0)
    }))
    .sort((a, b) => b.distance - a.distance || a.direction.localeCompare(b.direction));
  return candidates[0] ? { type: "move", entityId: entity.id, direction: candidates[0].direction } : { type: "defend", entityId: entity.id };
}

function normalizeDirectAction(state, monster, actionType) {
  if (actionType === "basic_attack") {
    const target = chooseAttackTarget(state, monster);
    return target ? { type: "basic_attack", entityId: monster.id, targetId: target.id } : { type: "wait", entityId: monster.id };
  }
  if (actionType.startsWith("move_")) {
    return { type: "move", entityId: monster.id, direction: actionType.replace("move_", "") };
  }
  if (actionType === "wait") return { type: "wait", entityId: monster.id };
  return { type: "defend", entityId: monster.id };
}
