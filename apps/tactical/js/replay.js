import { deepClone } from "./state.js";

export const REPLAY_SCHEMA_VERSION = "shaelvien.replay.v1";

export function stableStringify(value) {
  return JSON.stringify(sortStable(value));
}

function sortStable(value) {
  if (Array.isArray(value)) return value.map(sortStable);
  if (value && typeof value === "object") {
    return Object.keys(value)
      .filter((key) => !["animation", "accumulator", "presentation"].includes(key))
      .sort()
      .reduce((acc, key) => {
        acc[key] = sortStable(value[key]);
        return acc;
      }, {});
  }
  return value;
}

export function stableHash(value) {
  const text = stableStringify(value);
  let hash = 0x811c9dc5;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

export function comparableEncounterState(encounterState) {
  if (!encounterState) return null;
  return {
    encounterId: encounterState.encounterId,
    territoryId: encounterState.territoryId,
    battleMapId: encounterState.battleMapId,
    round: encounterState.round,
    status: encounterState.status,
    winner: encounterState.winner,
    activeEntityId: encounterState.activeEntityId,
    activeTurnIndex: encounterState.activeTurnIndex,
    combatants: encounterState.combatants
      .map((entity) => ({
        id: entity.id,
        faction: entity.faction,
        x: entity.x,
        y: entity.y,
        hp: entity.hp,
        maxHp: entity.maxHp,
        defeated: entity.defeated,
        defending: entity.defending,
        timeSpent: entity.timeSpent
      }))
      .sort((a, b) => a.id.localeCompare(b.id)),
    pendingCommanderActions: encounterState.pendingCommanderActions.map((item) => ({
      entityId: item.entityId,
      orderId: item.orderId,
      source: item.source,
      type: item.action.type
    }))
  };
}

export function createReplayRecord({ encounterState, mapPath, replayId }) {
  const finalState = comparableEncounterState(encounterState);
  const orderedEvents = encounterState.events.map((event) => deepClone(event));
  const replay = {
    schemaVersion: REPLAY_SCHEMA_VERSION,
    rulesVersion: encounterState.rulesVersion,
    replayId,
    mapPath: deepClone(mapPath),
    territoryId: encounterState.territoryId,
    encounterId: encounterState.encounterId,
    initialState: deepClone(encounterState.initialState),
    orderedEvents,
    resolvedRandomValues: [],
    finalState,
    finalStateHash: stableHash(finalState),
    integrityHash: ""
  };
  replay.integrityHash = stableHash({
    schemaVersion: replay.schemaVersion,
    rulesVersion: replay.rulesVersion,
    replayId: replay.replayId,
    mapPath: replay.mapPath,
    territoryId: replay.territoryId,
    encounterId: replay.encounterId,
    initialState: replay.initialState,
    orderedEvents: replay.orderedEvents,
    resolvedRandomValues: replay.resolvedRandomValues,
    finalStateHash: replay.finalStateHash
  });
  return replay;
}

export function rebuildEncounterState(replay, eventLimit = replay.orderedEvents.length) {
  const rebuilt = deepClone(replay.initialState);
  rebuilt.events = [];
  const events = replay.orderedEvents.slice(0, eventLimit);
  events.forEach((event) => {
    rebuilt.events.push(deepClone(event));
    applyReplayEvent(rebuilt, event);
  });
  return rebuilt;
}

function applyReplayEvent(encounter, event) {
  const payload = event.payload || {};
  if (event.type === "commander_action_generated") {
    encounter.pendingCommanderActions.push(deepClone(payload.queuedAction));
    return;
  }
  if (event.type === "action_executed") {
    if (payload.source === "commander" || payload.source === "direct_gm") {
      encounter.pendingCommanderActions = encounter.pendingCommanderActions.filter((item) => item.entityId !== payload.entityId);
    }
    return;
  }
  if (event.type === "direct_gm_override") {
    encounter.pendingCommanderActions = encounter.pendingCommanderActions.filter((item) => item.entityId !== payload.entityId);
    if (payload.queuedAction) encounter.pendingCommanderActions.push(deepClone(payload.queuedAction));
    return;
  }
  if (event.type === "movement") {
    const entity = encounter.combatants.find((item) => item.id === payload.entityId);
    if (entity) {
      entity.x = payload.to.x;
      entity.y = payload.to.y;
    }
    return;
  }
  if (event.type === "attack") {
    const target = encounter.combatants.find((item) => item.id === payload.targetId);
    if (target) {
      target.hp = payload.hpAfter;
      target.defeated = payload.defeatedAfter;
      target.defending = false;
    }
    return;
  }
  if (event.type === "defend") {
    const entity = encounter.combatants.find((item) => item.id === payload.entityId);
    if (entity) entity.defending = true;
    return;
  }
  if (event.type === "interaction") {
    encounter.lastInteraction = payload;
    return;
  }
  if (event.type === "time_spent") {
    const entity = encounter.combatants.find((item) => item.id === payload.entityId);
    if (entity) entity.timeSpent = payload.spentAfter;
    return;
  }
  if (event.type === "round_ended") {
    encounter.round = payload.nextRound;
    encounter.activeTurnIndex = payload.nextActiveTurnIndex;
    encounter.activeEntityId = payload.nextActiveEntityId;
    encounter.combatants.forEach((entity) => {
      entity.timeSpent = 0;
      entity.defending = false;
    });
    return;
  }
  if (event.type === "activation_advanced") {
    encounter.activeTurnIndex = payload.nextActiveTurnIndex;
    encounter.activeEntityId = payload.nextActiveEntityId;
    const active = encounter.combatants.find((item) => item.id === payload.nextActiveEntityId);
    if (active) {
      active.timeSpent = 0;
      active.defending = false;
    }
    return;
  }
  if (event.type === "entity_defeated") {
    const entity = encounter.combatants.find((item) => item.id === payload.entityId);
    if (entity) {
      entity.hp = 0;
      entity.defeated = true;
    }
    return;
  }
  if (event.type === "encounter_completed") {
    encounter.status = "completed";
    encounter.winner = payload.winner;
  }
}

export function verifyReplayRecord(replay, liveEncounterSnapshot) {
  const rebuiltOnce = rebuildEncounterState(replay);
  const rebuiltTwice = rebuildEncounterState(replay);
  const rebuiltFinal = comparableEncounterState(rebuiltOnce);
  const rebuiltHash = stableHash(rebuiltFinal);
  const repeatHash = stableHash(comparableEncounterState(rebuiltTwice));
  const beforeHash = stableHash(liveEncounterSnapshot);
  const afterHash = stableHash(liveEncounterSnapshot);
  return {
    finalStateHashMatches: rebuiltHash === replay.finalStateHash,
    repeatHashMatches: repeatHash === rebuiltHash,
    replayDoesNotMutateLiveState: beforeHash === afterHash,
    rebuiltHash,
    repeatHash,
    liveHash: stableHash(liveEncounterSnapshot)
  };
}

export function replayRounds(replay) {
  const rounds = [{ round: 1, index: 0 }];
  replay.orderedEvents.forEach((event, index) => {
    if (event.type === "round_ended") {
      rounds.push({ round: event.payload.nextRound, index: index + 1 });
    }
  });
  return rounds;
}
