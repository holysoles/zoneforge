import dns.query
import dns.zone
import dns.resolver
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from zoneforge.core import ZFZone


def zone_from_zone_transfer(
    *,
    zone_name: dns.name.Name,
    zonefile_folder: str,
    nameserver_ip: str = None,
    nameserver_port: int = 53,
    use_udp: bool = False,
) -> ZFZone:
    """
    Initiate a DNS zone transfer for the specified zone from the specified nameserver. Saves the resultant zonefile to the specified zonefile folder.
    """
    try:
        soa_answer = dns.resolver.resolve(zone_name, "SOA")
    except dns.resolver.NXDOMAIN as e:
        raise BadRequest("SOA record for provided domain not resolvable") from e

    if not nameserver_ip:
        master_answer = dns.resolver.resolve(soa_answer[0].mname, "A")
        nameserver_ip = master_answer[0].address

    new_zone = dns.versioned.Zone(
        origin=zone_name,
    )
    new_zfzone = ZFZone(zone=new_zone, zonefile_folder=zonefile_folder)
    udp_mode = dns.query.UDPMode.NEVER
    if use_udp:
        udp_mode = dns.query.UDPMode.TRY_FIRST
    try:
        dns.query.inbound_xfr(
            where=nameserver_ip,
            txn_manager=new_zone,
            port=nameserver_port,
            udp_mode=udp_mode,
        )
    except dns.xfr.TransferError as e:
        raise BadRequest(
            "Zone transfer refused by nameserver. Ensure zone transfers are enabled for the zone."
        )
    new_zfzone.write_to_file()

    return new_zfzone
