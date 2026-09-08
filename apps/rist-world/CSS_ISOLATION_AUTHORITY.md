# CSS Isolation Authority

Blazor component-scoped styles in `*.razor.css` are emitted into the generated `RistWorld.styles.css` bundle during publish.

`wwwroot/index.html` must load `RistWorld.styles.css` explicitly. Without that link, components still render but fall back to browser/default/global styling, producing oversized white buttons, blue link-like text, collapsed spacing, and broken mobile composition.

Release gates should verify both:

- source `index.html` references `RistWorld.styles.css`
- published `build/rist/wwwroot/RistWorld.styles.css` exists

Do not replace component-scoped CSS with duplicate global CSS as a workaround.