def test_zf_api_recordtype_get_all(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN record data type information is requested
    THEN a list of record data type dicts is returned
    """
    res = client_new.get("/api/types/recordtype")
    assert res.status_code == 200
    res_body = res.json
    assert len(res_body) > 1
    assert isinstance(res_body, list)
    assert res_body[0]["type"] == "A"
    assert res_body[0]["fields"] == ["address"]


def test_zf_api_recordtype_get_single(client_new):
    """
    GIVEN a web client for a newly initialized server
    WHEN the server status is requested
    THEN a single record data type dict is returned
    """
    res = client_new.get("/api/types/recordtype/CNAME")
    assert res.status_code == 200
    res_body = res.json
    assert isinstance(res_body, dict)
    assert res_body["type"] == "CNAME"
    assert res_body["fields"] == ["target"]
