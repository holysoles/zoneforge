# pylint: disable=missing-class-docstring
import os.path
import dns.rdatatype
import dns.zone
import dns.name
import dns.rrset
import dns.rdata
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from zoneforge.core import (
    ZFZone,
    get_zones,
    create_zone,
    delete_zone,
    get_records,
    create_record,
    update_record,
    delete_record,
)

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
    # Check the internal zone object
    # pylint: disable=protected-access
    assert new_zf_zone._zone == new_zone
    # pylint: enable=protected-access
    assert new_zf_zone.record_count == 1  # should just get the NS record in enumeration


def test_zfzone_to_response():
    """
    GIVEN a zfzone object
    WHEN its newly initialized
    THEN check that it can be converted to a response dictionary with expected keys
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    res = new_zf_zone.to_response()
    assert isinstance(res, dict)
    assert res.get("name")
    assert res.get("record_count")
    assert res.get("soa")


def test_zfzone_write_to_disk(app_new):
    """
    GIVEN a zfzone object
    WHEN given an existing zone to update
    THEN check that it can be written to disk successfully to the expected location, and writing to disk is idempotent
    """
    new_zone = dns.zone.from_text(text=ZONE_DATA_LIGHT)
    new_zf_zone = ZFZone(new_zone)
    new_zone_name = f"{str(new_zone.origin)}zone"
    with app_new.app_context():
        new_zf_zone.write_to_file()
    folder_path = os.environ.get("ZONE_FILE_FOLDER")

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
    assert len(new_zf_zone.get_all_records(record_type="A")) == 0


# get_zones()
def test_zf_get_zones_new(app_new):
    with app_new.app_context():
        zone_count_for_new_app = len(get_zones())
        assert zone_count_for_new_app == 0


def test_zf_get_zones_single(app_with_single_zone):
    with app_with_single_zone.app_context():
        zone_count_for_single_zone_app = len(get_zones())
        assert zone_count_for_single_zone_app == 1


def test_zf_get_zones_multi(app_with_multi_zones):
    with app_with_multi_zones.app_context():
        zone_count_for_single_zone_app = len(get_zones())
        assert zone_count_for_single_zone_app == 2


def test_zf_get_zones_specific(app_with_multi_zones):
    zone_name = "example.com"
    zone_dns_name = dns.name.from_text(zone_name)
    with app_with_multi_zones.app_context():
        zone_list = get_zones(zone_name=zone_dns_name)
        assert len(zone_list) == 1
        assert isinstance(zone_list[0], dns.zone.Zone)
        assert zone_list[0].origin == zone_dns_name


# create_zone()
def test_zf_create_new_zone(app_new, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin
    soa_rrset = zfzone_common_data.get_all_records(record_type="SOA")[0]
    ns_rrset = zfzone_common_data.get_all_records(record_type="NS")[0]

    with app_new.app_context():
        zone = create_zone(
            zone_name=zone_dns_name, soa_rrset=soa_rrset, ns_rrset=ns_rrset
        )
    assert isinstance(zone, ZFZone)
    assert zone.origin == zone_dns_name
    # check that only "counted" record is the NS record
    assert zone.record_count == 1


def test_zf_create_existing_zone(app_with_single_zone, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin
    soa_rrset = zfzone_common_data.get_all_records(record_type="SOA")[0]
    ns_rrset = zfzone_common_data.get_all_records(record_type="NS")[0]
    try:
        with app_with_single_zone.app_context():
            _ = create_zone(
                zone_name=zone_dns_name, soa_rrset=soa_rrset, ns_rrset=ns_rrset
            )
        assert False
    except Forbidden:
        assert True


# delete_zone()
def test_zf_delete_zone(app_with_single_zone, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin

    with app_with_single_zone.app_context():
        deleted = delete_zone(zone_dns_name)
        expected_filepath = os.path.join(
            app_with_single_zone.config["ZONE_FILE_FOLDER"], f"{zone_dns_name}zone"
        )
    assert deleted
    assert not os.path.exists(expected_filepath)


# get_records()
def test_zf_get_all_records(app_with_single_zone, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin

    with app_with_single_zone.app_context():
        records = get_records(zone_dns_name)
    assert len(records) > 0
    for record in records:
        assert isinstance(record, dns.rrset.RRset)


def test_zf_get_all_records_of_type(app_with_single_zone, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin
    record_type = "NS"

    with app_with_single_zone.app_context():
        records = get_records(zone_name=zone_dns_name, record_type=record_type)
    assert len(records) > 0
    for record in records:
        assert isinstance(record, dns.rrset.RRset)
        assert record.rdtype == dns.rdatatype.from_text(record_type)


def test_zf_get_specific_record(app_with_single_zone, zfzone_common_data):
    zone_dns_name = zfzone_common_data.origin
    record_name = "@"
    relativized_name = zone_dns_name.relativize(zone_dns_name)

    with app_with_single_zone.app_context():
        records = get_records(zone_name=zone_dns_name, record_name=record_name)
    assert len(records) > 0
    for record in records:
        assert record.name == relativized_name


# create_record()
def test_zf_create_a_record(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "test"
    record_dns_name = dns.name.from_text(record_name, origin=zfzone_common_data.origin)
    record_type = "A"
    record_data = {"address": "192.168.1.1"}

    with app_with_single_zone.app_context():
        created_record = create_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            zone_name=zone_name,
        )
    assert isinstance(created_record, dns.rrset.RRset)
    assert created_record.name == record_dns_name.relativize(
        origin=zfzone_common_data.origin
    )
    assert created_record.rdtype == dns.rdatatype.from_text(record_type)
    created_rdata = created_record[0]
    for key, data in record_data.items():
        assert getattr(created_rdata, key) == data

    with app_with_single_zone.app_context():
        got_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    assert len(got_records) == 1
    assert created_record == got_records[0]


def test_zf_create_cname_record(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "cname-test"
    record_dns_name = dns.name.from_text(record_name, origin=zfzone_common_data.origin)
    record_type = "CNAME"
    record_data = {"target": "example.com"}

    with app_with_single_zone.app_context():
        created_record = create_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            zone_name=zone_name,
        )
    assert isinstance(created_record, dns.rrset.RRset)
    assert created_record.name == record_dns_name.relativize(
        origin=zfzone_common_data.origin
    )
    assert created_record.rdtype == dns.rdatatype.from_text(record_type)
    created_rdata = created_record[0]
    for key, data in record_data.items():
        assert getattr(created_rdata, key) == data

    with app_with_single_zone.app_context():
        got_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    assert len(got_records) == 1
    assert created_record == got_records[0]


def test_zf_create_mx_record(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "mail-test"
    record_dns_name = dns.name.from_text(record_name, origin=zfzone_common_data.origin)
    record_type = "MX"
    record_data = {"preference": 20, "exchange": "mail"}

    with app_with_single_zone.app_context():
        created_record = create_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            zone_name=zone_name,
        )
    assert isinstance(created_record, dns.rrset.RRset)
    assert created_record.name == record_dns_name.relativize(
        origin=zfzone_common_data.origin
    )
    assert created_record.rdtype == dns.rdatatype.from_text(record_type)
    created_rdata = created_record[0]
    for key, data in record_data.items():
        assert getattr(created_rdata, key) == data

    with app_with_single_zone.app_context():
        got_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    assert len(got_records) == 1
    assert created_record == got_records[0]


def test_zf_create_record_nowrite(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "test"
    record_dns_name = dns.name.from_text(record_name, origin=zfzone_common_data.origin)
    record_type = "A"
    record_data = {"address": "192.168.1.1"}

    with app_with_single_zone.app_context():
        created_record = create_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            zone_name=zone_name,
            write=False,
        )
    assert isinstance(created_record, dns.rrset.RRset)
    assert created_record.name == record_dns_name.relativize(
        origin=zfzone_common_data.origin
    )
    assert created_record.rdtype == dns.rdatatype.from_text(record_type)
    created_rdata = created_record[0]
    for key, data in record_data.items():
        assert getattr(created_rdata, key) == data

    try:
        with app_with_single_zone.app_context():
            _ = get_records(
                zone_name=zone_name, record_name=record_name, record_type=record_type
            )
        assert False
    except NotFound:
        assert True


# update_record()
def test_zf_update_a_record(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "ns1"
    record_type = "A"
    record_data = {"address": "192.168.1.1"}

    with app_with_single_zone.app_context():
        existing_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    for key, data in record_data.items():
        assert data != getattr(existing_records[0][0], key)

    with app_with_single_zone.app_context():
        updated_record = update_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            zone_name=zone_name,
        )
    assert isinstance(updated_record, dns.rrset.RRset)
    updated_rdata = updated_record[0]
    for key, data in record_data.items():
        assert getattr(updated_rdata, key) == data

    with app_with_single_zone.app_context():
        got_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    assert len(got_records) == 1
    assert updated_rdata == got_records[0][0]


# delete_record()
def test_zf_delete_a_record(app_with_single_zone, zfzone_common_data):
    zone_name = str(zfzone_common_data.origin)
    record_name = "ns1"
    record_type = "A"
    record_ttl = "86400"
    record_data = {"address": "192.168.1.10"}

    with app_with_single_zone.app_context():
        existing_records = get_records(
            zone_name=zone_name, record_name=record_name, record_type=record_type
        )
    assert len(existing_records) == 1
    for key, data in record_data.items():
        assert data == getattr(existing_records[0][0], key)

    with app_with_single_zone.app_context():
        _ = delete_record(
            record_name=record_name,
            record_type=record_type,
            record_data=record_data,
            record_ttl=record_ttl,
            zone_name=zone_name,
        )

    with app_with_single_zone.app_context():
        try:
            _ = get_records(
                zone_name=zone_name, record_name=record_name, record_type=record_type
            )
            assert False
        except NotFound:
            assert True
