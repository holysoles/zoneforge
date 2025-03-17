from zoneforge.api.records import DnsRecord
from zoneforge.api.zones import DnsZone
from zoneforge.api.status import ServerStatus
from zoneforge.api.types import RecordTypeResource

def test_zf_api_zone_get_empty(client_new):
    res = client_new.get("/api/zones")
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) == 0

def test_zf_api_zone_get_single(client_single_zone, zfzone_common_data):
    res = client_single_zone.get("/api/zones")
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
    res = client_single_zone.get(f"/api/zones/{origin}")
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
    res = client_multi_zone.get("/api/zones")
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
    res = client_new.post('/api/zones', json = create_data)
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
        "soa_ttl": 1234,
        "admin_email": f"hostmaster_new@{origin.rstrip('.')}",
        "refresh": zfzone_common_data.get_soa().refresh + 5,
        "retry": zfzone_common_data.get_soa().retry + 5,
        "expire": zfzone_common_data.get_soa().expire + 5,
        "minimum": zfzone_common_data.get_soa().minimum + 5,
        "primary_ns": "ns2",
    }
    res = client_single_zone.put(f"/api/zones/{origin}", json = update_data)
    assert res.status_code == 200
    zone = res.json
    assert isinstance(zone, dict)
    assert zone['name'] == origin
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
    current_zones = client_single_zone.get('/api/zones')
    assert len(current_zones.json) == 1
    res = client_single_zone.delete('/api/zones', json = delete_data)
    assert res.status_code == 200
    remaining_zones = client_single_zone.get('/api/zones')
    assert len(remaining_zones.json) == 0

def test_zf_api_zone_delete_single(client_multi_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    current_zones = client_multi_zone.get(f"/api/zones/{origin}")
    assert len(current_zones.json) > 1
    res = client_multi_zone.delete(f"/api/zones/{origin}")
    assert res.status_code == 200
    remaining_zones = client_multi_zone.get('/api/zones')
    assert len(remaining_zones.json) >= 1
