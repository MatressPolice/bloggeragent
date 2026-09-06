import os
import secrets
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

# Point to the directory containing your agent package
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create the ADK FastAPI app with agent discovery
# We pass specific allowed origins directly to get_fast_api_app so the ADK's built-in CORS
# and OriginCheckMiddleware properly accept the frontend's cross-origin requests.
app = get_fast_api_app(
    agents_dir=AGENT_DIR, 
    web=False,
    allow_origins=["https://adk-default-service-name-122956929515.us-west1.run.app", "http://localhost:8080"]
)

# Public endpoints that do not require authentication
PUBLIC_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/health", "/version"}

# Prefixes for endpoints that require authentication
AUTH_PREFIXES = ("/run", "/list-apps", "/apps", "/version", "/health")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    # Allow OPTIONS preflight requests to pass through
    if request.method == "OPTIONS":
        return await call_next(request)

    # If this route is meant to be public or is a static file, skip auth
    if request.url.path in PUBLIC_PATHS or not request.url.path.startswith(AUTH_PREFIXES):
        # We assume endpoints that require auth start with one of the ADK prefixes,
        # otherwise we let it pass for static files and frontend routes
        return await call_next(request)

    api_key = os.getenv("API_KEY")
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
frontend_dir = os.path.join(AGENT_DIR, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def no_frontend():
        return {"detail": "frontend dir not found", "cwd": os.getcwd(), "files": os.listdir(AGENT_DIR)}