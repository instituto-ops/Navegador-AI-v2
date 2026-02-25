import os
import sys

from fastapi.testclient import TestClient

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app

client = TestClient(app)

def test_cors_allowed_origin():
    """Test that the default allowed origin works."""
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_disallowed_origin():
    """Test that a disallowed origin is blocked (no CORS headers)."""
    response = client.get("/health", headers={"Origin": "http://evil.com"})
    assert response.status_code == 200
    # Important: The response succeeds (200 OK), but the browser blocks it because
    # the Access-Control-Allow-Origin header is missing or doesn't match.
    assert "access-control-allow-origin" not in response.headers
