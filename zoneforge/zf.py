import dns.immutable
import dns.node
import dns.name
import dns.rdatatype
import dns.zone
import dns.rdata
import dns.rdataset
import dns.rrset
import dns.versioned
import dns.transaction
from datetime import datetime
from os import remove
from os.path import join, exists, basename
import glob
from werkzeug.exceptions import *

# TODO get this declared in app.py, support it as a env var and arg
ZONE_FILE_FOLDER = './lib/examples'

def get_zones(zone_name: dns.name.Name = None) -> list[dns.zone.Zone]:
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
            continue
        try:
            #TODO parse file, dump ttl to .ttl file for zone if there is a ttl directive
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

def create_zone(
        zone_name: dns.name.Name,
        soa_rrset: dns.rrset.RRset,
        ns_rrset: dns.rrset.RRset,
        ns_a_rrset: dns.rrset.RRset = None
    ) -> dns.zone.Zone:
    zone_file_path = join(ZONE_FILE_FOLDER, f"{zone_name}zone")
    if exists(zone_file_path):
        raise Forbidden('A zone with that name already exists.')
    else:
        new_zone = dns.zone.Zone(
            origin=zone_name,
        )
        with new_zone.writer() as txn:
            txn.add(soa_rrset)
            txn.add(ns_rrset)
            if ns_a_rrset:
                txn.add(ns_a_rrset)
        _write_zone(new_zone)
        return new_zone

def delete_zone(zone_name: dns.name.Name) -> bool:
    zone_file_name = join(ZONE_FILE_FOLDER, f"{zone_name}zone")
    if exists(zone_file_name):
        remove(zone_file_name)
        return True
    return False

def _write_zone(zone: dns.zone.Zone):
    update_timestamp = int(datetime.now().strftime("%Y%m%d"))
    with zone.writer() as txn:
        txn.update_serial(value=update_timestamp, relative=False)
    print(f"INFO: Writing zone {zone.origin} to disk")
    zone_file_path = join(ZONE_FILE_FOLDER, f"{zone.origin}zone")
    zone.to_file(f=zone_file_path, want_comments=True, want_origin=True)




def get_records(
        zone_name: str,
        record_name: str = None,
        record_type: str = None,
    ) -> dns.rrset.RRset:
    zone = get_zones(zone_name)
    if not zone:
        raise NotFound('the specified zone does not exist.')
    zone = zone[0]

    if record_name:
        matching_node = zone[record_name].rdatasets

        if record_type:
            record_type = dns.rdatatype.from_text(record_type)
            matching_records = [dns.rrset.from_rdata_list(record_name, ttl=record.ttl, rdatas=record.items) for record in matching_node if record.rdtype == record_type]
        else:
            matching_records = [dns.rrset.from_rdata_list(record_name, ttl=record.ttl, rdatas=record.items) for record in matching_node]
        return matching_records
    else:
        record_type = dns.rdatatype.from_text(record_type) if record_type else dns.rdatatype.from_text('ANY')
        all_records_gen = zone.iterate_rdatasets(rdtype=record_type)
        all_records = (dns.rrset.from_rdata_list(record[0], ttl=record[1].ttl, rdatas=record[1].items) for record in all_records_gen)

        return list(all_records)

# TODO probably need to handle @/origin in thesemethods .. TBD
def create_record(
        record_name: str,
        record_type: str,
        record_data: str,
        zone_name: str = None,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = 86400,
        record_comment: str = None,
        write: bool = True,
    ) -> dns.rrset.RRset:

    if not zone_name and write:
        raise ValueError('A zone_name must be provided to write to a zone file.')
    if zone_name:
        zone = get_zones(zone_name)[0]
        if zone.get_rdataset(name=record_name, rdtype=record_type):
            raise BadRequest('specified record already exists.')
    tokenizer_data = f" {record_data}; {record_comment}"
    new_rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=tokenizer_data, ) # TODO add origin, but needs to be DNS name obj
    new_rrset = dns.rrset.from_rdata(record_name, record_ttl, new_rdata)
    if write:
        with zone.writer() as txn:
            txn.add(new_rrset)
        print(f"INFO: Created record {record_name} in zone {zone_name} with data '{record_data}'")
        _write_zone(zone)
    return new_rrset

def update_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = 86400,
        record_comment: str = None,
    ) -> dns.rrset.RRset:
    zone = get_zones(zone_name)[0]
    if not zone.get_rdataset(name=record_name, rdtype=record_type):
        raise NotFound('specified record does not exist.')
    tokenizer_data = f" {record_data}; {record_comment}"
    new_rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=tokenizer_data, ) # TODO add origin, but needs to be DNS name obj
    new_rrset = dns.rrset.from_rdata(record_name, record_ttl, new_rdata)
    # TODO check for planned changes with existing rdata

    with zone.writer() as txn:
        txn.replace(new_rrset)
    print(f"INFO: Updated record {record_name} in zone {zone_name} with data '{record_data}'")
    _write_zone(zone)
    return new_rrset

def delete_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: str,
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
