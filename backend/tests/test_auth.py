# backend/tests/test_auth.py
def test_login_redirect(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert "url" in resp.json()

def test_callback_error_missing_code(client):
    resp = client.get("/auth/callback")  # no code param
    assert resp.status_code == 422  # FastAPI’s validation error
