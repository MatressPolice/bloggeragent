import sys
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

def test_no_frontend_endpoint():
    # Mock os.path.isdir to return False for the frontend directory
    # so that the fallback endpoint is registered instead of the static mount.
    with patch("os.path.isdir", return_value=False):
        # We must import main inside the mocked context so the module-level 
        # condition is evaluated with the mocked isdir.
        import main
        # Force reload in case it was already imported
        import importlib
        importlib.reload(main)
        
        client = TestClient(main.app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "frontend dir not found"
        assert "cwd" in data
        assert "files" in data
