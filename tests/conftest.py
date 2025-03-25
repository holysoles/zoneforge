import os
import shutil
from datetime import datetime
import pytest
import dns.zone
from app import create_app
from zoneforge.core import ZFZone

ZONE_WITH_COMMON_DATA = """
$ORIGIN example.com.
@ 86400 IN NS ns1
@ 86400 IN MX 10 mail
@ 86400 IN MX 20 mail2
@ 86400 IN A 192.168.10.10
@ 86400 IN TXT "This domain name is reserved for use in documentation"
@ 36000 IN SOA ns1 hostmaster %s 28800 1800 2592000 86400 ; minimum (1 day)
ftp 86400 IN CNAME @
mail 86400 IN A 192.168.2.10
mail2 86400 IN A 192.168.2.20
ns1 86400 IN A 192.168.1.10
ns2 86400 IN A 192.168.1.20
subdomain 86401 IN CNAME subdomain2.example.com
webmail 86400 IN CNAME @
www 86400 IN CNAME @ ; comments can be used to additional document information
www2 86400 IN A 192.168.10.20
www2 86400 IN A 192.168.10.30
""" % (
    datetime.now().strftime("%Y%m%d")
)


# pylint: disable=redefined-outer-name
def _teardown_app(path: str):
    shutil.rmtree(path)


@pytest.fixture()
def app_new(tmp_path):
    zonefile_folder = str(tmp_path)
    os.environ["ZONE_FILE_FOLDER"] = zonefile_folder
    os.environ["VERSION"] = "v1.0.0"

    app = create_app()
    app.config.update({"TESTING": True, "ZONE_FILE_FOLDER": zonefile_folder})
    app.app_context().push()
    yield app

    # teardown
    _teardown_app(tmp_path)


@pytest.fixture()
def zfzone_common_data(app_new):
    with app_new.app_context():
        new_zone = dns.zone.from_text(text=ZONE_WITH_COMMON_DATA)
        new_zf_zone = ZFZone(
            zone=new_zone, zonefile_folder=app_new.config["ZONE_FILE_FOLDER"]
        )

        yield new_zf_zone


@pytest.fixture()
def app_with_single_zone(app_new):

    with app_new.app_context():
        new_zone = dns.zone.from_text(text=ZONE_WITH_COMMON_DATA)
        new_zf_zone = ZFZone(
            zone=new_zone, zonefile_folder=app_new.config["ZONE_FILE_FOLDER"]
        )
        new_zf_zone.write_to_file()

    yield app_new


@pytest.fixture()
def app_with_multi_zones(app_with_single_zone):
    zone_with_common_data = """
$ORIGIN sub.example.com.
@ 86400 IN NS ns1
@ 86400 IN NS ns2
@ 86400 IN NS ns3
@ 36000 IN SOA ns1 hostmaster 20250118 28800 1800 2592000 86400
ns1 86400 IN A 192.168.1.1
ns2 86400 IN A 192.168.1.2
ns3 86400 IN A 192.168.1.3
ns4 86400 IN A 192.168.1.4
ns5 86400 IN A 192.168.1.255
"""
    new_zone = dns.zone.from_text(text=zone_with_common_data)
    with app_with_single_zone.app_context():
        new_zf_zone = ZFZone(
            zone=new_zone,
            zonefile_folder=app_with_single_zone.config["ZONE_FILE_FOLDER"],
        )
        new_zf_zone.write_to_file()

    yield app_with_single_zone


@pytest.fixture()
def client_new(app_new):
    return app_new.test_client()


@pytest.fixture()
def client_single_zone(app_with_single_zone):
    return app_with_single_zone.test_client()


@pytest.fixture()
def client_multi_zone(app_with_multi_zones):
    return app_with_multi_zones.test_client()
