## 2024-05-14 - [Avoid `asyncio.to_thread` overhead for frequent static file checks]
**Learning:** `asyncio.to_thread` introduces overhead due to thread dispatch context switching. For a very frequent path resolution in FastAPI middleware (like checking `os.path.isfile` for every request path against a frontend directory), this can add a measurable penalty (around 0.2ms per request).
**Action:** When performing file path validation (e.g. `os.path.abspath` or `os.path.isfile`) in hot paths like HTTP middleware, memoize the results using an in-memory dictionary cache to prevent redundant thread dispatch and disk I/O. Make sure to set a cache size limit and clear it appropriately to prevent memory leaks.

## 2026-09-16 - Bounded in-memory cache for static files
**Learning:** In asynchronous FastAPI applications, memoize highly frequent path validations in middleware using a bounded in-memory dictionary cache to prevent redundant disk I/O and context switching from thread dispatch overhead.
**Action:** Use a module-level dictionary to cache os.path.isfile results in high-throughput middleware, clearing it if it grows too large.
