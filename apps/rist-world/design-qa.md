# Design QA — tiled world and card browser

- Source visual truth: `/workspace/scratch/3589cb8b6e4d/upload/IMG_7398.png` and `/workspace/scratch/3589cb8b6e4d/upload/IMG_7397.png`
- Implementation: https://ryanlcole.github.io/DicePage/app/?qa=landscape-workspace-3
- Browser-rendered implementation screenshot: cloud-browser capture emitted during QA (1363 × 930 px)
- Source pixels: 750 × 1334 px each
- CSS viewport: 1363 × 930 (cloud QA); source was an iPhone portrait capture with browser chrome
- Density normalization: layout geometry compared in CSS pixels; browser chrome and orientation mismatch excluded from fidelity findings
- State: tiled Shaelvien world in landscape; Card Library open in logged-out QA session. Authenticated private-card results were not available in the QA browser.

## Full-view comparison evidence

The source showed two actionable regressions: the 20 × 13 world board was stretched to the landscape workspace, and the Card Library's explanatory sentence consumed result space. The revised implementation renders 260 individual tile cells, with a measured map size of 1042 × 677.296875 CSS px (ratio 1.53847, matching 20:13), centered at the largest contained size. The Card Library overlay measures 1042 × 739 CSS px and its header is now 42 px high with only “Card library” visible.

## Focused region evidence

A focused DOM/geometry check confirmed:
- 260 `.tile-cell` elements are present.
- The world board ratio is 20:13, so each 5% × 7.692307% cell is square.
- The former “Search private cards, create cards…” description is absent.
- The Card Library header remains visible and tappable.
- The mobile spellbook area is reduced to a 62 px bottom dock, reserving the remaining workspace for cards.

## Required fidelity surfaces

- Typography: existing Shaelvien type hierarchy and gold/cream weights are preserved; only redundant helper copy was removed.
- Spacing/layout rhythm: the world board is contained and centered without deformation; the card header is compact and the mobile workspace prioritizes results.
- Colors/tokens: no palette, border, or semantic-color changes.
- Image quality/assets: the world is still composed of its 260 source tiles; no screenshot fallback or stretched replacement asset is used.
- Copy/content: the requested top description was removed; the title and accessible control labels remain.

## Comparison history

1. Earlier P1 — landscape world distortion.
   - Evidence: the final landscape override forced `.map` to `width:100%; height:100%; aspect-ratio:auto`.
   - Fix: restored 20:13 geometry and used container-relative sizing to fit the largest undistorted board.
   - Post-fix evidence: measured ratio 1.53847 with 260 rendered tile cells.

2. Earlier P1 — card results hidden below descriptive chrome.
   - Evidence: source screenshot showed the two-line helper sentence above filters and results.
   - Fix: removed the sentence, reduced the header to 42 px, and converted the portrait spellbook pane to a compact bottom dock.
   - Post-fix evidence: old helper copy is absent and the Card Library header remains 42 px.

## Console and interaction checks

- Open Card Library button: passed.
- Card Library open/close rendering: passed.
- New stylesheet cache token loaded: passed.
- Browser console: no application-origin errors; only unrelated browser-extension metadata errors were present.
- Residual test gap: authenticated private-card results could not be exercised in the logged-out cloud QA session.

## Findings

No actionable P0/P1/P2 visual findings remain for the requested changes.

## Follow-up polish

- P3: repeat the portrait check in an authenticated iPhone session to confirm the exact number of visible card rows above the compact spellbook dock.

final result: passed
