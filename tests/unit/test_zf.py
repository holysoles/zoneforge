import pytest
from flask import current_app, Flask
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
    THEN check that it can be written to disk successfully, and the update persists
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    tmp_zone_folder = tmp_path
    with current_app.app_context():
         # default filepath uses env var from app context
        new_zf_zone.write_to_file(folder=tmp_zone_folder)
    expected_filepath = os.path.join(tmp_zone_folder, new_zone.origin)
    zone_written = dns.zone.from_file(expected_filepath)
    zone_written
    #TODO test loading