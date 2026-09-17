import os
import asyncio
import secrets
import posixpath
from urllib.parse import unquote
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

API_KEY = os.getenv("API_KEY")

# Point to the directory containing your agent package
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(AGENT_DIR, "frontend")
FRONTEND_DIR_EXISTS = os.path.isdir(FRONTEND_DIR)
FRONTEND_DIR_ABSPATH_PREFIX = os.path.abspath(FRONTEND_DIR) + os.path.sep

# Create the ADK FastAPI app with agent discovery
# We pass specific allowed origins directly to get_fast_api_app so the ADK's built-in CORS
# and OriginCheckMiddleware properly accept the frontend's cross-origin requests.
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allow_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app = get_fast_api_app(
    agents_dir=AGENT_DIR, 
    web=False,
    allow_origins=allow_origins
)

# Public endpoints that do not require authentication
PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health", "/version"}

# Cache for static file validation to avoid thread dispatch and disk I/O overhead
_STATIC_CACHE = {}
_MAX_CACHE_SIZE = 1000

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Allow OPTIONS preflight requests to pass through
    if request.method == "OPTIONS":
        return await call_next(request)

    norm_path = posixpath.normpath(unquote(request.url.path))
    if norm_path.startswith("//"):
        norm_path = "/" + norm_path.lstrip("/")

    # If this route is meant to be public, skip auth
    if norm_path in PUBLIC_PATHS:
        return await call_next(request)

    # Check if it's a valid static file in the frontend directory
    if FRONTEND_DIR_EXISTS:
        is_static = _STATIC_CACHE.get(norm_path)
        if is_static is None:
            file_path = os.path.join(FRONTEND_DIR, norm_path.lstrip("/"))
            is_static = os.path.abspath(file_path).startswith(FRONTEND_DIR_ABSPATH_PREFIX) and await asyncio.to_thread(os.path.isfile, file_path)

            if len(_STATIC_CACHE) >= _MAX_CACHE_SIZE:
                _STATIC_CACHE.clear()
            _STATIC_CACHE[norm_path] = is_static

        if is_static:
            return await call_next(request)

    # Anything else requires authentication (default-deny policy)

    api_key = API_KEY
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "API_KEY environment variable is not set. The server is secured by default."}
        )

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header[7:]
    if not secrets.compare_digest(token, api_key):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)

# Serve the web interface directly from the Cloud Run container
if FRONTEND_DIR_EXISTS:
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def no_frontend():
        return {"detail": "frontend dir not found", "cwd": os.getcwd(), "files": os.listdir(AGENT_DIR)}