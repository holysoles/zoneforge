import glob
import re
import importlib
import logging
from datetime import datetime
from os import remove
from os.path import join, exists, basename
from typing import Type
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
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin

RECORD_FIELDS_TO_RELATIVIZE = [
    "target",
    "next",
    "exchange",
]
ZFZONE_CUSTOM_ATTRS = ["_zone", "record_count"]

# Assume we have a logger setup for us already
logger = logging.getLogger()


class ZFZone(dns.zone.Zone):
    """
    Extends the dnspython library's Zone class to provide additional handling
    """

    # We don't want to call super init since we don't have the same information that the dns.zone.Zone needs
    # pylint: disable=super-init-not-called
    def __init__(self, zone: dns.zone.Zone, zonefile_folder: str):
        self._zone = zone  # Store the original zone instance
        self.record_count = len(self.get_all_records())
        self.zonefile_folder = zonefile_folder

    # pylint: enable=super-init-not-called

    def __getattr__(self, name):
        return getattr(self._zone, name)

    def __setattr__(self, name, value):
        if name in ZFZONE_CUSTOM_ATTRS:
            super().__setattr__(name, value)
        else:
            setattr(self._zone, name, value)

    def to_response(self):
        res = {}
        res["name"] = self.origin.to_text()
        res["record_count"] = self.record_count
        soa = super().get_rrset(
            name="@", rdtype="SOA"
        )  # could use zone.get_soa(), but we want an rrset for transform_records
        res["soa"] = record_to_response(soa)[0]
        return res

    def write_to_file(self):
        update_timestamp = int(datetime.now().strftime("%Y%m%d"))
        zone_name = str(self.origin)
        with self.writer() as txn:
            txn.update_serial(value=update_timestamp, relative=False)
        zone_file_path = join(self.zonefile_folder, f"{zone_name}zone")

        logger.debug("Writing zone %s to '%s'", self.origin, zone_file_path)
        self.to_file(f=zone_file_path, want_comments=True, want_origin=True)
        self.record_count = len(self.get_all_records())

    def get_all_records(self, record_type: str = None, include_soa: bool = False):
        include_soa = include_soa or record_type == "SOA"
        record_type = (
            dns.rdatatype.from_text(record_type)
            if record_type
            else dns.rdatatype.from_text("ANY")
        )
        all_records_gen = self.iterate_rdatasets(rdtype=record_type)
        all_records = [
            dns.rrset.from_rdata_list(
                record[0], ttl=record[1].ttl, rdatas=record[1].items
            )
            for record in all_records_gen
            if include_soa or record[1].rdtype != dns.rdatatype.SOA
        ]
        return list(all_records)


def get_zones(zonefile_folder: str, zone_name: dns.name.Name = None) -> list[ZFZone]:
    zonefile_map = {}
    zones = []
    if zone_name:
        logger.debug("Getting zone object for origin '%s'", zone_name)
        zonefile_map[zone_name] = join(zonefile_folder, f"{zone_name}zone")
    else:
        zonefile_pattern = join(zonefile_folder, "*zone")
        zone_files = glob.glob(zonefile_pattern)
        for filepath in zone_files:
            filename = basename(filepath)
            domain = ".".join(filename.split(".")[:-1])
            if domain:
                zonefile_map[domain] = filepath

    for z_name, z_file_path in zonefile_map.items():
        if not exists(z_file_path):
            continue
        try:
            zone = dns.zone.from_file(
                f=z_file_path,
                origin=z_name,
                zone_factory=dns.versioned.Zone,
                relativize=True,
            )
            zfzone = ZFZone(zone=zone, zonefile_folder=zonefile_folder)
            zones.append(zfzone)
        except Exception as e:
            raise InternalServerError(
                f"ERROR: exception loading zone file '{z_file_path}'"
            ) from e
    return zones


def create_zone(
    *,
    zone_name: dns.name.Name,
    zonefile_folder: str,
    soa_rrset: dns.rrset.RRset,
    ns_rrset: dns.rrset.RRset,
    ns_a_rrset: dns.rrset.RRset = None,
) -> ZFZone:
    zone_file_path = join(zonefile_folder, f"{zone_name}zone")
    if exists(zone_file_path):
        raise Forbidden("A zone with that name already exists.")
    new_zone = dns.zone.Zone(
        origin=zone_name,
    )
    new_zfzone = ZFZone(zone=new_zone, zonefile_folder=zonefile_folder)
    with new_zfzone.writer() as txn:
        txn.add(soa_rrset)
        txn.add(ns_rrset)
        if ns_a_rrset:
            txn.add(ns_a_rrset)
    new_zfzone.write_to_file()
    return new_zfzone


def delete_zone(zone_name: dns.name.Name, zonefile_folder: str) -> bool:
    zone_file_name = join(zonefile_folder, f"{zone_name}zone")
    if exists(zone_file_name):
        logger.info("Removing zone %s", zone_name)
        remove(zone_file_name)
        return True
    return False


def get_records(
    zone_name: str,
    zonefile_folder: str,
    *,
    record_name: str = None,
    record_type: str = None,
    include_soa: bool = False,
) -> list[dns.rrset.RRset]:
    zone = get_zones(zonefile_folder=zonefile_folder, zone_name=zone_name)
    if not zone:
        raise NotFound("the specified zone does not exist.")
    zone = ZFZone(zone=zone[0], zonefile_folder=zonefile_folder)

    if record_name:
        try:
            matching_node = zone[record_name].rdatasets
        except KeyError:
            # we're using the key indexing as a shortcut to test if we have the record
            raise NotFound  # pylint: disable=raise-missing-from

        if record_type:
            record_type = dns.rdatatype.from_text(record_type)
            matching_records = [
                dns.rrset.from_rdata_list(
                    record_name, ttl=record.ttl, rdatas=record.items
                )
                for record in matching_node
                if record.rdtype == record_type
            ]
        else:
            matching_records = [
                dns.rrset.from_rdata_list(
                    record_name, ttl=record.ttl, rdatas=record.items
                )
                for record in matching_node
            ]

        if not matching_records:
            raise NotFound
    else:
        matching_records = zone.get_all_records(
            record_type=record_type, include_soa=include_soa
        )
    return matching_records


# pylint: disable=too-many-arguments
def create_record(
    *,
    record_name: str,
    record_type: str,
    record_data: dict,
    record_ttl: int,
    zonefile_folder: str,
    zone_name: dns.name.Name = None,
    record_class: dns.rdataclass.RdataClass = "IN",
    record_comment: str = None,
    write: bool = True,
) -> dns.rrset.RRset:

    # perform validation only when we're writing to disk. creating a new zone requires we have the record objects first.
    matching_rrset = None
    if write:
        if not zone_name:
            raise ValueError("A zone_name must be provided to write to a zone file.")
        zone = get_zones(zonefile_folder=zonefile_folder, zone_name=zone_name)
        if not zone:
            raise NotFound("the specified zone does not exist.")
        zone = zone[0]
        matching_rrset = zone.get_rrset(name=record_name, rdtype=record_type)

    new_rdata = request_to_rdata(
        zone_name=zone_name,
        record_type=record_type,
        record_data=record_data,
        record_class=record_class,
        record_comment=record_comment,
    )

    # We always want a clean rrset to return, since rdata isn't associated with a name
    new_rrset = dns.rrset.from_rdata(record_name, record_ttl, new_rdata)
    if matching_rrset:
        try:
            matching_rrset.add(new_rdata, record_ttl)
            updated_rrset = matching_rrset
        except (dns.rdataset.IncompatibleTypes, dns.rdataset.DifferingCovers) as e:
            raise BadRequest from e
    else:
        updated_rrset = new_rrset

    if write:
        with zone.writer() as txn:
            txn.add(updated_rrset)
        logger.info(
            "Created record %s in zone %s with data '%s'",
            record_name,
            zone_name,
            record_data,
        )
        zone.write_to_file()
    return new_rrset


def update_record(
    *,
    zone_name: str,
    zonefile_folder: str,
    record_name: str,
    record_type: str,
    record_data: dict,
    record_index: int,
    record_ttl: int,
    record_class: dns.rdataclass.RdataClass = "IN",
    record_comment: str = None,
) -> dns.rrset.RRset:
    zone = get_zones(zonefile_folder=zonefile_folder, zone_name=zone_name)[0]

    matching_rrset = zone.get_rrset(name=record_name, rdtype=record_type)
    if not matching_rrset:
        raise NotFound("specified record does not exist.")

    new_rdata = request_to_rdata(
        zone_name=zone_name,
        record_type=record_type,
        record_data=record_data,
        record_class=record_class,
        record_comment=record_comment,
    )
    # replace the original rdata of the record we're updating with the new rdata
    try:
        rdata_to_change = list(matching_rrset.items)[record_index]
    except IndexError:
        # pylint: disable=raise-missing-from
        raise NotFound("Provided record index was not found.")
        # pylint: enable=raise-missing-from
    new_rdata_list = [
        new_rdata if rdata == rdata_to_change else rdata
        for rdata in list(matching_rrset.items)
    ]
    updated_rrset = dns.rrset.from_rdata_list(record_name, record_ttl, new_rdata_list)

    with zone.writer() as txn:
        txn.replace(updated_rrset)
    logger.info(
        "Updated record %s in zone %s with data '%s'",
        record_name,
        zone_name,
        record_data,
    )
    zone.write_to_file()
    # We always want a clean rrset to return, since rdata isn't associated with a name
    return dns.rrset.from_rdata(record_name, record_ttl, new_rdata)


def delete_record(
    *,
    zone_name: str,
    zonefile_folder: str,
    record_name: str,
    record_type: str,
    record_data: dict,
    # we aren't using record_index at the moment, but it is required in the event it is deemed necessary for use
    record_index: int,  # pylint: disable=unused-argument
    record_class: dns.rdataclass.RdataClass = "IN",
) -> bool:
    zone = get_zones(zonefile_folder=zonefile_folder, zone_name=zone_name)[0]

    target_rdata = request_to_rdata(
        zone_name=zone_name,
        record_type=record_type,
        record_data=record_data,
        record_class=record_class,
    )
    with zone.writer() as txn:
        try:
            txn.delete_exact(record_name, target_rdata)
            logger.info("Deleted record %s in zone %s", record_name, zone_name)
        except dns.transaction.DeleteNotExact:
            raise NotFound(  # pylint: disable=raise-missing-from
                "specified record does not exist."
            )
    zone.write_to_file()
    return True


# pylint: enable=too-many-arguments


def record_to_response(records: list[dns.rrset.RRset]) -> dict:
    transformed_records = []
    if isinstance(records, dns.rrset.RRset):
        records = [records]

    for rrset in records:
        logger.debug("transforming records under name %s", rrset.name)
        rdata_index = 0
        for rdata in rrset.items:
            record_type = rrset.rdtype
            record = {
                "name": str(rrset.name),
                "type": record_type._name_,  # pylint: disable=protected-access
                "ttl": rrset.ttl,
                "data": {},
                "comment": "",
                "index": rdata_index,
            }
            if getattr(rdata, "rdcomment", None):
                record["comment"] = rdata.rdcomment
            record_slots = get_rdata_class_slots(
                record_type._name_  # pylint: disable=protected-access
            )
            for slot in record_slots:
                property_value = getattr(rdata, slot)
                # perform any necessary transformations
                # needs to be explicitly checked for None since dns.name.Name for a root record is evaluated to False (len=0)
                if property_value is not None:
                    if slot == "strings":
                        txt = ""
                        prefix = ""
                        for s in property_value:
                            txt += f"{prefix}{dns.rdata._escapify(s)}"  # pylint: disable=protected-access
                            prefix = " "
                        property_value = txt
                    if isinstance(property_value, dns.name.Name):
                        property_value = property_value.to_text()
                    if slot == "rname":
                        email_not_relative = len(property_value.split(".")) > 1
                        if email_not_relative:
                            email_with_address = re.sub(
                                r"(?<=[^\\])\.(?=(.*\.).*)", "@", property_value
                            )
                            email_proper = re.sub(r"\\\.", ".", email_with_address)
                            property_value = email_proper
                record["data"][slot] = property_value

            transformed_records.append(record)
            rdata_index += 1
    return transformed_records


def request_to_rdata(
    *,
    zone_name: str,
    record_type: str,
    record_data: dict,
    record_class: dns.rdataclass.RdataClass,
    record_comment: str = None,
) -> dns.rdata.Rdata:
    origin = dns.name.from_text(text=zone_name)

    # relativize the record data fields that are names
    for record_field in RECORD_FIELDS_TO_RELATIVIZE:
        if record_field in record_data:
            data_name = dns.name.from_text(
                text=record_data[record_field], origin=origin
            )
            record_data[record_field] = data_name.relativize(origin=origin)

    # construct rdata class values from string in the proper order. We could pass these to a constructor as kwargs, but we don't currently have client side rdata slot typing
    rdata_str = ""
    for rdata_slot in get_rdata_class_slots(record_type):
        slot_data = record_data[rdata_slot]
        if rdata_slot == "strings":
            slot_data = f'"{slot_data}"'
        rdata_str += f"{slot_data} "
    rdata = dns.rdata.from_text(rdclass=record_class, rdtype=record_type, tok=rdata_str)

    if record_comment:
        # we can't set the comment via the constructor, so we need to use __getstate__ and __setstate__
        rdata_dict = rdata.__getstate__()
        rdata_dict["rdcomment"] = record_comment
        rdata.__setstate__(rdata_dict)

    return rdata


def get_record_type_map(record_type_name: str = None):
    """
    For a given record type, returns a dict of type=name, and fields=[<all record data fields for that record data type>]
    """
    return {"type": record_type_name, "fields": get_rdata_class_slots(record_type_name)}


def get_all_record_types() -> list:
    """
    Returns a list of dicts of record data types and their associated fields.
    """
    record_types = []
    for rdtype in dns.rdatatype.RdataType:
        rdtype_text = dns.rdatatype.to_text(rdtype)
        rdtype_map = get_record_type_map(rdtype_text)
        # deprecated record types have no slots, so we skip them
        if len(rdtype_map["fields"]) > 0:
            record_types.append(rdtype_map)
    # sort for user friendliness
    record_types = sorted(record_types, key=lambda rdata_type: rdata_type["type"])
    return record_types


def get_rdata_class_slots(rdtype_text: str) -> list[str]:
    """Try to get the data-related slots for a given record type."""
    rdata_class = _get_rdata_class(rdtype_text)
    all_slots = []
    if rdata_class:
        for cls in rdata_class.__mro__:
            slots = getattr(cls, "__slots__", [])
            for slot in slots:
                if slot not in all_slots:
                    all_slots.append(slot)

    base_slots = ["rdclass", "rdtype", "rdcomment"]
    all_slots = [slot for slot in all_slots if slot not in base_slots]

    return all_slots


def _get_rdata_class(rdtype_text: str) -> Type[dns.rdata.Rdata]:
    """
    dynamically import the rdata class for a given record type
    """
    for package in ["ANY", "IN"]:
        try:
            module_name = rdtype_text.replace("-", "_")
            module = importlib.import_module(f"dns.rdtypes.{package}.{module_name}")
            rdata_class = getattr(module, module_name)
            return rdata_class
        except ImportError:
            pass
    return None


def friendly_email_to_zone_format(email_address: str) -> str:
    email_parts = email_address.split("@")
    email_username = email_parts[0].replace(
        ".", "\\."
    )  # need to escape username periods for zonefile
    email_domain = email_parts[1]
    return f"{email_username}.{email_domain}"
