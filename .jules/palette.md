
## 2024-09-19 - Screen Reader Semantics for Visual Indicators
**Learning:** Purely decorative icons and visually structured progress steppers cause redundant and confusing screen reader announcements if not properly annotated.
**Action:** Always add aria-hidden="true" to purely decorative emojis/icons. Map visual progress steppers to native role="list" and role="listitem" semantics, using aria-current="step" to explicitly indicate the currently active stage.
