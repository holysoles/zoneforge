import dns.name
from flask_restx import Namespace, Resource, reqparse, fields
from flask import current_app
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from zoneforge.core import (
    get_zones,
    create_zone,
    delete_zone,
    create_record,
    update_record,
    friendly_email_to_zone_format,
)
from zoneforge.core.transfer import zone_from_zone_transfer
from zoneforge.api.records import dns_record_model

api = Namespace("zones", description="DNS zone related operations")

zone_parser = reqparse.RequestParser()
zone_parser.add_argument("name", type=str, help="Name of the DNS Zone", required=False)

zone_post_parser = zone_parser.copy()
zone_parser.replace_argument(
    "name", type=str, help="Name of the DNS Zone", required=True
)
zone_post_parser.add_argument("soa_ttl", type=str, help="SOA TTL", required=True)
zone_post_parser.add_argument(
    "admin_email", type=str, help="Email address of zone admin", required=True
)
zone_post_parser.add_argument(
    "refresh",
    type=str,
    help="Record refresh frequency for secondary nameservers",
    required=True,
)
zone_post_parser.add_argument(
    "retry", type=str, help="Retry frequency for failed zone transfers", required=True
)
zone_post_parser.add_argument(
    "expire",
    type=str,
    help="Period after which the zone is discarded if no updates are received",
    required=True,
)
zone_post_parser.add_argument(
    "minimum",
    type=str,
    help="Used for calculation of negative response TTL",
    required=True,
)
zone_post_parser.add_argument(
    "primary_ns", type=str, help="Primary nameserver for the zone", required=True
)
zone_post_parser.add_argument(
    "primary_ns_ttl",
    type=str,
    help="TTL for the primary nameserver's NS record",
    required=True,
)
zone_post_parser.add_argument(
    "primary_ns_ip",
    type=str,
    help="IP for the primary nameserver's A record",
    required=False,
)
zone_post_parser.add_argument(
    "primary_ns_a_ttl",
    type=str,
    help="TTL for the primary nameserver's A record",
    required=False,
)

zone_put_parser = zone_parser.copy()
zone_put_parser.remove_argument("name")
zone_put_parser.add_argument("soa_ttl", type=str, help="SOA TTL", required=True)
zone_put_parser.add_argument(
    "admin_email", type=str, help="Email address of zone admin", required=True
)
zone_put_parser.add_argument(
    "refresh",
    type=str,
    help="Record refresh frequency for secondary nameservers",
    required=True,
)
zone_put_parser.add_argument(
    "retry", type=str, help="Retry frequency for failed zone transfers", required=True
)
zone_put_parser.add_argument(
    "expire",
    type=str,
    help="Period after which the zone is discarded if no updates are received",
    required=True,
)
zone_put_parser.add_argument(
    "minimum",
    type=str,
    help="Used for calculation of negative response TTL",
    required=True,
)
zone_put_parser.add_argument(
    "primary_ns", type=str, help="Primary nameserver for the zone", required=True
)

zone_model = api.model(
    "DnsZone",
    {
        "name": fields.String(example="example.com."),
        "record_count": fields.Integer(example=13),
        "soa": fields.Nested(
            dns_record_model,
            example={
                "name": "@",
                "type": "SOA",
                "ttl": 36000,
                "comment": " minimum (1 day)",
                "data": {
                    "minimum": "86400",
                    "expire": "2592000",
                    "retry": "1800",
                    "refresh": "28800",
                    "serial": "20250116",
                    "rname": "hostmaster",
                    "mname": "ns1",
                },
            },
        ),
    },
)

zone_transfer_parser = reqparse.RequestParser()
zone_transfer_parser.add_argument(
    "zone_name",
    type=str,
    help="Name of the zone to initiate a transfer for.",
    required=True,
)
zone_transfer_parser.add_argument(
    "primary_ns_ip",
    type=str,
    help="IP to connect to for the zone transfer. If not provided, the primary nameserver for the Zone is looked up via SOA query.",
    required=False,
)
zone_transfer_parser.add_argument(
    "primary_ns_port",
    type=str,
    help="Port to connect to for the zone transfer. If not provided, port 53 is assumed.",
    required=False,
)
zone_transfer_parser.add_argument(
    "use_udp",
    type=bool,
    help="Whether or not the transfer should attempted to be initiated over UDP. Default is to use TCP.",
    required=False,
)
zone_transfer_parser.add_argument(
    "transfer_timeout",
    type=str,
    help="How long to wait, in seconds, for the entire transfer to complete. 60s by default.",
    required=False,
)


@api.route("")
class DnsZone(Resource):
    @api.marshal_with(zone_model, as_list=True)
    def get(self):
        """
        Gets a list of all DNS Zones known to the server.
        """
        zones_response = []

        dns_name = None
        zones = get_zones(current_app.config["ZONE_FILE_FOLDER"], dns_name)
        for zone in zones:
            zones_response.append(zone.to_response())
        return zones_response

    @api.expect(zone_post_parser)
    @api.marshal_with(zone_model)
    def post(self):
        """
        Creates a new DNS Zone to be managed by the server.
        """
        args = zone_post_parser.parse_args()

        zone_name = args.get("name")
        dns_name = dns.name.from_text(zone_name)

        zones = get_zones(current_app.config["ZONE_FILE_FOLDER"], dns_name)
        if len(zones) != 0:
            raise BadRequest("A zone with that name already exists.")

        # prepare required initial zone data
        primary_ns = args["primary_ns"]
        admin_email = friendly_email_to_zone_format(args["admin_email"])
        soa_record_data = {
            "mname": primary_ns,
            "rname": admin_email,
            "serial": 0,  # will be handled on zone write to disk
            "refresh": args["refresh"],
            "retry": args["retry"],
            "expire": args["expire"],
            "minimum": args["minimum"],
        }
        soa_rrset = create_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name="@",
            record_type="SOA",
            record_data=soa_record_data,
            record_ttl=args["soa_ttl"],
            write=False,
        )
        primary_ns_record_data = {
            "target": primary_ns,
        }
        primary_ns_rrset = create_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name="@",
            record_type="NS",
            record_data=primary_ns_record_data,
            record_ttl=args["primary_ns_ttl"],
            write=False,
        )

        make_primary_ns_a_record = args.get("primary_ns_ip") and args.get(
            "primary_ns_a_ttl"
        )
        if make_primary_ns_a_record:
            primary_ns_a_record_data = {"address": args["primary_ns_ip"]}
            primary_ns_a_rrset = create_record(
                zone_name=zone_name,
                zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
                record_name=f"{primary_ns}",
                record_type="A",
                record_data=primary_ns_a_record_data,
                record_ttl=args["primary_ns_a_ttl"],
                write=False,
            )
        else:
            primary_ns_a_rrset = None

        new_zone = create_zone(
            zone_name=dns_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            soa_rrset=soa_rrset,
            ns_rrset=primary_ns_rrset,
            ns_a_rrset=primary_ns_a_rrset,
        )

        return new_zone.to_response()


@api.route("/<string:zone_name>")
class SpecificDnsZone(Resource):
    @api.marshal_with(zone_model)
    def get(self, zone_name: str):
        """
        Gets an existing DNS Zone.
        """
        dns_name = dns.name.from_text(zone_name)

        zone = get_zones(
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"], zone_name=dns_name
        )[0]
        if not zone:
            raise NotFound("A zone with that name does not exist.")

        return zone.to_response()

    @api.marshal_with(zone_model)
    def put(self, zone_name: str):
        """
        Updates an existing DNS Zone.
        """
        args = zone_put_parser.parse_args()

        dns_name = dns.name.from_text(zone_name)

        zones = get_zones(
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"], zone_name=dns_name
        )
        if len(zones) != 1:
            raise BadRequest(
                "A zone with that name does not currently exist. Zone names are not currently mutable."
            )

        # update SOA record
        primary_ns = args["primary_ns"]
        admin_email = friendly_email_to_zone_format(args["admin_email"])
        soa_record_data = {
            "mname": primary_ns,
            "rname": admin_email,
            "serial": 0,  # will be handled on zone write to disk
            "refresh": args["refresh"],
            "retry": args["retry"],
            "expire": args["expire"],
            "minimum": args["minimum"],
        }
        _ = update_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name="@",
            record_type="SOA",
            record_data=soa_record_data,
            record_ttl=args["soa_ttl"],
            record_index=0,
        )

        update_zone = get_zones(
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"], zone_name=dns_name
        )
        update_zone_response = update_zone[0].to_response()
        return update_zone_response

    @api.marshal_with(zone_model)
    def delete(self, zone_name: str):
        """
        Deletes a DNS Zone.
        """
        dns_name = dns.name.from_text(zone_name)

        if delete_zone(
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"], zone_name=dns_name
        ):
            return {}
        raise NotFound("A zone with that name does not exist.")


@api.route("/transfer")
class DnsZoneInboundTransfer(Resource):
    @api.expect(zone_transfer_parser)
    @api.marshal_with(zone_model)
    def post(self):
        """
        Initiates a zone transfer (XFR) from an existing authoritative nameserver.
        """
        args = zone_transfer_parser.parse_args()
        zone_name_clean = str(dns.name.from_text(args["zone_name"]))

        kw_args = {}
        primary_ns_ip = args.get("primary_ns_ip")
        if primary_ns_ip:
            kw_args["nameserver_ip"] = primary_ns_ip
        primary_ns_port = int(args.get("primary_ns_port"))
        if primary_ns_port:
            kw_args["nameserver_port"] = primary_ns_port
        use_udp = args.get("use_udp")
        if use_udp:
            kw_args["use_udp"] = use_udp
        xfr_timeout = args.get("transfer_timeout")
        if xfr_timeout:
            kw_args["transfer_timeout"] = int(xfr_timeout)

        new_zone = zone_from_zone_transfer(
            zone_name=zone_name_clean,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            **kw_args,
        )
        return new_zone.to_response()
