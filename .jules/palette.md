## 2023-10-01 - Preserve accessibility attributes on dynamic elements
**Learning:** When dynamically updating the text content of a UI element that contains purely decorative emojis or icons, using `.textContent` overwrites any child elements like `<span aria-hidden="true">`.
**Action:** Use `.innerHTML` instead of `.textContent` to preserve essential accessibility attributes like `aria-hidden="true"` when swapping decorative icons.
