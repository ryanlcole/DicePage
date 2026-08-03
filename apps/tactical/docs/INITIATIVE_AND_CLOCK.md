# Initiative And Clock

The initiative strip is a scene object displayed near the map. It tracks active entry, round, visibility, and turn state.

## Clock

The chess-clock-style timer tracks:

- active turn seconds
- remaining seconds
- paused state
- turn progress

The GM can pause and resume. Advancing initiative resets the clock for the next entry.

## Fade Timer

Cards and clock surfaces may show a visual drain or fade tied to turn progress. Reduced-motion mode replaces motion-heavy cues with stable text and progress values.

Timer presentation is UI state unless campaign rules explicitly make timing authoritative.

