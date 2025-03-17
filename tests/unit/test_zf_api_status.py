def test_zf_api_status(client_new):
    res = client_new.get("/api/status")
    assert res.status_code == 200
    assert res.json['running'] == True
