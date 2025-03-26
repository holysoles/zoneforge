from werkzeug.exceptions import BadRequest, BadGateway
from zoneforge.core import ZFZone
from zoneforge.core.transfer import zone_from_zone_transfer


def test_zf_zone_transfer(mocker, app_new, zfzone_common_data):
    # pylint: disable=unused-argument
    def _mock_transfer(*, where, txn_manager, port, udp_mode, lifetime):
        zone_records = zfzone_common_data.get_all_records(include_soa=True)
        for record in zone_records:
            with txn_manager.writer() as txn:
                txn.add(record)

    # pylint: enable=unused-argument

    mocker.patch("dns.query.inbound_xfr", side_effect=_mock_transfer)

    origin = zfzone_common_data.origin.to_text()
    with app_new.app_context():
        new_zone = zone_from_zone_transfer(
            zone_name=origin, zonefile_folder=app_new.config["ZONE_FILE_FOLDER"]
        )
    assert isinstance(new_zone, ZFZone)
    assert new_zone.origin == zfzone_common_data.origin
    assert new_zone.record_count == zfzone_common_data.record_count


def test_zf_zone_transfer_params(mocker, app_new, zfzone_common_data):
    # pylint: disable=unused-argument
    def _mock_transfer(*, where, txn_manager, port, udp_mode, lifetime):
        zone_records = zfzone_common_data.get_all_records(include_soa=True)
        for record in zone_records:
            with txn_manager.writer() as txn:
                txn.add(record)

    # pylint: enable=unused-argument

    mocker.patch("dns.query.inbound_xfr", side_effect=_mock_transfer)

    origin = zfzone_common_data.origin.to_text()
    with app_new.app_context():
        new_zone = zone_from_zone_transfer(
            zone_name=origin,
            zonefile_folder=app_new.config["ZONE_FILE_FOLDER"],
            nameserver_ip="1.1.1.1",
            nameserver_port=5353,
            use_udp=True,
            transfer_timeout=1,
        )
    assert isinstance(new_zone, ZFZone)
    assert new_zone.origin == zfzone_common_data.origin


def test_zf_zone_transfer_fail_no_such_domain(app_new, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    with app_new.app_context():
        try:
            _ = zone_from_zone_transfer(
                zone_name=origin, zonefile_folder=app_new.config["ZONE_FILE_FOLDER"]
            )
            assert False
        except BadRequest:
            assert True


def test_zf_zone_transfer_fail_timeout(app_new, zfzone_common_data):
    origin = zfzone_common_data.origin.to_text()
    with app_new.app_context():
        try:
            _ = zone_from_zone_transfer(
                zone_name=origin,
                zonefile_folder=app_new.config["ZONE_FILE_FOLDER"],
                nameserver_ip="1.1.1.1",
                nameserver_port=5353,
                use_udp=True,
                transfer_timeout=1,
            )
            assert False
        except BadGateway:
            assert True
