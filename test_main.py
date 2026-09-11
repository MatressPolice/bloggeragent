import os
from unittest.mock import patch
from fastapi.testclient import TestClient

import tempfile

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
            import main
            import importlib
            importlib.reload(main)

            client = TestClient(main.app)
            response = client.get("/")

            assert response.status_code == 200
            assert "Mocked Frontend" in response.text

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

@patch.dict(os.environ, {"API_KEY": "supersecret"})
def test_auth_middleware_with_invalid_header_format():
    import main
    client = TestClient(main.app)

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
    import main
    client = TestClient(main.app)

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

def test_auth_middleware_path_traversal_static():
    import tempfile
    import asyncio
    with tempfile.TemporaryDirectory() as tmpdir:
        frontend_dir = os.path.join(tmpdir, "frontend")
        os.makedirs(frontend_dir)
        with open(os.path.join(frontend_dir, "index.html"), "w") as f:
            f.write("hello")

        with open(os.path.join(tmpdir, "frontend-secret.txt"), "w") as f:
            f.write("secret")

        real_abspath = os.path.abspath
        def mock_abspath(path):
            if path.endswith("main.py"):
                return os.path.join(tmpdir, "main.py")
            return real_abspath(path)

        with patch("os.path.abspath", side_effect=mock_abspath):
            with patch("main.AGENT_DIR", tmpdir):
                with patch.dict(os.environ, {"API_KEY": "supersecret"}):
                    import main
                    import importlib
                    importlib.reload(main)

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

                    response = asyncio.run(main.verify_api_key(request, mock_call_next))

                    # Before the fix, this bypassed auth check and returned 200 from mock_call_next
                    # After the fix, it should return 401 Unauthorized
                    assert response.status_code == 401


@patch.dict(os.environ, {"ALLOWED_ORIGINS": "https://custom-origin.example.com, http://localhost:3000 "})
def test_custom_cors_origins():
    import main
    import importlib
    importlib.reload(main)

    assert "https://custom-origin.example.com" in main.allow_origins
    assert "http://localhost:3000" in main.allow_origins
    assert len(main.allow_origins) == 2

    client = TestClient(main.app)
    # Perform an OPTIONS request for CORS check. We just want to check if the route returns allowed headers for our origin
    response = client.options("/", headers={"Origin": "https://custom-origin.example.com", "Access-Control-Request-Method": "GET"})

    # Note: the exact headers might depend on ADK defaults, but we can just check if our env vars loaded properly
    assert response.status_code == 200

def test_default_cors_origins():
    # Delete ALLOWED_ORIGINS if it exists
    if "ALLOWED_ORIGINS" in os.environ:
        del os.environ["ALLOWED_ORIGINS"]

    import main
    import importlib
    importlib.reload(main)

    assert "https://adk-default-service-name-122956929515.us-west1.run.app" in main.allow_origins
    assert "http://localhost:8080" in main.allow_origins

def test_static_file_auth_bypass_success():
    import main
    import uuid
    import shutil

    frontend_dir = os.path.join(main.AGENT_DIR, "frontend")
    frontend_created = False
    if not os.path.exists(frontend_dir):
        os.makedirs(frontend_dir)
        frontend_created = True

    test_filename = f"test_bypass_{uuid.uuid4().hex}.html"
    test_filepath = os.path.join(frontend_dir, test_filename)

    try:
        with open(test_filepath, "w") as f:
            f.write("<html><body>Bypass Test</body></html>")

        with patch.dict(os.environ, {"API_KEY": "supersecret"}):
            client = TestClient(main.app)
            response = client.get(f"/{test_filename}")

            assert response.status_code == 200
            assert "Bypass Test" in response.text
    finally:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)
        if frontend_created and os.path.exists(frontend_dir):
            shutil.rmtree(frontend_dir)
