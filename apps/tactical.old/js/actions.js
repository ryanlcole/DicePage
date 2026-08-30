import { recordEvent, pushMessage } from "./state.js";
import { findTile, getCurrentMap, openChildMapFromTile, returnToParentMap, updateSelectedTile } from "./maps.js";
import { activateTrigger } from "./triggers.js";
import { startEncounter } from "./encounter.js";

export const ACTION_TYPES = Object.freeze([
  "enter_child_map",
  "return_to_parent",
  "open",
  "close",
  "reveal",
  "hide",
  "inspect",
  "search",
  "unlock",
  "move_entity",
  "change_tile_state",
  "start_encounter"
]);

export function actionTemplate(type, tile = null) {
  const safeType = ACTION_TYPES.includes(type) ? type : "inspect";
  const base = {
    id: `action-${safeType}-${Date.now().toString(36)}`,
    type: safeType,
    label: safeType.replaceAll("_", " "),
    allowedActors: safeType === "hide" ? ["gm"] : ["gm", "player"],
    timeCost: safeType === "inspect" ? 0 : 2,
    requirements: {},
    effects: []
  };
  if (safeType === "enter_child_map") {
    base.timeCost = 0;
    base.effects.push({ type: "open_child_map", mapId: tile?.childMapId || null, entryPointId: tile?.entryPointId || null });
  }
  if (safeType === "return_to_parent") base.timeCost = 0;
  if (safeType === "reveal") base.effects.push({ type: "reveal_tile", tileId: tile?.id || null });
  if (safeType === "hide") base.effects.push({ type: "hide_tile", tileId: tile?.id || null });
  if (safeType === "start_encounter") {
    base.timeCost = 0;
    base.allowedActors = ["gm"];
    base.effects.push({ type: "start_encounter", encounterId: tile?.encounterId || "enc-tavern-ambush" });
  }
  return base;
}

export function validateAction(state, action, actor, context = {}) {
  if (!action || !ACTION_TYPES.includes(action.type)) return { ok: false, message: "Invalid action type." };
  if (!action.allowedActors?.includes(actor.role)) return { ok: false, message: "Actor is not allowed to use this action." };
  if (actor.role === "player" && context.tile?.hiddenFromPlayers) return { ok: false, message: "Tile is not visible to players." };
  if (action.type === "enter_child_map" && !context.tile?.childMapId) return { ok: false, message: "No child map is assigned." };
  if (action.type === "start_encounter" && !(context.tile?.encounterId || action.effects?.some((effect) => effect.type === "start_encounter" && effect.encounterId))) {
    return { ok: false, message: "No encounter is assigned." };
  }
  return { ok: true };
}

export function executeAction(state, action, actor = { role: state.role, playerId: state.actorPlayerId }, context = {}) {
  const validation = validateAction(state, action, actor, context);
  if (!validation.ok) {
    recordEvent(state, "action_executed", { action: action?.type || "unknown", reason: validation.message, actor }, { rejected: true, stateChanging: false });
    pushMessage(state, validation.message, "warn");
    return validation;
  }

  const map = getCurrentMap(state);
  const tile = context.tile || findTile(map, state.selectedTileId);
  let result = { ok: true };
  recordEvent(state, "action_executed", { actionId: action.id, actionType: action.type, actorRole: actor.role, tileId: tile?.id || null, timeCost: action.timeCost });

  if (action.type === "enter_child_map") {
    result = openChildMapFromTile(state, tile, actor);
  } else if (action.type === "return_to_parent") {
    result = returnToParentMap(state, actor);
  } else if (action.type === "reveal") {
    result = updateSelectedTile(state, { hiddenFromPlayers: false, visible: true });
  } else if (action.type === "hide") {
    result = updateSelectedTile(state, { hiddenFromPlayers: true });
  } else if (action.type === "inspect" || action.type === "search") {
    pushMessage(state, `${action.label}: ${tile?.metadata?.label || map.name}`);
  } else if (action.type === "open" || action.type === "close" || action.type === "unlock" || action.type === "change_tile_state") {
    const nextState = action.type === "close" ? "closed" : "open";
    result = updateSelectedTile(state, { metadata: { ...(tile.metadata || {}), state: nextState } });
  } else if (action.type === "start_encounter") {
    const effect = action.effects?.find((item) => item.type === "start_encounter");
    result = startEncounter(state, effect?.encounterId || tile?.encounterId, { source: "action", sourceTileId: tile?.id || null });
  }

  if (!result.ok) {
    recordEvent(state, "action_executed", { actionId: action.id, reason: result.message }, { rejected: true, stateChanging: false });
    pushMessage(state, result.message, "warn");
    return result;
  }
  return result;
}

export function executeFirstTileAction(state, tile, actor) {
  const action = tile?.actions?.find((item) => item.allowedActors.includes(actor.role));
  if (!action) {
    recordEvent(state, "action_executed", { tileId: tile?.id || null, reason: "no accessible action" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "No accessible action." };
  }
  return executeAction(state, action, actor, { tile });
}

export function manualTriggerSelectedTile(state) {
  const map = getCurrentMap(state);
  const tile = findTile(map, state.selectedTileId);
  const triggerId = tile?.triggers?.[0] || map.triggers.find((trigger) => trigger.conditions.includes("gm_manual"))?.id;
  if (!triggerId) return { ok: false, message: "No manual trigger is available." };
  return activateTrigger(state, triggerId, "gm_manual", { sourceTileId: tile?.id || null, actorRole: "gm" });
}
