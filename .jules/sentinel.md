## 2026-09-16 - [Missing Security Headers]
**Vulnerability:** The application was missing basic security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and `Strict-Transport-Security`.
**Learning:** These headers provide a baseline of defense against MIME sniffing, clickjacking, and XSS attacks. The default setup of FastAPI doesn't enforce these, so they must be added manually.
**Prevention:** Always add a middleware to include baseline HTTP security headers for web applications to enforce defense in depth.
