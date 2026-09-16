import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

import asyncio
import importlib
import uuid
import main

@pytest.fixture
def mock_frontend_dir(tmp_path):
    """Fixture that creates a temporary frontend directory with an index.html file."""
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "index.html").write_text("<html><body>Mocked Frontend</body></html>")
    return frontend_dir

def setup_test_client(reload=False):
    if reload:
        importlib.reload(main)
    return TestClient(main.app), main

def test_frontend_static_mount(mock_frontend_dir):
    tmpdir = str(mock_frontend_dir.parent)

    # Patch os.path.abspath so that main.AGENT_DIR becomes tmpdir without changing signature
    real_abspath = os.path.abspath
    def mock_abspath(path):
        if path.endswith("main.py"):
            return os.path.join(tmpdir, "main.py")
        return real_abspath(path)

    with patch("os.path.abspath", side_effect=mock_abspath):
        client, _ = setup_test_client(reload=True)
        response = client.get("/")

        assert response.status_code == 200
        assert "Mocked Frontend" in response.text

def test_no_frontend_endpoint():
    # Mock os.path.isdir to return False for the frontend directory
    # so that the fallback endpoint is registered instead of the static mount.
    with patch("os.path.isdir", return_value=False):
        # We must import main inside the mocked context so the module-level 
        # condition is evaluated with the mocked isdir.
        client, _ = setup_test_client(reload=True)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "frontend dir not found"
        assert "cwd" in data
        assert "files" in data

def test_auth_middleware_no_key_configured():
    # If API_KEY is not set, API should deny access by default (secure by default)
    with patch.dict(os.environ, {}, clear=True), patch("main.API_KEY", None):
        client, _ = setup_test_client(reload=False)
        response = client.get("/list-apps")
        assert response.status_code == 401
        assert "API_KEY environment variable is not set" in response.json()["detail"]

@patch('main.API_KEY', 'supersecret')
def test_auth_middleware_with_key_unauthorized():
    client, main_mod = setup_test_client(reload=False)

    # Public endpoints should still be accessible
    for path in main_mod.PUBLIC_PATHS:
        assert client.get(path).status_code == 200

    # Protected endpoints should return 401
    response = client.get("/list-apps")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@patch('main.API_KEY', 'supersecret')
def test_auth_middleware_with_key_authorized():
    client, _ = setup_test_client(reload=False)

    # Using correct API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer supersecret"}
    )
    assert response.status_code == 200

@patch('main.API_KEY', 'supersecret')
def test_auth_middleware_with_wrong_key():
    client, _ = setup_test_client(reload=False)

    # Using incorrect API key
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer wrongkey"}
    )
    assert response.status_code == 401

@patch('main.API_KEY', 'supersecret')
def test_auth_middleware_with_invalid_header_format():
    client, _ = setup_test_client(reload=False)

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

    # Empty token ("Bearer " without token)
    response = client.get(
        "/list-apps",
        headers={"Authorization": "Bearer "}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

@patch('main.API_KEY', 'supersecret')
@patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://localhost:8080"})
def test_auth_middleware_options_preflight():
    importlib.reload(main)
    client = TestClient(main.app)

    # OPTIONS request to a protected path should return 200 OK
    # due to the preflight bypass in verify_api_key.
    # We must include proper CORS headers for the CORSMiddleware to intercept
    # and return 200 instead of the router returning 405 Method Not Allowed.
    response = client.options(
        "/list-apps",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200

@patch('main.API_KEY', 'supersecret')
def test_auth_middleware_bypass_attempts():
    client, _ = setup_test_client(reload=False)

    # Attempting bypass using path traversal, url encoding, or extra slashes
    bypass_paths = [
        "/%72un",
        "http://testserver//list-apps",
        "http://testserver///list-apps",
        "/docs/../list-apps",
        "/static/../list-apps",
        "/nonexistent"
    ]
    for path in bypass_paths:
        response = client.get(path)
        assert response.status_code == 401, f"Failed for path {path}: expected 401, got {response.status_code}"
        assert response.json()["detail"] == "Unauthorized"

def test_auth_middleware_path_traversal_static(mock_frontend_dir):
    tmpdir = str(mock_frontend_dir.parent)

    with open(os.path.join(tmpdir, "frontend-secret.txt"), "w") as f:
        f.write("secret")

    real_abspath = os.path.abspath
    def mock_abspath(path):
        if path.endswith("main.py"):
            return os.path.join(tmpdir, "main.py")
        return real_abspath(path)

    with patch("os.path.abspath", side_effect=mock_abspath), \
         patch("main.AGENT_DIR", tmpdir), \
         patch.dict(os.environ, {"API_KEY": "supersecret"}), \
         patch("main.API_KEY", "supersecret"):
        _, main_mod = setup_test_client(reload=True)

        from fastapi import Request

        async def mock_call_next(request):
            class MockResponse:
                status_code = 200
            return MockResponse()

        # URL encoded path traversal
        scope = {
            "type": "http",
            "method": "GET",
            "url": "http://testserver/%2E%2E%2Ffrontend-secret.txt",
            "path": "%2E%2E%2Ffrontend-secret.txt",
            "headers": []
        }

        request = Request(scope)

        response = asyncio.run(main_mod.verify_api_key(request, mock_call_next))

        # Before the fix, this bypassed auth check and returned 200 from mock_call_next
        # After the fix, it should return 401 Unauthorized
        assert response.status_code == 401

@patch.dict(os.environ, {"ALLOWED_ORIGINS": "https://custom-origin.example.com, http://localhost:3000 "})
def test_custom_cors_origins():
    client, main_mod = setup_test_client(reload=True)

    assert "https://custom-origin.example.com" in main_mod.allow_origins
    assert "http://localhost:3000" in main_mod.allow_origins
    assert len(main_mod.allow_origins) == 2

    # Perform an OPTIONS request for CORS check. We just want to check if the route returns allowed headers for our origin
    response = client.options("/", headers={"Origin": "https://custom-origin.example.com", "Access-Control-Request-Method": "GET"})

    # Note: the exact headers might depend on ADK defaults, but we can just check if our env vars loaded properly
    assert response.status_code == 200

def test_default_cors_origins():
    # Delete ALLOWED_ORIGINS if it exists
    if "ALLOWED_ORIGINS" in os.environ:
        del os.environ["ALLOWED_ORIGINS"]

    _, main_mod = setup_test_client(reload=True)

    assert main_mod.allow_origins == []

def test_frontend_dir_abspath_prefix_performance_optimization():
    """Verify that the module-level FRONTEND_DIR_ABSPATH_PREFIX optimization is in place."""
    import main
    import os
    expected_prefix = os.path.abspath(main.FRONTEND_DIR) + os.path.sep
    assert main.FRONTEND_DIR_ABSPATH_PREFIX == expected_prefix, (
        "FRONTEND_DIR_ABSPATH_PREFIX must be calculated at module level "
        "to avoid redundant abspath calculations in the middleware."
    )

def test_static_file_auth_bypass_success(mock_frontend_dir):
    tmpdir = str(mock_frontend_dir.parent)
    test_filename = f"test_bypass_{uuid.uuid4().hex}.html"
    test_filepath = os.path.join(str(mock_frontend_dir), test_filename)

    with open(test_filepath, "w") as f:
        f.write("<html><body>Bypass Test</body></html>")

    real_abspath = os.path.abspath
    def mock_abspath(path):
        if path.endswith("main.py"):
            return os.path.join(tmpdir, "main.py")
        return real_abspath(path)

    with patch("os.path.abspath", side_effect=mock_abspath), \
         patch("main.AGENT_DIR", tmpdir), \
         patch.dict(os.environ, {"API_KEY": "supersecret"}), \
         patch("main.API_KEY", "supersecret"):
        client, main_mod = setup_test_client(reload=True)
        response = client.get(f"/{test_filename}")

        assert response.status_code == 200
        assert "Bypass Test" in response.text
