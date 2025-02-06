from zoneforge.zf_api import StatusResource, ZoneResource, RecordResource, RecordTypeResource

def test_zf_api_status(client_new):
    res = client_new.get("/api/status")
    assert res.json['status'] == 'OK'

def test_zf_api_zone_get_empty(client_new):
    res = client_new.get("/api/zone")
    assert res.json == None

def test_zf_api_zone_get_single(client_single_zone, zfzone_common_data):
    res = client_single_zone.get("/api/zone")
    assert len(res.json) == 1
    zone = res.json[0]
    assert zone['name'] == zfzone_common_data.origin.to_text()
    assert zone['record_count'] == zfzone_common_data.record_count
    expected_soa = zfzone_common_data.get_soa().mname
    assert zone['soa']['name'] == "@"
    assert zone['soa']['type'] == 'SOA'
    assert zone['soa']['ttl'] == 36000
    assert zone['soa']['data']['mname'] == expected_soa.mname.to_text()
    assert zone['soa']['data']['rname'] == expected_soa.rname.to_text()
    assert zone['soa']['data']['serial'] == expected_soa.serial
    assert zone['soa']['data']['refresh'] == expected_soa.refresh
    assert zone['soa']['data']['retry'] == expected_soa.retry
    assert zone['soa']['data']['expire'] == expected_soa.expire
    assert zone['soa']['data']['minimum'] == expected_soa.minimum
    assert zone['soa']['comment'] #exists

def test_zf_api_zone_get_multi(client_multi_zone):
    res = client_multi_zone.get("/api/zone")
    assert len(res.json) > 1
    #TODO more


