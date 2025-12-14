def test_health(api):
    r = api.get("/api/health/")
    assert r.json().get("status") == "ok"
