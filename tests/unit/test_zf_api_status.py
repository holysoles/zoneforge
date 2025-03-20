# pylint: disable=missing-class-docstring
def test_zf_api_status(client_new):
    res = client_new.get("/api/status")
    assert res.status_code == 200
    assert res.json["running"] is True


def test_zf_api_version(client_new):
    res = client_new.get("/api/status/version")
    assert res.status_code == 200
    version = res.json.get("version")
    assert version == "v1.0.0"
    assert isinstance(version, str)
