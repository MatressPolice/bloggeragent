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
