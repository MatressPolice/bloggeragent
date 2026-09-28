## 2024-09-28 - Semantics for progress steppers and emojis
**Learning:** Progress steppers need native `role="list"` and `role="listitem"` semantics with `aria-current="step"` for active states. Furthermore, dynamically updating text content of decorative emojis removes essential `aria-hidden="true"` attributes if `.textContent` is used instead of `.innerHTML`.
**Action:** Always map visual progress to list semantics and use `.innerHTML` with explicit ARIA attributes when updating purely decorative icons dynamically.
