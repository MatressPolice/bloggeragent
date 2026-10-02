## 2026-09-16 - [Missing Security Headers]
**Vulnerability:** The application was missing basic security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, and `Strict-Transport-Security`.
**Learning:** These headers provide a baseline of defense against MIME sniffing, clickjacking, and XSS attacks. The default setup of FastAPI doesn't enforce these, so they must be added manually.
**Prevention:** Always add a middleware to include baseline HTTP security headers for web applications to enforce defense in depth.

## 2026-09-17 - [Add input length limits to blog topic form]
**Vulnerability:** The `#topicInput` field in the frontend application lacked a length restriction, making it possible to submit excessively large strings which could cause DoS (Denial of Service) conditions by overwhelming backend processing or LLM token capacities.
**Learning:** Even client-facing forms in low-stakes applications need strictly bounded input parameters to guarantee stable resource utilization.
**Prevention:** Always define a `maxlength` HTML attribute on text inputs and enforce identical bounds within JavaScript form submission handlers as a defense-in-depth measure.

## 2026-09-18 - [Fix information disclosure in fallback endpoint]
**Vulnerability:** The `no_frontend` fallback endpoint returned `cwd` and `files` which exposed internal server directory structures (`os.getcwd()` and `os.listdir(AGENT_DIR)`). This kind of information leakage can aid attackers in reconnaissance and path traversal exploits.
**Learning:** Fallback endpoints or debug messages left in production can easily leak sensitive internal details (like file paths and directory listings) to unauthorized users.
**Prevention:** Avoid returning internal filesystem paths, directory structures, or detailed stack traces in API responses, especially in default or fallback endpoints.

## 2026-09-19 - [Missing Content-Security-Policy Header]
**Vulnerability:** The application was missing a Content-Security-Policy (CSP) header, which could allow malicious scripts to be executed or unauthorized resources to be loaded if an XSS vulnerability was present or if a third-party dependency was compromised.
**Learning:** Even if HTML rendering uses DOMPurify and marked.js is considered safe, a defense-in-depth approach is necessary. Missing CSP leaves the application without an extra layer of defense against Cross-Site Scripting (XSS) and data injection attacks.
**Prevention:** Always add a `Content-Security-Policy` header explicitly in API or middleware configuration to restrict external domains and lock down external resource loading (e.g. scripts, styles, fonts) to only trusted sources.
