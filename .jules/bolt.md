## 2024-05-14 - [Avoid `asyncio.to_thread` overhead for frequent static file checks]
**Learning:** `asyncio.to_thread` introduces overhead due to thread dispatch context switching. For a very frequent path resolution in FastAPI middleware (like checking `os.path.isfile` for every request path against a frontend directory), this can add a measurable penalty (around 0.2ms per request).
**Action:** When performing file path validation (e.g. `os.path.abspath` or `os.path.isfile`) in hot paths like HTTP middleware, memoize the results using an in-memory dictionary cache to prevent redundant thread dispatch and disk I/O. Make sure to set a cache size limit and clear it appropriately to prevent memory leaks.

## 2026-09-16 - Bounded in-memory cache for static files
**Learning:** In asynchronous FastAPI applications, memoize highly frequent path validations in middleware using a bounded in-memory dictionary cache to prevent redundant disk I/O and context switching from thread dispatch overhead.
**Action:** Use a module-level dictionary to cache os.path.isfile results in high-throughput middleware, clearing it if it grows too large.

## 2026-09-16 - Removed redundant isdir check in middleware
**Learning:** Checking `os.path.isdir` during request handling introduces unnecessary I/O and asynchronous thread dispatch overhead (`await asyncio.to_thread`) for a directory structure that is static during application runtime. In local benchmarking, caching this value improved static file middleware routing times by ~52% (from 4.81s to 2.31s per 10k requests).
**Action:** When writing middleware or high-frequency request handlers, calculate and cache static directory existences and paths at the module/initialization level instead of inside the request loop.

## 2026-09-17 - Added GZipMiddleware for static payloads
**Learning:** Large frontend payloads (like the 45KB index.html) served directly from the FastAPI application using StaticFiles are not compressed by default. Adding `GZipMiddleware` allows the application to compress these payloads, reducing memory/bandwidth overhead for clients without needing to configure an external reverse proxy for local testing or simple containerized deployments.
**Action:** When an ASGI application serves moderately large text-based assets directly, evaluate adding built-in compression middleware (like `fastapi.middleware.gzip.GZipMiddleware`) to automatically reduce the payload size if no reverse proxy is handling it.
