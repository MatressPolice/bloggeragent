## 2026-09-16 - Bounded in-memory cache for static files
**Learning:** In asynchronous FastAPI applications, memoize highly frequent path validations in middleware using a bounded in-memory dictionary cache to prevent redundant disk I/O and context switching from thread dispatch overhead.
**Action:** Use a module-level dictionary to cache os.path.isfile results in high-throughput middleware, clearing it if it grows too large.
