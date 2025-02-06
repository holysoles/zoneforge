import dns.immutable
import dns.node
import dns.name
import dns.rdatatype
import dns.rdtypes.txtbase
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
import re
import importlib
from werkzeug.exceptions import *
from flask import current_app
from typing import Type

RECORD_FIELDS_TO_RELATIVIZE = [
    'target',
    'next',
    'exchange',
]

ZFZONE_CUSTOM_ATTRS = ['_zone', 'record_count']
class ZFZone(dns.zone.Zone):
    """
    Extends the dnspython library's Zone class to provide additional handling
    """
    def __init__(self, zone: dns.zone.Zone):
        self._zone = zone  # Store the original zone instance
        self.record_count = len(self.get_all_records())

    def __getattr__(self, name):
        return getattr(self._zone, name)

    def __setattr__(self, name, value):
        if name in ZFZONE_CUSTOM_ATTRS:
            super().__setattr__(name, value)
        else:
            setattr(self._zone, name, value)
    
    def to_response(self):
        repr = {}
        repr['name'] = self.origin.to_text()
        repr['record_count'] = self.record_count
        soa = super().get_rrset(name="@", rdtype="SOA") # could use zone.get_soa(), but we want an rrset for transform_records
        repr['soa'] = record_to_response(soa)[0]
        return repr

    def write_to_file(self):
        update_timestamp = int(datetime.now().strftime("%Y%m%d"))
        zone_name = str(self.origin)
        with self.writer() as txn:
            txn.update_serial(value=update_timestamp, relative=False)
        zone_file_path = join(current_app.config['ZONE_FILE_FOLDER'], f"{zone_name}zone")

        print(f"DEBUG: Writing zone {self.origin} to '{zone_file_path}'")
        self.to_file(f=zone_file_path, want_comments=True, want_origin=True)
        self.record_count = len(self.get_all_records())
    
    def get_all_records(self, record_type: str = None, include_soa: bool = False):
        include_soa = include_soa or record_type == "SOA"
        record_type = dns.rdatatype.from_text(record_type) if record_type else dns.rdatatype.from_text('ANY')
        all_records_gen = self.iterate_rdatasets(rdtype=record_type)
        all_records = [
            dns.rrset.from_rdata_list(record[0], ttl=record[1].ttl, rdatas=record[1].items) 
            for record in all_records_gen
            if include_soa or record[1].rdtype != dns.rdatatype.SOA
        ]
        return list(all_records)

def get_zones(zone_name: dns.name.Name = None) -> list[ZFZone]:
    zonefile_map = {}
    zones = []
    if zone_name:
        print("Getting zone object for origin", zone_name)
        zonefile_map[zone_name] = join(current_app.config['ZONE_FILE_FOLDER'], f"{zone_name}zone")
    else:
        zonefile_pattern = join(current_app.config['ZONE_FILE_FOLDER'], "*zone")
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
            zone = dns.zone.from_file( #TODO see if we can make this a class method for ZFZone
                f=zone_file_path,
                origin=zone_name,
                zone_factory=dns.versioned.Zone,
                relativize=True
            )
            zfzone = ZFZone(zone)
            zones.append(zfzone)
        except Exception as e:
            print (f"ERROR: exception loading zone file '{zone_file_path}' ", e.__class__, e)
            raise InternalServerError
    return zones

def create_zone(
        zone_name: dns.name.Name,
        soa_rrset: dns.rrset.RRset,
        ns_rrset: dns.rrset.RRset,
        ns_a_rrset: dns.rrset.RRset = None
    ) -> ZFZone:
    zone_file_path = join(current_app.config['ZONE_FILE_FOLDER'], f"{zone_name}zone")
    if exists(zone_file_path):
        raise Forbidden('A zone with that name already exists.')
    else:
        new_zone = dns.zone.Zone(
            origin=zone_name,
        )
        new_zfzone = ZFZone(new_zone)
        with new_zfzone.writer() as txn:
            txn.add(soa_rrset)
            txn.add(ns_rrset)
            if ns_a_rrset:
                txn.add(ns_a_rrset)
        new_zfzone.write_to_file()
        return new_zfzone

def delete_zone(zone_name: dns.name.Name) -> bool:
    zone_file_name = join(current_app.config['ZONE_FILE_FOLDER'], f"{zone_name}zone")
    if exists(zone_file_name):
        print(f"INFO: Removing zone {zone_name}")
        remove(zone_file_name)
        return True
    return False

def get_records(
        zone_name: str,
        record_name: str = None,
        record_type: str = None,
        include_soa: bool = False,
    ) -> list[dns.rrset.RRset]:
    zone = get_zones(zone_name)
    if not zone:
        raise NotFound('the specified zone does not exist.')
    zone = ZFZone(zone[0])

    if record_name:
        try:
            matching_node = zone[record_name].rdatasets
        except KeyError:
            raise NotFound

        if record_type:
            record_type = dns.rdatatype.from_text(record_type)
            matching_records = [dns.rrset.from_rdata_list(record_name, ttl=record.ttl, rdatas=record.items) for record in matching_node if record.rdtype == record_type]
        else:
            matching_records = [dns.rrset.from_rdata_list(record_name, ttl=record.ttl, rdatas=record.items) for record in matching_node]
        
        if not matching_records:
            raise NotFound
        return matching_records
    else:
        all_records = zone.get_all_records(record_type=record_type, include_soa=include_soa)
        return all_records

def create_record(
        record_name: str,
        record_type: str,
        record_data: dict,
        zone_name: dns.name.Name = None,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = None,
        record_comment: str = None,
        write: bool = True,
    ) -> dns.rrset.RRset:

    # perform validation only when we're writing to disk. creating a new zone requires we have the record objects first.
    if write:
        if not zone_name:
            raise ValueError('A zone_name must be provided to write to a zone file.')
        zone = get_zones(zone_name)
        if not zone:
            raise NotFound('the specified zone does not exist.')
        zone = zone[0]
        if zone.get_rdataset(name=record_name, rdtype=record_type):
            raise BadRequest('specified record already exists.')

    new_rrset = request_to_record(zone_name=zone_name, record_name=record_name, record_type=record_type, record_data=record_data, record_ttl=record_ttl, record_class=record_class, record_comment=record_comment)

    if write:
        with zone.writer() as txn:
            txn.add(new_rrset)
        print(f"INFO: Created record {record_name} in zone {zone_name} with data '{record_data}'")
        zone.write_to_file()
    return new_rrset

def update_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_class: dns.rdataclass.RdataClass = "IN",
        record_ttl: int = None,
        record_comment: str = None,
    ) -> dns.rrset.RRset:
    zone = get_zones(zone_name)[0]
    if not zone.get_rdataset(name=record_name, rdtype=record_type):
        raise NotFound('specified record does not exist.')
    
    new_rrset = request_to_record(zone_name=zone_name, record_name=record_name, record_type=record_type, record_data=record_data, record_ttl=record_ttl, record_class=record_class, record_comment=record_comment)

    with zone.writer() as txn:
        txn.replace(new_rrset)
    print(f"INFO: Updated record {record_name} in zone {zone_name} with data '{record_data}'")
    zone.write_to_file()
    return new_rrset

def delete_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_ttl: int,
        record_class: dns.rdataclass.RdataClass = "IN",
    ) -> bool:
    zone = get_zones(zone_name)[0]

    target_rrset = request_to_record(zone_name=zone_name, record_name=record_name, record_type=record_type, record_data=record_data, record_ttl=record_ttl, record_class=record_class)
    with zone.writer() as txn:
        try:
            txn.delete_exact(target_rrset)
            print(f"INFO: Deleted record {record_name} in zone {zone_name}")
        except dns.transaction.DeleteNotExact as e:
            raise NotFound('specified record does not exist.')
    zone.write_to_file()
    return True

#  TODO records cannot currently be created with the same name and type, but different data (i.e. MX records)
def record_to_response(records: list[dns.rrset.RRset]) -> dict:
    transformed_records = []
    if isinstance(records, dns.rrset.RRset):
        records = [records]

    for rrset in records:
        print(f"DEBUG: transforming records under name {rrset.name}")
        for rdata in rrset.items:
            record_type = rrset.rdtype
            record = {
                        "name": str(rrset.name),
                        "type": record_type._name_,
                        "ttl": rrset.ttl,
                        "data": {},
                    }
            if getattr(rdata, 'rdcomment', None):
                record['comment'] = rdata.rdcomment
            else:
                record['comment'] = ""
            record_slots = get_rdata_class_slots(record_type._name_)
            for slot in record_slots:
                property_value = getattr(rdata, slot)
                # perform any necessary transformations
                if property_value != None: # needs to be explicitly checked for None since dns.name.Name for a root record is evaluated to False (len=0)
                    if slot == "strings":
                        txt = ""
                        prefix = ""
                        for s in property_value:
                            txt += f'{prefix}{dns.rdata._escapify(s)}'
                            prefix = " "
                        property_value = txt
                    if isinstance(property_value, dns.name.Name):
                        property_value = property_value.to_text()
                    if slot == 'rname':
                        email_not_relative = len(property_value.split('.')) > 1
                        if email_not_relative:
                            email_with_address = re.sub(r'(?<=[^\\])\.(?=(.*\.).*)', '@', property_value)
                            email_proper = re.sub(r'\\\.', '.', email_with_address)
                            property_value = email_proper
                record["data"][slot] = property_value
                    
            transformed_records.append(record)
    return transformed_records

def request_to_record(
        zone_name: str,
        record_name: str,
        record_type: str,
        record_data: dict,
        record_class: dns.rdataclass.RdataClass,
        record_ttl: int = None,
        record_comment: str = None,
    ) -> dns.rrset.RRset:
    origin = dns.name.from_text(text=zone_name)

    if not record_ttl:
        record_ttl = current_app.config['DEFAULT_ZONE_TTL']

    # relativize the record data fields that are names
    for record_field in RECORD_FIELDS_TO_RELATIVIZE:
        if record_field in record_data:
            data_name = dns.name.from_text(text=record_data[record_field], origin=origin)
            record_data[record_field] = data_name.relativize(origin=origin)

    # construct rdata class values from string in the proper order. We could pass these to a constructor as kwargs, but we don't currently have client side rdata slot typing
    # rdata_class = _get_rdata_class(record_type)
    # rdata = rdata_class(rdclass=record_class, rdtype=record_type, **record_data)
    rdata_str = ""
    for rdata_slot in get_rdata_class_slots(record_type):
        rdata_str += f"{record_data[rdata_slot]} "
    rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=rdata_str)

    if record_comment:
        # we can't set the comment via the constructor, so we need to use __getstate__ and __setstate__
        rdata_dict = rdata.__getstate__()
        rdata_dict['rdcomment'] = record_comment
        rdata.__setstate__(rdata_dict)

    rrset = dns.rrset.from_rdata(record_name, record_ttl, rdata)
    return rrset

def get_record_types_map(record_type_name: str = None):
    """
    returns a dict of all record types with their names as keys, their attributes as subkeys, and the attributes typing as a subkey
    """        
    record_types = {}
    if record_type_name:
        record_types[record_type_name] = get_rdata_class_slots(record_type_name)
    else:
        for rdtype in dns.rdatatype.RdataType:
            rdtype_text = dns.rdatatype.to_text(rdtype)
            slots = get_rdata_class_slots(rdtype_text)
            # deprecated record types have no slots, so we skip them
            if len(slots) > 0:
                record_types[rdtype_text] = slots
        record_types = {k: record_types[k] for k in sorted(record_types)} # sort for user friendliness

    return record_types

def get_rdata_class_slots(rdtype_text: str) -> list[str]: 
    """Try to get the data-related slots for a given record type."""
    rdata_class = _get_rdata_class(rdtype_text)
    all_slots = []
    if rdata_class:
        for cls in rdata_class.__mro__:
            slots = getattr(cls, '__slots__', [])
            for slot in slots:
                if slot not in all_slots:
                    all_slots.append(slot)
    
    base_slots = ['rdclass', 'rdtype', 'rdcomment']
    all_slots = [slot for slot in all_slots if slot not in base_slots]
    
    return all_slots

def _get_rdata_class(rdtype_text: str) -> Type[dns.rdata.Rdata]:
    """
    dynamically import the rdata class for a given record type
    """
    for package in ['ANY', 'IN']:
        try:
            module_name = rdtype_text.replace('-', '_')
            module = importlib.import_module(f'dns.rdtypes.{package}.{module_name}')
            rdata_class = getattr(module, module_name)
            return rdata_class
        except(ImportError):
            pass
    return None

def friendly_email_to_zone_format(email_address: str) -> str:
    email_parts = email_address.split('@')
    email_username = email_parts[0].replace('.', '\\.') # need to escape username periods for zonefile
    email_domain = email_parts[1]
    return f"{email_username}.{email_domain}"