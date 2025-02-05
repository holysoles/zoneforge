from zoneforge.zf import ZFZone
import dns.zone
import os.path

ZONE_DATA_LIGHT = """
$ORIGIN example.com.
@ 86400 IN NS ns1
@ 36000 IN SOA ns1 hostmaster 20250116 28800 1800 2592000 86400
    """

def test_new_zfzone():
    """
    GIVEN a zone object
    WHEN it is new, from the minimum info
    THEN check that it correct sets the _zone, record_count properties
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    assert new_zf_zone._zone == new_zone
    assert new_zf_zone.record_count == 1 # should just get the NS record in enumeration

def test_zfzone_to_response():
    """
    GIVEN a zfzone object
    WHEN #TODO
    THEN check that it can be converted to a response dictionary with expected keys
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    res = new_zf_zone.to_response()
    assert isinstance(res, dict)
    assert res.get('name')
    assert res.get('record_count')
    assert res.get('soa')

def test_zfzone_write_to_disk(app):
    """
    GIVEN a zfzone object
    WHEN given an existing zone to update
    THEN check that it can be written to disk successfully to the expected location, and writing to disk is idempotent
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    new_zone_name = f"{str(new_zone.origin)}zone"
    with app.app_context():
        new_zf_zone.write_to_file()
    folder_path = os.environ.get('ZONE_FILE_FOLDER')

    expected_filepath = os.path.join(folder_path, new_zone_name)
    assert os.path.exists(expected_filepath)

    zone_written = dns.zone.from_file(expected_filepath)
    assert zone_written == new_zone

def test_zfzone_get_records():
    """
    GIVEN a zfzone object
    WHEN records are present
    THEN check it can enumerate its records, and can be filtered by type
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    assert len(new_zf_zone.get_all_records()) == 1
    assert len(new_zf_zone.get_all_records(include_soa=True)) == 2
    assert len(new_zf_zone.get_all_records(record_type='A')) == 0

#TODO test get_zones()

# TODO test create_zone()

# TODO test delete_zone()

