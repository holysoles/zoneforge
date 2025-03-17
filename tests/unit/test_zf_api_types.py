
# Record definition information endpoint
def test_zf_api_recordtype_get_all(client_new):
    res = client_new.get('/api/types/recordtype')
    assert res.status_code == 200
    res_body = res.json
    assert len(res_body) > 1
    assert isinstance(res_body, list)
    assert res_body[0]['type'] == 'A'
    assert res_body[0]['fields'] == ['address']

def test_zf_api_recordtype_get_single(client_new):
    res = client_new.get('/api/types/recordtype/CNAME')
    assert res.status_code == 200
    res_body = res.json
    assert isinstance(res_body, dict)
    assert res_body['type'] == 'CNAME'
    assert res_body['fields'] == ['target']
