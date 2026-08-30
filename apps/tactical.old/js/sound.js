import { deepClone, recordEvent } from "./state.js";
import { propagateSound } from "./acoustics.js";

export const SOUND_SCHEMA_VERSION = "shaelvien.sound_event.v1";

export function createSoundEvent(input) {
  const position = input.sourcePosition || { x: Number(input.x) || 0, y: Number(input.y) || 0 };
  return {
    schemaVersion: SOUND_SCHEMA_VERSION,
    soundEventId: input.soundEventId || `sound-${Date.now().toString(36)}`,
    mapId: input.mapId,
    sourceEntityId: input.sourceEntityId || null,
    sourcePosition: deepClone(position),
    intensity: clamp(Number(input.intensity ?? 0.8), 0, 1),
    category: input.category || "environmental",
    description: input.description || "distant sound",
    durationMs: Math.max(100, Math.round(Number(input.durationMs) || 1800)),
    repeatPolicy: input.repeatPolicy || "event_based",
    createdAtEventSeq: input.createdAtEventSeq || null
  };
}

export function emitSoundEvent(state, input, options = {}) {
  const sound = createSoundEvent({ ...input, createdAtEventSeq: state.nextEventSeq });
  state.soundEvents = Array.isArray(state.soundEvents) ? state.soundEvents : [];
  const existingIndex = state.soundEvents.findIndex((item) => item.soundEventId === sound.soundEventId);
  if (existingIndex >= 0) state.soundEvents[existingIndex] = sound;
  else state.soundEvents.push(sound);
  if (options.record !== false) {
    recordEvent(state, "sound_event_emitted", {
      soundEventId: sound.soundEventId,
      mapId: sound.mapId,
      sourcePosition: sound.sourcePosition,
      category: sound.category,
      intensity: sound.intensity
    });
  }
  return sound;
}

export function perceivedSoundsForEntity(state, map, entity, hearingProfile) {
  const sounds = (state.soundEvents || []).filter((sound) => sound.mapId === map.id);
  return sounds
    .map((sound) => propagateSound(state, map, sound, entity, hearingProfile))
    .filter((result) => result.heard);
}

export function soundEventPublicView(perceived) {
  return {
    soundEventId: perceived.soundEventId,
    category: perceived.category,
    description: perceived.description,
    strength: perceived.strength,
    perceivedSound: deepClone(perceived.perceivedSound)
  };
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
