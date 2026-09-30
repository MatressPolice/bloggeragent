## 2026-09-30 - Accessible Emojis in Icon-Only Buttons
**Learning:** Dynamically updating `textContent` for decorative emojis in buttons overwrites essential screen reader attributes like `aria-hidden="true"`.
**Action:** Use `.innerHTML` to insert emojis wrapped in `<span aria-hidden="true">` elements when they act as visual decorators inside ARIA-labeled buttons.
