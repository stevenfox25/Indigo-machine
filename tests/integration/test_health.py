from indigo.api.app import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("ok") is (True)
