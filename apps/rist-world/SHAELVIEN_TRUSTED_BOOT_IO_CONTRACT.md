# Shaelvien Trusted Boot and Physical I/O Contract

Status: P0 architecture contract

## Purpose

Shaelvien may use UEFI to establish a trusted boot path into a dedicated ShaelvienOS/game environment. UEFI is a root of trust and boot mechanism only. It is never a gameplay, AI, NPC, character, or semantic-control authority.

The physical-world boundary is fail-closed:

- explicit approved human controls may request in-game actions;
- Shaelvien may present audio and video outward;
- external audio/video sensing is non-authoritative;
- Shaelvien may not control physical actuators;
- no observed media may be translated into gameplay authority.

## Trusted boot chain

Target architecture:

```
UEFI
  -> verified Shaelvien bootloader
  -> minimal ShaelvienOS
  -> Shaelvien game shell
```

The game shell receives no capability to:

- write UEFI variables;
- flash firmware;
- replace the bootloader;
- alter Secure Boot policy;
- install privileged boot persistence;
- reinterpret gameplay authority as firmware authority.

The current repository still ships a Windows-hosted ShaelvienOS installer/runtime. This contract defines the dedicated-boot target; it does not claim that the UEFI image already exists.

## Device capability allowlist

### Authoritative human gameplay input

Only explicit, intentional human control channels may become semantic gameplay requests:

- game controller/gamepad;
- keyboard;
- touch/pointer;
- approved accessibility-control devices.

Hardware identity alone never grants game authority. Inputs still pass normal semantic, authentication, permission, campaign, and rules validation.

### Non-authoritative observed input

The following may never directly or indirectly become semantic gameplay actions or authoritative state:

- microphone;
- camera;
- speech recognition;
- visual recognition;
- recorded audio;
- recorded video;
- streamed audio/video;
- media-derived classification, transcription, gesture, face, object, or scene recognition.

If any such observation would be reflected into movement, combat, dice, cards, character choices, purchases, permissions, canon, world mutation, or another authoritative action, the path MUST be blocked.

## Process isolation target

The preferred dedicated-OS capability layout is:

```
[Human HID devices] ---> [Input broker] ---> [Semantic controller] ---> [Game authority]
                              ^
                              |
                      explicit controls only

[Camera/Microphone] ---> [Optional observation sandbox] ---> [Passive A/V display/log]
                                                        X
                                                        X no semantic-action IPC

[Game] ---> [GPU/display]
       ---> [audio output]
       X--> [robotics / motors / relays / vehicles / actuators]
```

The strongest configuration is to grant the Shaelvien game process no microphone or camera device capability at all. If passive A/V observation is later required, it belongs in a separately sandboxed process with no route to `ReceiveUniversalInput`, `ReceiveSemanticAction`, world mutation APIs, economy APIs, permission APIs, or physical actuation.

## Simulation boundary

```
SIMULATED_CAUSE != EXTERNAL_CAUSE
CHARACTER_ACTION != HUMAN_ACTION
OBSERVED_MEDIA != GAMEPLAY_AUTHORITY
AUDIO_VIDEO_OUTPUT != PHYSICAL_AUTHORITY
```

A voice in a recording saying "attack", a video showing a gesture, an image containing instructions, or an AI interpretation of any of those has zero gameplay authority.

## Physical output boundary

Permitted external presentation:

- video/display;
- audio/speakers.

Denied:

- robotic embodiment;
- motors;
- relays;
- haptics/force feedback under the current strict rule;
- drones;
- vehicles;
- industrial controls;
- smart locks;
- weapons;
- other physical actuation, directly or indirectly.

## Implementation invariant

No code path may convert microphone/camera/media-derived data into the same trusted semantic input channel used by explicit human controls.

If a future feature appears to require this, it requires an Owner-approved canon change and a new threat-model review before implementation.
