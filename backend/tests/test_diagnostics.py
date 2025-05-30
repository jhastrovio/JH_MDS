# backend/tests/test_diagnostics.py
def test_readiness(client):
    resp = client.get("/debug/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert "redis" in data and "uptime" in data