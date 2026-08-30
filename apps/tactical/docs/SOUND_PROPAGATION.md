# Sound Propagation

Milestone: `SHAELVIEN-PERCEPTION-1`

Sound events are authoritative records with source position, intensity, category, description, duration, and repeat policy.

Sound propagation uses a bounded acoustic graph over map cells:

- Open cells have low acoustic cost.
- Open doors and openings are low-cost transitions.
- Closed doors attenuate sound but may transmit it.
- Sealed walls with very low transmission block the first bounded model.
- Total acoustic cost must remain within hearing range.

Player-facing sound markers use perceived location, not true source position. When sound travels through a doorway, the marker appears at the doorway. In open fields, the marker appears near the approximate bearing. Source identity is not exposed unless future rules permit it.

Pulse animation is presentation-only and excluded from replay.

