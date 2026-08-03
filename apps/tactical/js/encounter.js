import { RULES_VERSION, SCENES, deepClone, recordEvent, pushMessage } from "./state.js";
import { getMapPath, restoreExplorationAfterEncounter } from "./maps.js";
import { comparableEncounterState, createReplayRecord, stableHash } from "./replay.js";

export const ENCOUNTER_SCHEMA_VERSION = "shaelvien.encounter.v1";

const DIRECTIONS = Object.freeze({
  up: { dx: 0, dy: -1 },
  down: { dx: 0, dy: 1 },
  left: { dx: -1, dy: 0 },
  right: { dx: 1, dy: 0 }
});

export function startEncounter(state, encounterId, context = {}) {
  const definition = state.encounters[encounterId];
  if (!definition) {
    recordEvent(state, "encounter_started", { encounterId, reason: "missing encounter" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Encounter definition not found." };
  }
  const battleMap = state.maps[definition.battleMapId];
  const territory = state.maps[definition.territoryId];
  if (!battleMap || !territory) {
    recordEvent(state, "encounter_started", { encounterId, reason: "missing maps" }, { rejected: true, stateChanging: false });
    return { ok: false, message: "Encounter maps are incomplete." };
  }

  state.explorationBeforeEncounter = {
    currentMapId: state.currentMapId,
    selectedTileId: state.selectedTileId,
    mapPath: getMapPath(state)
  };

  const combatants = buildCombatants(state, definition);
  const turnOrder = combatants
    .filter((entity) => !entity.defeated)
    .sort((a, b) => b.initiative - a.initiative || a.id.localeCompare(b.id))
    .map((entity) => entity.id);

  const encounterState = {
    schemaVersion: ENCOUNTER_SCHEMA_VERSION,
    rulesVersion: RULES_VERSION,
    encounterId: definition.id,
    territoryId: definition.territoryId,
    battleMapId: definition.battleMapId,
    name: definition.name,
    round: 1,
    status: "active",
    winner: null,
    timeAllowance: definition.roundTimeAllowance,
    timeCosts: deepClone(definition.timeCosts),
    combatants,
    turnOrder,
    activeTurnIndex: 0,
    activeEntityId: turnOrder[0],
    pendingCommanderActions: [],
    commandHistory: [],
    events: [],
    initialState: null,
    finalReplayId: null,
    territorySummary: {
      name: territory.name,
      category: territory.category,
      placedTileCount: territory.placedTiles.length
    }
  };
  encounterState.initialState = comparableEncounterState({ ...encounterState, events: [] });
  state.activeEncounter = encounterState;
  state.currentMapId = definition.battleMapId;
  state.scene = SCENES.ENCOUNTER;
  recordEvent(state, "encounter_started", {
    encounterId: definition.id,
    territoryId: definition.territoryId,
    battleMapId: definition.battleMapId,
    source: context.source || "manual",
    triggerId: context.triggerId || null,
    mapPath: getMapPath(state)
  });
  recordEncounterEvent(state, "encounter_started", {
    encounterId: definition.id,
    territoryId: definition.territoryId,
    battleMapId: definition.battleMapId,
    source: context.source || "manual",
    triggerId: context.triggerId || null
  });
  pushMessage(state, `${definition.name} started.`);
  return { ok: true, encounter: encounterState };
}

function buildCombatants(state, definition) {
  const players = definition.playerStarts.map((start) => {
    const character = state.characters[start.definitionId];
    return {
      id: start.entityId,
      definitionId: start.definitionId,
      name: character.name,
      controller: "player",
      assignedPlayerId: character.assignedPlayerId,
      faction: "players",
      role: "character",
      x: start.x,
      y: start.y,
      hp: character.hp,
      maxHp: character.hp,
      attack: character.attack,
      defense: character.defense,
      initiative: character.initiative,
      defeated: false,
      defending: false,
      timeSpent: 0
    };
  });
  const monsters = definition.monsterStarts.map((start) => {
    const creature = state.creatures[start.definitionId];
    return {
      id: start.entityId,
      definitionId: start.definitionId,
      name: creature.name,
      controller: "gm",
      assignedPlayerId: null,
      faction: "monsters",
      role: creature.role,
      commanderId: creature.commanderId || null,
      x: start.x,
      y: start.y,
      hp: creature.hp,
      maxHp: creature.hp,
      attack: creature.attack,
      defense: creature.defense,
      initiative: creature.initiative,
      defeated: false,
      defending: false,
      timeSpent: 0
    };
  });
  return [...players, ...monsters];
}

export function activeCombatant(state) {
  const encounter = state.activeEncounter;
  if (!encounter) return null;
  return encounter.combatants.find((entity) => entity.id === encounter.activeEntityId) || null;
}

export function livingCombatants(state, faction = null) {
  return (state.activeEncounter?.combatants || []).filter((entity) => !entity.defeated && (!faction || entity.faction === faction));
}

export function recordEncounterEvent(state, type, payload = {}) {
  const encounter = state.activeEncounter;
  if (!encounter) return null;
  const event = {
    sequence: encounter.events.length + 1,
    type,
    round: encounter.round,
    activeEntityId: encounter.activeEntityId,
    payload: deepClone(payload)
  };
  encounter.events.push(event);
  return event;
}

export function validateEncounterAction(state, actor, action) {
  const encounter = state.activeEncounter;
  if (!encounter || encounter.status !== "active") return { ok: false, message: "No active encounter." };
  if (!action || !["move", "basic_attack", "defend", "interact", "inspect", "wait"].includes(action.type)) {
    return { ok: false, message: "Invalid encounter action." };
  }
  const entity = encounter.combatants.find((item) => item.id === (action.entityId || encounter.activeEntityId));
  if (!entity || entity.defeated) return { ok: false, message: "Combatant is unavailable." };
  if (action.type !== "inspect" && entity.id !== encounter.activeEntityId) return { ok: false, message: "It is not that combatant's activation." };
  if (actor.role === "player") {
    if (entity.controller !== "player" || entity.assignedPlayerId !== actor.playerId) return { ok: false, message: "Player is not authorized for that combatant." };
  }
  if (actor.role === "gm" && entity.controller === "player" && action.source !== "test") {
    return { ok: false, message: "GM direct controls are limited to monsters in this slice." };
  }
  const cost = actionCost(encounter, action);
  if (cost > remainingTime(entity, encounter)) return { ok: false, message: "Insufficient time remains." };
  if (action.type === "move") {
    const direction = DIRECTIONS[action.direction];
    if (!direction) return { ok: false, message: "Invalid movement direction." };
    const to = { x: entity.x + direction.dx, y: entity.y + direction.dy };
    if (!canCombatantMoveTo(state, entity, to.x, to.y)) return { ok: false, message: "Movement blocked." };
  }
  if (action.type === "basic_attack") {
    const target = chooseAttackTarget(state, entity, action.targetId);
    if (!target) return { ok: false, message: "No adjacent legal target." };
  }
  return { ok: true, entity, cost };
}

export function executeEncounterAction(state, actor, action) {
  const validation = validateEncounterAction(state, actor, action);
  if (!validation.ok) {
    recordEvent(state, "action_executed", { actionType: action?.type || "unknown", reason: validation.message, actorRole: actor.role }, { rejected: true, stateChanging: false });
    pushMessage(state, validation.message, "warn");
    return validation;
  }
  const encounter = state.activeEncounter;
  const entity = validation.entity;
  const cost = validation.cost;
  recordEvent(state, "action_executed", { encounterId: encounter.encounterId, actionType: action.type, entityId: entity.id, controller: actor.role, source: action.source || actor.source || "manual", cost });
  recordEncounterEvent(state, "action_executed", { actionType: action.type, entityId: entity.id, controller: actor.role, source: action.source || actor.source || "manual", cost });

  if (action.type === "inspect") {
    recordEncounterEvent(state, "interaction", { entityId: entity.id, interaction: "inspect", cost: 0 });
    recordEvent(state, "interaction", { encounterId: encounter.encounterId, entityId: entity.id, interaction: "inspect", cost: 0 });
    return { ok: true, entity };
  }

  if (action.type === "move") {
    const direction = DIRECTIONS[action.direction];
    const from = { x: entity.x, y: entity.y };
    entity.x += direction.dx;
    entity.y += direction.dy;
    recordEncounterEvent(state, "movement", { entityId: entity.id, from, to: { x: entity.x, y: entity.y }, cost, controller: actor.role });
    recordEvent(state, "movement", { encounterId: encounter.encounterId, entityId: entity.id, from, to: { x: entity.x, y: entity.y }, cost, controller: actor.role });
    spendTime(state, entity, cost, "move");
  } else if (action.type === "basic_attack") {
    const target = chooseAttackTarget(state, entity, action.targetId);
    const defense = target.defense + (target.defending ? 1 : 0);
    const damage = Math.max(1, entity.attack - defense);
    const hpBefore = target.hp;
    target.hp = Math.max(0, target.hp - damage);
    target.defending = false;
    const defeatedNow = target.hp === 0 && !target.defeated;
    target.defeated = target.hp === 0;
    const payload = {
      attackerId: entity.id,
      targetId: target.id,
      damage,
      hpBefore,
      hpAfter: target.hp,
      defeatedAfter: target.defeated,
      formula: "damage = max(1, attack - defense)"
    };
    recordEncounterEvent(state, "attack", payload);
    recordEvent(state, "attack", { encounterId: encounter.encounterId, ...payload });
    spendTime(state, entity, cost, "basic_attack");
    if (defeatedNow) {
      recordEncounterEvent(state, "entity_defeated", { entityId: target.id, byEntityId: entity.id });
      recordEvent(state, "entity_defeated", { encounterId: encounter.encounterId, entityId: target.id, byEntityId: entity.id });
    }
  } else if (action.type === "defend") {
    entity.defending = true;
    recordEncounterEvent(state, "defend", { entityId: entity.id, cost });
    recordEvent(state, "defend", { encounterId: encounter.encounterId, entityId: entity.id, cost });
    spendTime(state, entity, cost, "defend");
  } else if (action.type === "interact") {
    recordEncounterEvent(state, "interaction", { entityId: entity.id, interaction: "simple", cost });
    recordEvent(state, "interaction", { encounterId: encounter.encounterId, entityId: entity.id, interaction: "simple", cost });
    spendTime(state, entity, cost, "interact");
  } else if (action.type === "wait") {
    spendTime(state, entity, remainingTime(entity, encounter), "wait");
  }

  checkEncounterCompletion(state);
  if (encounter.status === "active" && remainingTime(entity, encounter) <= 0) advanceActivation(state);
  return { ok: true, entity };
}

export function executeQueuedActionForActive(state) {
  const encounter = state.activeEncounter;
  const entity = activeCombatant(state);
  if (!encounter || !entity) return { ok: false, message: "No active combatant." };
  const index = encounter.pendingCommanderActions.findIndex((item) => item.entityId === entity.id);
  if (index < 0) return { ok: false, message: "No queued action for active combatant." };
  const [queued] = encounter.pendingCommanderActions.splice(index, 1);
  return executeEncounterAction(state, { role: "gm", source: queued.source }, { ...queued.action, entityId: entity.id, source: queued.source, orderId: queued.orderId });
}

export function actionCost(encounter, action) {
  if (!encounter) return 0;
  if (action.type === "move") return encounter.timeCosts.move_one_cell;
  if (action.type === "basic_attack") return encounter.timeCosts.basic_attack;
  if (action.type === "defend") return encounter.timeCosts.defend;
  if (action.type === "interact") return encounter.timeCosts.simple_interaction;
  if (action.type === "inspect") return encounter.timeCosts.inspect;
  if (action.type === "wait") return 0;
  return 0;
}

export function remainingTime(entity, encounter) {
  return Math.max(0, encounter.timeAllowance - entity.timeSpent);
}

function spendTime(state, entity, seconds, reason) {
  const encounter = state.activeEncounter;
  const before = entity.timeSpent;
  entity.timeSpent = Math.min(encounter.timeAllowance, entity.timeSpent + seconds);
  const payload = {
    entityId: entity.id,
    reason,
    seconds,
    spentBefore: before,
    spentAfter: entity.timeSpent,
    remainingAfter: remainingTime(entity, encounter)
  };
  recordEncounterEvent(state, "time_spent", payload);
  recordEvent(state, "time_spent", { encounterId: encounter.encounterId, ...payload });
}

export function advanceActivation(state) {
  const encounter = state.activeEncounter;
  const livingIds = encounter.turnOrder.filter((id) => {
    const entity = encounter.combatants.find((item) => item.id === id);
    return entity && !entity.defeated;
  });
  if (livingIds.length === 0) return;

  let nextIndex = encounter.activeTurnIndex;
  let wrapped = false;
  for (let attempt = 0; attempt < encounter.turnOrder.length; attempt += 1) {
    nextIndex = (nextIndex + 1) % encounter.turnOrder.length;
    if (nextIndex === 0) wrapped = true;
    const candidate = encounter.combatants.find((item) => item.id === encounter.turnOrder[nextIndex]);
    if (candidate && !candidate.defeated) break;
  }
  const active = encounter.combatants.find((item) => item.id === encounter.turnOrder[nextIndex]);
  if (!active) return;
  encounter.activeTurnIndex = nextIndex;
  encounter.activeEntityId = active.id;
  active.timeSpent = 0;
  active.defending = false;
  if (wrapped) {
    const previousRound = encounter.round;
    encounter.round += 1;
    encounter.combatants.forEach((entity) => {
      entity.timeSpent = 0;
      entity.defending = false;
    });
    recordEncounterEvent(state, "round_ended", { previousRound, nextRound: encounter.round, nextActiveTurnIndex: nextIndex, nextActiveEntityId: active.id });
    recordEvent(state, "round_ended", { encounterId: encounter.encounterId, previousRound, nextRound: encounter.round, nextActiveTurnIndex: nextIndex, nextActiveEntityId: active.id });
  } else {
    recordEncounterEvent(state, "activation_advanced", { nextActiveTurnIndex: nextIndex, nextActiveEntityId: active.id });
  }
}

export function canCombatantMoveTo(state, entity, x, y) {
  const encounter = state.activeEncounter;
  const map = state.maps[encounter.battleMapId];
  if (x < 0 || y < 0 || x >= map.width || y >= map.height) return false;
  const terrain = map.terrain?.overrides?.find((item) => item.x === x && item.y === y)?.definitionId || map.terrain?.default || "floor";
  if (state.tileDefinitions[terrain]?.blocked) return false;
  const blocker = map.placedTiles.find((tile) => tile.blocked && x >= tile.x && y >= tile.y && x < tile.x + tile.width && y < tile.y + tile.height);
  if (blocker) return false;
  const occupied = encounter.combatants.find((item) => !item.defeated && item.id !== entity.id && item.x === x && item.y === y);
  return !occupied;
}

export function chooseAttackTarget(state, entity, requestedTargetId = null) {
  const enemies = livingCombatants(state, entity.faction === "players" ? "monsters" : "players")
    .filter((target) => manhattan(entity, target) === 1)
    .sort((a, b) => a.hp - b.hp || a.id.localeCompare(b.id));
  if (requestedTargetId) {
    return enemies.find((target) => target.id === requestedTargetId) || null;
  }
  return enemies[0] || null;
}

export function nearestEnemy(state, entity) {
  return livingCombatants(state, entity.faction === "players" ? "monsters" : "players")
    .map((target) => ({ target, distance: manhattan(entity, target) }))
    .sort((a, b) => a.distance - b.distance || a.target.id.localeCompare(b.target.id))[0]?.target || null;
}

export function bestStepToward(state, entity, target) {
  const candidates = [
    { direction: "right", dx: 1, dy: 0 },
    { direction: "left", dx: -1, dy: 0 },
    { direction: "down", dx: 0, dy: 1 },
    { direction: "up", dx: 0, dy: -1 }
  ]
    .map((step) => ({ ...step, x: entity.x + step.dx, y: entity.y + step.dy }))
    .filter((step) => canCombatantMoveTo(state, entity, step.x, step.y))
    .map((step) => ({ ...step, distance: Math.abs(step.x - target.x) + Math.abs(step.y - target.y) }))
    .sort((a, b) => a.distance - b.distance || a.direction.localeCompare(b.direction));
  return candidates[0] || null;
}

function manhattan(a, b) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

function checkEncounterCompletion(state) {
  const encounter = state.activeEncounter;
  const playersAlive = livingCombatants(state, "players").length;
  const monstersAlive = livingCombatants(state, "monsters").length;
  if (playersAlive && monstersAlive) return;
  encounter.status = "completed";
  encounter.winner = playersAlive ? "players" : "monsters";
  recordEncounterEvent(state, "encounter_completed", { winner: encounter.winner });
  recordEvent(state, "encounter_completed", { encounterId: encounter.encounterId, winner: encounter.winner });
  saveReplayFromEncounter(state);
}

export function saveReplayFromEncounter(state) {
  const encounter = state.activeEncounter;
  if (!encounter || encounter.finalReplayId) return null;
  const replay = createReplayRecord({
    encounterState: encounter,
    mapPath: state.explorationBeforeEncounter?.mapPath || getMapPath(state),
    replayId: `replay-${encounter.encounterId}-${state.nextEventSeq}`
  });
  encounter.finalReplayId = replay.replayId;
  state.replays.push(replay);
  state.replay.selectedReplayId = replay.replayId;
  recordEvent(state, "replay_saved", { replayId: replay.replayId, finalStateHash: replay.finalStateHash, integrityHash: replay.integrityHash });
  return replay;
}

export function autoResolveEncounterToEnd(state, maxSteps = 240) {
  let steps = 0;
  while (state.activeEncounter?.status === "active" && steps < maxSteps) {
    const entity = activeCombatant(state);
    if (!entity) break;
    if (entity.defeated) {
      advanceActivation(state);
      steps += 1;
      continue;
    }
    const queued = state.activeEncounter.pendingCommanderActions.find((item) => item.entityId === entity.id);
    if (entity.controller === "gm" && queued) {
      executeQueuedActionForActive(state);
      if (state.activeEncounter?.status !== "active") break;
      if (activeCombatant(state)?.id === entity.id && remainingTime(entity, state.activeEncounter) > 0) {
        executeEncounterAction(state, { role: "gm" }, chooseDeterministicAction(state, entity));
      }
    } else {
      const actor = entity.controller === "player" ? { role: "player", playerId: entity.assignedPlayerId } : { role: "gm" };
      executeEncounterAction(state, actor, chooseDeterministicAction(state, entity));
    }
    steps += 1;
  }
  return {
    ok: state.activeEncounter?.status === "completed",
    steps,
    finalHash: state.activeEncounter ? stableHash(comparableEncounterState(state.activeEncounter)) : null
  };
}

function chooseDeterministicAction(state, entity) {
  const encounter = state.activeEncounter;
  const adjacent = chooseAttackTarget(state, entity);
  if (adjacent && remainingTime(entity, encounter) >= encounter.timeCosts.basic_attack) {
    return { type: "basic_attack", entityId: entity.id, targetId: adjacent.id };
  }
  const target = nearestEnemy(state, entity);
  const step = target ? bestStepToward(state, entity, target) : null;
  if (step && remainingTime(entity, encounter) >= encounter.timeCosts.move_one_cell) {
    return { type: "move", entityId: entity.id, direction: step.direction };
  }
  if (remainingTime(entity, encounter) >= encounter.timeCosts.defend && entity.faction === "monsters") {
    return { type: "defend", entityId: entity.id };
  }
  return { type: "wait", entityId: entity.id };
}

export function exitEncounterToMap(state) {
  if (state.activeEncounter?.status === "completed" && !state.activeEncounter.finalReplayId) {
    saveReplayFromEncounter(state);
  }
  restoreExplorationAfterEncounter(state);
}
