# backend/tests/test_market.py

def test_price_endpoint(client):
    # assuming you mock Redis or it’s empty
    resp = client.get("/market/price/EUR-USD")
    assert resp.status_code == 404

def test_ticks_endpoint(client, monkeypatch):
    # monkeypatch fetch_ticks in market_service
    from services.market_data import fetch_ticks

    def fake_ticks(symbol, redis, settings, logger):
        return [{"symbol": symbol, "bid": 1.1, "ask": 1.2, "timestamp": "2025-05-30T12:00:00Z"}]
    monkeypatch.setattr(fetch_ticks, "__wrapped__", fake_ticks)

    resp = client.get("/market/ticks/EUR-USD")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list) and data[0]["symbol"] == "EUR-USD"
