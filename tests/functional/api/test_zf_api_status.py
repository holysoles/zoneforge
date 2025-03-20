def test_zf_api_status(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the server status is requested
    THEN returns an HTML page with 200
    """
    res = client_new.get("/api/status")
    assert res.status_code == 200
    assert res.json["running"] is True


def test_zf_api_version(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the server version is requested
    THEN returns a version string
    """
    res = client_new.get("/api/status/version")
    assert res.status_code == 200
    assert res.json["version"] is not None
    assert isinstance(res.json["version"], str)
