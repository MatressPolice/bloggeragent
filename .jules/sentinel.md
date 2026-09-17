## 2026-09-16 - [Missing Security Headers]
**Vulnerability:** The application was missing basic security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and `Strict-Transport-Security`.
**Learning:** These headers provide a baseline of defense against MIME sniffing, clickjacking, and XSS attacks. The default setup of FastAPI doesn't enforce these, so they must be added manually.
**Prevention:** Always add a middleware to include baseline HTTP security headers for web applications to enforce defense in depth.

## 2026-09-17 - [Add input length limits to blog topic form]
**Vulnerability:** The `#topicInput` field in the frontend application lacked a length restriction, making it possible to submit excessively large strings which could cause DoS (Denial of Service) conditions by overwhelming backend processing or LLM token capacities.
**Learning:** Even client-facing forms in low-stakes applications need strictly bounded input parameters to guarantee stable resource utilization.
**Prevention:** Always define a `maxlength` HTML attribute on text inputs and enforce identical bounds within JavaScript form submission handlers as a defense-in-depth measure.
