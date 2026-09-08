import os
from unittest.mock import patch
from fastapi.testclient import TestClient

import tempfile

def get_client():
    import main
    import importlib
    importlib.reload(main)
    return TestClient(main.app)

def test_frontend_static_mount():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy frontend directory and index.html inside the tmpdir
        frontend_dir = os.path.join(tmpdir, "frontend")
        os.makedirs(frontend_dir)
        with open(os.path.join(frontend_dir, "index.html"), "w") as f:
            f.write("<html><body>Mocked Frontend</body></html>")

        # Patch os.path.abspath so that main.AGENT_DIR becomes tmpdir without changing signature
        real_abspath = os.path.abspath
        def mock_abspath(path):
            if path.endswith("main.py"):
                return os.path.join(tmpdir, "main.py")
            return real_abspath(path)

        with patch("os.path.abspath", side_effect=mock_abspath):
            client = get_client()
            response = client.get("/")

            assert response.status_code == 200
            assert "Mocked Frontend" in response.text

def test_no_frontend_endpoint():
    # Mock os.path.isdir to return False for the frontend directory
    # so that the fallback endpoint is registered instead of the static mount.
    with patch("os.path.isdir", return_value=False):
        client = get_client()
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
    client = get_client()
    response = client.get("/list-apps")
    assert response.status_code == 401
    assert "API_KEY environment variable is not set" in response.json()["detail"]

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_key_unauthorized():
    client = get_client()

    # Public endpoints should still be accessible
    assert client.get("/docs").status_code == 200

    # Protected endpoints should return 401
    response = client.get("/list-apps")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_key_authorized():
    client = get_client()

    # Using correct API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer supersecret"}
    )
    assert response.status_code == 200

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_wrong_key():
    client = get_client()

    # Using incorrect API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer wrongkey"}
    )
    assert response.status_code == 401

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_invalid_header_format():
    client = get_client()

    # Missing "Bearer " prefix (Basic)
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Basic supersecret"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

    # Missing prefix entirely
    response = client.get(
        "/list-apps",
        headers={"Authorization": "supersecret"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_bypass_attempts():
    client = get_client()

    # Attempting bypass using path traversal, url encoding, or extra slashes
    bypass_paths = [
        "/%72un",
        "http://testserver//list-apps",
        "/docs/../list-apps",
        "/static/../list-apps",
        "/nonexistent"
    ]
    for path in bypass_paths:
        response = client.get(path)
        assert response.status_code == 401, f"Failed for path {path}: expected 401, got {response.status_code}"
        assert response.json()["detail"] == "Unauthorized"

