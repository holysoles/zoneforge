import dns.immutable
import dns.node
import dns.zone
import dns.rdata
import dns.versioned
import dns.transaction
from os import listdir, remove
from os.path import join, exists, basename
import glob
from werkzeug.exceptions import *

# TODO get this declared in app.py, support it as a env var and arg
ZONE_FILE_FOLDER = './lib/examples'

def get_zones(zone_name=None) -> list[dns.zone.Zone]:
    zonefile_map = {}
    zones = []
    if zone_name:
        print("Getting zone object for origin", zone_name)
        zonefile_map[zone_name] = join(ZONE_FILE_FOLDER, f"{zone_name}zone")
    else:
        zonefile_pattern = join(ZONE_FILE_FOLDER, "*zone")
        zone_files = glob.glob(zonefile_pattern)
        for filepath in zone_files:
            filename = basename(filepath) 
            domain = '.'.join(filename.split('.')[:-1])
            if domain:
                zonefile_map[domain] = filepath

    for zone_name, zone_file_path in zonefile_map.items():
        if not exists(zone_file_path):
            raise NotFound('A zone with that name does not exist.')
        try:
            zone = dns.zone.from_file(
                f=zone_file_path,
                origin=zone_name,
                zone_factory=dns.versioned.Zone
                )
            zones.append(zone)
        except Exception as e:
            print (f"ERROR: exception loading zone file '{zone_file_path}' ", e.__class__, e)
            raise InternalServerError
    return zones

def create_zone(zone_name) -> bool:
    zone_file_path = join(ZONE_FILE_FOLDER, f"{zone_name}zone")
    if exists(zone_file_path):
        raise Forbidden('A zone with that name already exists.')
    else:
        new_zone = dns.zone.Zone(
            origin=zone_name
        )
        # TODO need to have SOA record at creation time
        with open(zone_file_path, "w") as zone_file:
            zone_file.write(new_zone.to_text())
        return new_zone

def delete_zone(zone_name) -> bool:
    zone_file_name = join(ZONE_FILE_FOLDER, f"{zone_name}zone")
    if exists(zone_file_name):
        remove(zone_file_name)
        return True
    return False

def _write_zone(zone: dns.zone.Zone):
    print(f"INFO: Writing zone {zone.origin} to disk")
    zone_file_path = join(ZONE_FILE_FOLDER, f"{zone.origin}zone")
    zone.to_file(f=zone_file_path, want_comments=True, want_origin=True)




def get_records(zone_name, record_name=None, record_type=None) -> dns.immutable.Dict | dns.versioned.Zone:
    # TODO support filtering on record_type
    zone = get_zones(zone_name)
    if not zone:
        raise NotFound('the specified zone does not exist.')
    zone = zone[0]
    if record_name:
        return zone[record_name]
    else:
        return zone.nodes

# TODO probably need to handle @/origin in thesemethods .. TBD
def create_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = 86400
    ) -> dns.rdata.Rdata:
    zone = get_zones(zone_name)[0]
    if zone.get_rdataset(name=record_name, rdtype=record_type):
        raise BadRequest('specified record already exists.')
    rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=record_data, ) # TODO add origin, but needs to be DNS name obj
    with zone.writer() as txn:
        txn.add(record_name, record_ttl, rdata)
    print(f"INFO: Created record {record_name} in zone {zone_name} with data '{record_data}'")
    _write_zone(zone)
    return zone[record_name]

def update_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = 86400
    ) -> dns.rdata.Rdata:
    zone = get_zones(zone_name)[0]
    if not zone.get_rdataset(name=record_name, rdtype=record_type):
        raise NotFound('specified record does not exist.')
    new_rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=record_data, ) # TODO add origin, but needs to be DNS name obj
    # TODO check for planned changes with existing rdata
    with zone.writer() as txn:
        txn.replace(record_name, record_ttl, new_rdata)
    print(f"INFO: Updated record {record_name} in zone {zone_name} with data '{record_data}'")
    _write_zone(zone)
    return zone[record_name]

def delete_record(
        zone_name: str,
        record_name: str,
        record_type: str,
    ) -> bool:
    zone = get_zones(zone_name)[0]

    with zone.writer() as txn:
        try:
            txn.delete_exact(record_name, record_type)
            print(f"INFO: Deleted record {record_name} in zone {zone_name}")
        except dns.transaction.DeleteNotExact as e:
            raise NotFound('specified record does not exist.')
    _write_zone(zone)
    return True
