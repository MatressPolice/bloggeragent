## 2024-09-15 - Global Scope for Keyboard Shortcuts
**Learning:** When adding keyboard shortcut hints (like "Ctrl ↵") to a submit button, users expect those shortcuts to work globally across the view. If the `keydown` event listener is only attached to a specific input field, it creates a "fake affordance" and confusing UX when the user tries to use the shortcut while focused elsewhere.
**Action:** Always ensure that if a keyboard shortcut is visually advertised as a primary action for the page, the corresponding event listener should be bound to the `document` level to make it truly intuitive, unless it's strictly a field-specific interaction.

## 2026-09-16 - Global Keyboard Shortcuts
**Learning:** Global keyboard shortcuts (like Ctrl+Enter to submit) should be attached to the `document` rather than a specific input field. This prevents user frustration when trying to use a shortcut while focus has unintentionally shifted away from the input.
**Action:** Always attach application-wide keyboard shortcuts to the document object, especially for core actions like primary form submission, ensuring the shortcut remains intuitive and functional regardless of focus state.

## 2024-09-17 - Visual Cues for Disabled Inputs
**Learning:** When a form or specific input field is disabled during background processing (like data generation), leaving it visually identical to its enabled state causes confusion. Users may perceive the app as frozen or broken. Adding clear styling (e.g. reduced opacity, `not-allowed` cursor, dim background) directly addresses this.
**Action:** Always ensure that dynamically disabled interactive elements, especially inputs used in asynchronous submission flows, have an explicit `:disabled` CSS state to provide immediate visual feedback.
## 2026-09-18 - Autofocus on Primary Input
**Learning:** Automatically focusing the primary input field on a single-purpose page reduces friction and improves the overall user experience.
**Action:** Use the `autofocus` HTML attribute on primary input fields where the immediate user action is expected to be text entry.

## 2026-10-27 - Dynamic ARIA Labels and Inline Feedback
**Learning:** Bounded inputs (with maxlength) lacking visual feedback create anxiety for users. Simply truncating their typing without a cue is bad UX. Furthermore, icon-only buttons that toggle states (like a theme toggle) often fail accessibility checks if they only use static labels (e.g. "Toggle theme").
**Action:** Always provide inline, real-time character counters for inputs with enforced length limits so users can adjust behavior before errors. Always use dynamic `aria-label` attributes for toggle buttons that accurately describe the *action* (e.g., "Switch to light theme") instead of describing the generic purpose.
