import os
from fastapi.staticfiles import StaticFiles
from google.adk.cli.fast_api import get_fast_api_app

# Point to the directory containing your agent package
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Create the ADK FastAPI app with agent discovery
# We pass allow_origins=["*"] directly to get_fast_api_app so the ADK's built-in CORS
# and OriginCheckMiddleware properly accept the frontend's cross-origin requests.
app = get_fast_api_app(
    agents_dir=AGENT_DIR, 
    web=False,
    allow_origins=["*"]
)

# Serve the web interface directly from the Cloud Run container
frontend_dir = os.path.join(AGENT_DIR, "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def no_frontend():
        return {"detail": "frontend dir not found", "cwd": os.getcwd(), "files": os.listdir(AGENT_DIR)}