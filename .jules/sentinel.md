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
## 2023-10-24 - [HIGH] Fix authentication bypass in middleware
**Vulnerability:** The FastAPI middleware used `posixpath.normpath(unquote(request.scope.get("path", "")))` for route validation, allowing URL-encoded path traversal (e.g., `/protected%2f..%2fhealth`) to bypass authentication checks by masquerading as public endpoints like `/health`.
**Learning:** The ASGI router processes raw paths differently, preserving URL-encoded characters. Attempting to normalize the path in middleware creates a mismatch with the application router's path resolution, leading to bypass vulnerabilities.
**Prevention:** Always validate using the exact same raw path representation that the ASGI application router receives (`request.scope.get('path', '')`) directly, without custom decoding or normalization.
