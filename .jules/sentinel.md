## 2026-10-03 - URL-encoded Path Traversal Bypass
**Vulnerability:** Attackers could bypass path-based security blocks (e.g. `startswith`) or the `os.path.realpath` check by URL-encoding characters like `%2E%2E%2F` (../) in API requests. FastAPIs raw path does not automatically normalize encoded payloads.
**Learning:** URL-encoded strings remain encoded in the `scope['path']` raw property. Any validation using strings or `os.path.realpath` directly on the raw string fails to catch directory traversal if it isn't URL-decoded first.
**Prevention:** Always decode paths using `urllib.parse.unquote` before applying path normalizations or verifying prefixes.
