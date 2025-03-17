from zoneforge.api.records import DnsRecord
from zoneforge.api.zones import DnsZone
from zoneforge.api.status import ServerStatus
from zoneforge.api.types import RecordTypeResource

def test_zf_api_record_get(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    zone_endpoint = f"/api/zones/{origin}/records"
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
    record_endpoint = f"/api/zones/{origin}/records"
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
    record_name = 'ns1'
    record_endpoint = f"/api/zones/{origin}/records/{record_name}"
    update_record_data = {
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
    assert record['name'] == record_name
    assert record['type'] == update_record_data['type']
    assert record['data']['address'] == update_record_data['data']['address']

def test_zf_api_record_delete(client_single_zone, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    record_name = 'ns1'
    record_endpoint = f"/api/zones/{origin}/records/{record_name}"
    delete_record_data = {
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
