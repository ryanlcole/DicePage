# Shaelvien / RIST stacked-Z freeze

Frozen: 2026-09-09 18:42 EDT
Source branch: `live-alpha-rist-blazor-world`
Frozen source commit: `4cb537f60bed7b30b6889fc005c834f889bc00cc`
Source commit message: `Refresh stacked Z viewer scripts`

## Intent preserved at freeze

- Stacking should naturally determine layer ordering rather than unexpectedly moving terrain into a higher tier.
- With Z-lock OFF, the viewer should show the complete stack from above: upper terrain remains visible while lower ice/hills remain visible beneath it.
- Upper/elevated terrain should react subtly to supported phone tilt/parallax.
- Zoom should flow continuously through layers instead of making upper content appear/disappear abruptly.
- Layer and tier navigation each need explicit up/down controls.
- Existing working production behavior must remain recoverable while this experimental stacked-Z viewer is repaired.

## Deployment state at freeze

The source commit was committed but its AWS frontend deployment failed at compile time, so this freeze is a recovery marker for the experimental source state, not a claim that it was successfully deployed.

Known compile blockers from the failed run:
- `Components/WorldBuilderStudio.razor` around line 133: Razor/C# parsing errors involving an `@media (max-width:...)` fragment.
- `Components/WorldBuilderStudio.Persistence.cs` line 52: unresolved `Footprints` reference.
