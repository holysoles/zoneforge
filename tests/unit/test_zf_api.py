from zoneforge.zf_api import StatusResource, ZoneResource, RecordResource, RecordTypeResource

def test_zf_api_status(client_new):
    res = client_new.get("/api/status")
    assert res.status_code == 200
    assert res.json['status'] == 'OK'

# zones
def test_zf_api_zone_get_empty(client_new):
    res = client_new.get("/api/zone")
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) == 0

def test_zf_api_zone_get_single(client_single_zone, zfzone_common_data):
    res = client_single_zone.get("/api/zone")
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) == 1
    zone = res.json[0]
    assert zone['name'] == zfzone_common_data.origin.to_text()
    assert zone['record_count'] == zfzone_common_data.record_count
    expected_soa = zfzone_common_data.get_soa()
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
    assert zone['soa']['comment']

def test_zf_api_zone_get_single_specific(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    res = client_single_zone.get(f"/api/zone/{origin}")
    assert res.status_code == 200
    assert isinstance(res.json, dict)
    zone = res.json
    assert zone['name'] == zfzone_common_data.origin.to_text()
    assert zone['record_count'] == zfzone_common_data.record_count
    expected_soa = zfzone_common_data.get_soa()
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
    assert zone['soa']['comment']

def test_zf_api_zone_get_multi(client_multi_zone):
    res = client_multi_zone.get("/api/zone")
    assert res.status_code == 200
    assert isinstance(res.json, list) and all(isinstance(item, dict) for item in res.json)
    assert len(res.json) > 1

def test_zf_api_zone_post_new(client_new, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    create_data = {
        "name": origin,
        "soa_ttl": 3600,
        "admin_email": f"hostmaster@{origin.rstrip('.')}",
        "refresh": zfzone_common_data.get_soa().refresh,
        "retry": zfzone_common_data.get_soa().retry,
        "expire": zfzone_common_data.get_soa().expire,
        "minimum": zfzone_common_data.get_soa().minimum,
        "primary_ns": zfzone_common_data.get_soa().mname.to_text(),
        "primary_ns_ttl": 3600,
        "primary_ns_ip": "192.0.2.1",
        "primary_ns_a_ttl": 3600,
    }
    res = client_new.post('/api/zone', json = create_data)
    assert res.status_code == 200
    zone = res.json
    assert isinstance(zone, dict)
    assert zone['name'] == create_data['name']
    assert zone['record_count'] == 2
    assert zone['soa']['name'] == "@"
    assert zone['soa']['type'] == 'SOA'
    assert zone['soa']['ttl'] == create_data['soa_ttl']
    assert zone['soa']['data']['mname'] == create_data['primary_ns']
    assert zone['soa']['data']['rname'] == create_data['admin_email']
    assert zone['soa']['data']['serial']
    assert zone['soa']['data']['refresh'] == create_data['refresh']
    assert zone['soa']['data']['retry'] == create_data['retry']
    assert zone['soa']['data']['expire'] == create_data['expire']
    assert zone['soa']['data']['minimum'] == create_data['minimum']
    assert zone['soa'].get('comment') != None

def test_zf_api_zone_put(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    update_data = {
        "name": origin,
        "soa_ttl": 1234,
        "admin_email": f"hostmaster_new@{origin.rstrip('.')}",
        "refresh": zfzone_common_data.get_soa().refresh + 5,
        "retry": zfzone_common_data.get_soa().retry + 5,
        "expire": zfzone_common_data.get_soa().expire + 5,
        "minimum": zfzone_common_data.get_soa().minimum + 5,
        "primary_ns": "ns2",
    }
    res = client_single_zone.put('/api/zone', json = update_data)
    assert res.status_code == 200
    zone = res.json
    assert isinstance(zone, dict)
    assert zone['name'] == update_data['name']
    assert zone['soa']['name'] == "@"
    assert zone['soa']['type'] == 'SOA'
    assert zone['soa']['ttl'] == update_data['soa_ttl']
    assert zone['soa']['data']['mname'] == update_data['primary_ns']
    assert zone['soa']['data']['rname'] == update_data['admin_email']
    assert zone['soa']['data']['serial']
    assert zone['soa']['data']['refresh'] == update_data['refresh']
    assert zone['soa']['data']['retry'] == update_data['retry']
    assert zone['soa']['data']['expire'] == update_data['expire']
    assert zone['soa']['data']['minimum'] == update_data['minimum']
    assert zone['soa'].get('comment') != None

def test_zf_api_zone_delete_single(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    delete_data = {
        "name": origin,
    }
    current_zones = client_single_zone.get('/api/zone')
    assert len(current_zones.json) == 1
    res = client_single_zone.delete('/api/zone', json = delete_data)
    assert res.status_code == 200
    remaining_zones = client_single_zone.get('/api/zone')
    assert len(remaining_zones.json) == 0

def test_zf_api_zone_delete_single(client_multi_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    delete_data = {
        "name": origin,
    }
    current_zones = client_multi_zone.get('/api/zone')
    assert len(current_zones.json) > 1
    res = client_multi_zone.delete('/api/zone', json = delete_data)
    assert res.status_code == 200
    remaining_zones = client_multi_zone.get('/api/zone')
    assert len(remaining_zones.json) >= 1

# records
def test_zf_api_record_get(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    zone_endpoint = f"/api/zone/{origin}/record"
    all_records = client_single_zone.get(zone_endpoint)
    assert isinstance(all_records.json, list)
    assert len(all_records.json) > 0
    for record in all_records.json:
        assert isinstance(record, dict)
        assert record.get('name')
        assert record.get('type')
        assert record.get('ttl')
        assert record.get('data')

    record_type_queries = [
        {"type": "A"},
        {"type": "CNAME"},
        {"type": "MX"},
    ]
    for query in record_type_queries:
        records = client_single_zone.get(zone_endpoint, json = query)
        assert isinstance(records.json, list)
        assert len(records.json) > 0
        for record in records.json:
            assert record['type'] == query['type']

    record_name_data = {"name": 'www2'}
    all_records_under_name = client_single_zone.get(zone_endpoint, json = record_name_data)
    assert isinstance(all_records_under_name.json, list)
    assert len(all_records_under_name.json) > 0
    for record in all_records_under_name.json:
        assert record['name'] == record_name_data['name']

    specific_record_data = {
        "name": "ns1",
        "type": "A"
    }
    specific_record = client_single_zone.get(zone_endpoint, json = specific_record_data)
    assert specific_record

def test_zf_api_record_post(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    record_endpoint = f"/api/zone/{origin}/record"
    new_record_data = {
        "name": "www3",
        "type": "A",
        "ttl": 1000,
        "data": {
            "address": "10.10.10.10",
        },
        "comment": "example comment",
    }
    # check for record first
    existing = client_single_zone.get(record_endpoint, json = new_record_data)
    assert existing.status_code == 404

    res = client_single_zone.post(record_endpoint, json = new_record_data)
    assert res.status_code == 200
    record = res.json
    assert isinstance(record, dict)
    assert record['name'] == new_record_data['name']
    assert record['type'] == new_record_data['type']
    assert record['ttl'] == new_record_data['ttl']
    assert record['comment'] == new_record_data['comment']
    assert record['data']['address'] == new_record_data['data']['address']

def test_zf_api_record_put(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    record_endpoint = f"/api/zone/{origin}/record"
    update_record_data = {
        "name": "ns1",
        "type": "A",
    }
    # check for record first
    existing = client_single_zone.get(record_endpoint, json = update_record_data)
    assert existing.status_code == 200
    update_record_data['data'] = {}
    update_record_data['data']['address'] = "192.168.1.100"
    assert existing.json[0]['data']['address'] != update_record_data['data']['address']


    res = client_single_zone.put(record_endpoint, json = update_record_data)
    assert res.status_code == 200
    record = res.json
    assert isinstance(record, dict)
    assert record['name'] == update_record_data['name']
    assert record['type'] == update_record_data['type']
    assert record['data']['address'] == update_record_data['data']['address']

def test_zf_api_record_delete(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    record_endpoint = f"/api/zone/{origin}/record"
    delete_record_data = {
        "name": "ns1",
        "type": "A",
        "ttl": 86400,
        "data": {
            "address": "192.168.1.10"
        }
    }

    existing = client_single_zone.get(record_endpoint, json = delete_record_data)
    assert existing.status_code == 200

    res = client_single_zone.delete(record_endpoint, json = delete_record_data)
    assert res.status_code == 200

# Record definition information endpoint
def test_zf_api_recordtype_get_all(client_new):
    res = client_new.get('/api/types/recordtype')
    assert res.status_code == 200
    res_body = res.json
    assert len(res_body) > 1
    assert isinstance(res_body, dict)
    assert isinstance(res_body['A'], list)
    assert isinstance(res_body['A'][0], str)

def test_zf_api_recordtype_get_single(client_new):
    res = client_new.get('/api/types/recordtype/CNAME')
    assert res.status_code == 200
    res_body = res.json
    assert len(res_body) == 1
    assert isinstance(res_body, dict)
    assert isinstance(res_body['CNAME'], list)
    assert isinstance(res_body['CNAME'][0], str)
    assert res_body['CNAME'][0] == 'target'