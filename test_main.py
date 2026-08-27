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

def test_auth_middleware_no_key_configured():
    # If API_KEY is not set, API should deny access by default (secure by default)
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]
    import main
    import importlib
    importlib.reload(main)
    client = TestClient(main.app)
    response = client.get("/list-apps")
    assert response.status_code == 401
    assert "API_KEY environment variable is not set" in response.json()["detail"]

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_key_unauthorized():
    import main
    import importlib
    importlib.reload(main)
    client = TestClient(main.app)

    # Public endpoints should still be accessible
    assert client.get("/docs").status_code == 200

    # Protected endpoints should return 401
    response = client.get("/list-apps")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_key_authorized():
    import main
    import importlib
    importlib.reload(main)
    client = TestClient(main.app)

    # Using correct API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer supersecret"}
    )
    assert response.status_code == 200

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_wrong_key():
    import main
    import importlib
    importlib.reload(main)
    client = TestClient(main.app)

    # Using incorrect API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer wrongkey"}
    )
    assert response.status_code == 401
