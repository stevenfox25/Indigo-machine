from indigo.api.app import create_app


def test_devices_endpoint_shape():
    app = create_app()
    client = app.test_client()

    resp = client.get("/api/devices")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)

    # Allow flexibility, but ensure it's not returning junk.
    # Expected keys can evolve, but we should always return structured JSON.
    assert "devices" in data or "lanes" in data or "utility" in data
