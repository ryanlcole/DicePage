import { deepClone, recordEvent, pushMessage } from "./state.js";
import { findTile, getCurrentMap } from "./maps.js";
import { startEncounter } from "./encounter.js";

export const TRIGGER_CONDITIONS = Object.freeze([
  "player_enters_tile",
  "player_leaves_tile",
  "player_interacts",
  "gm_manual",
  "map_entered",
  "map_exited",
  "elapsed_time",
  "round_started",
  "entity_defeated",
  "tile_state_changed"
]);

export const TRIGGER_EFFECTS = Object.freeze([
  "reveal_tile",
  "hide_tile",
  "open_child_map",
  "change_tile_state",
  "move_entity",
  "display_message",
  "start_encounter"
]);

export function triggerTemplate(condition = "player_interacts", tile = null) {
  const safeCondition = TRIGGER_CONDITIONS.includes(condition) ? condition : "player_interacts";
  return {
    id: `trigger-${safeCondition}-${Date.now().toString(36)}`,
    hidden: true,
    once: true,
    enabled: true,
    sourceTileId: tile?.id || null,
    conditions: [safeCondition],
    effects: [{ type: "display_message", message: "Trigger resolved." }],
    activated: false
  };
}

export function processMapEvent(state, condition, context = {}) {
  const map = getCurrentMap(state);
  const candidates = map.triggers.filter((trigger) => {
    if (!trigger.enabled) return false;
    if (trigger.once && trigger.activated) return false;
    if (!trigger.conditions.includes(condition)) return false;
    if (condition === "player_enters_tile" && trigger.sourceTileId) {
      const tile = findTile(map, trigger.sourceTileId);
      return tile && context.to && context.to.x >= tile.x && context.to.y >= tile.y && context.to.x < tile.x + tile.width && context.to.y < tile.y + tile.height;
    }
    return true;
  });
  for (const trigger of candidates) {
    const result = activateTrigger(state, trigger.id, condition, context);
    if (result.ok && state.activeEncounter) return result;
  }
  return { ok: true, activated: candidates.length };
}

export function activateTrigger(state, triggerId, condition = "gm_manual", context = {}) {
  const map = getCurrentMap(state);
  const trigger = map.triggers.find((item) => item.id === triggerId);
  if (!trigger) return { ok: false, message: "Trigger not found." };
  if (!trigger.enabled) {
    recordEvent(state, "trigger_activated", { triggerId, condition, reason: "disabled" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Trigger is disabled." };
  }
  if (!trigger.conditions.includes(condition)) {
    recordEvent(state, "trigger_activated", { triggerId, condition, reason: "condition mismatch" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Trigger condition is not valid." };
  }
  if (trigger.once && trigger.activated) {
    recordEvent(state, "trigger_activated", { triggerId, condition, reason: "already activated" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Trigger already activated." };
  }
  if (!trigger.effects.every((effect) => TRIGGER_EFFECTS.includes(effect.type))) {
    recordEvent(state, "trigger_activated", { triggerId, condition, reason: "invalid effect" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Trigger contains an invalid effect." };
  }

  trigger.activated = true;
  recordEvent(state, "trigger_activated", { mapId: map.id, trigger: visibleTriggerPayload(trigger), condition, context: deepClone(context) });
  let result = { ok: true };
  for (const effect of trigger.effects) {
    result = applyTriggerEffect(state, effect, trigger, context);
    if (!result.ok) return result;
  }
  return { ok: true, trigger };
}

function visibleTriggerPayload(trigger) {
  return {
    id: trigger.id,
    hidden: trigger.hidden,
    once: trigger.once,
    enabled: trigger.enabled,
    sourceTileId: trigger.sourceTileId,
    conditions: deepClone(trigger.conditions),
    effects: deepClone(trigger.effects)
  };
}

function applyTriggerEffect(state, effect, trigger, context) {
  const map = getCurrentMap(state);
  if (effect.type === "display_message") {
    pushMessage(state, effect.message || "Trigger resolved.");
    return { ok: true };
  }
  if (effect.type === "reveal_tile" || effect.type === "hide_tile" || effect.type === "change_tile_state") {
    const tile = findTile(map, effect.tileId || trigger.sourceTileId);
    if (!tile) return { ok: false, message: "Trigger target tile not found." };
    if (effect.type === "reveal_tile") tile.hiddenFromPlayers = false;
    if (effect.type === "hide_tile") tile.hiddenFromPlayers = true;
    if (effect.type === "change_tile_state") tile.metadata = { ...(tile.metadata || {}), state: effect.state || "changed" };
    recordEvent(state, "tile_state_changed", { mapId: map.id, tileId: tile.id, effect: effect.type });
    return { ok: true };
  }
  if (effect.type === "move_entity") {
    const entity = map.entities.find((item) => item.id === effect.entityId);
    if (!entity) return { ok: false, message: "Trigger target entity not found." };
    const from = { x: entity.x, y: entity.y };
    entity.x = effect.x;
    entity.y = effect.y;
    recordEvent(state, "movement", { mapId: map.id, entityId: entity.id, from, to: { x: entity.x, y: entity.y }, source: "trigger" });
    return { ok: true };
  }
  if (effect.type === "open_child_map") {
    const tile = findTile(map, effect.tileId || trigger.sourceTileId);
    if (!tile || !tile.childMapId) return { ok: false, message: "Trigger child map is missing." };
    state.currentMapId = tile.childMapId;
    recordEvent(state, "child_map_entered", { parentMapId: map.id, childMapId: tile.childMapId, source: "trigger" });
    return { ok: true };
  }
  if (effect.type === "start_encounter") {
    return startEncounter(state, effect.encounterId, { source: "trigger", triggerId: trigger.id, sourceTileId: trigger.sourceTileId, context });
  }
  return { ok: false, message: "Unsupported trigger effect." };
}
