from flask_restx import Resource, Namespace, reqparse, fields
from flask import current_app
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from zoneforge.core import (
    get_records,
    create_record,
    update_record,
    delete_record,
    record_to_response,
)

api = Namespace("records", description="DNS record related operations", path="/")

record_get_parser = reqparse.RequestParser()
record_get_parser.add_argument(
    "name", type=str, help="Name of the DNS record", required=False
)
record_get_parser.add_argument(
    "type", type=str, help="Type of DNS Record", required=False
)

record_post_parser = record_get_parser.copy()
record_post_parser.replace_argument(
    "name", type=str, help="Name of the DNS record", required=True
)
record_post_parser.replace_argument(
    "type", type=str, help="Type of DNS Record", required=True
)
record_post_parser.add_argument(
    "ttl", type=str, help="TTL of the DNS record", required=False
)
record_post_parser.add_argument(
    "data", type=dict, help="RData for the DNS Record", required=True
)
record_post_parser.add_argument(
    "comment", type=str, help="Comment for the DNS Record", required=False
)

record_put_parser = record_get_parser.copy()
record_put_parser.replace_argument(
    "type", type=str, help="Type of DNS Record", required=True
)
record_put_parser.add_argument(
    "ttl", type=str, help="TTL of the DNS record", required=False
)
record_put_parser.add_argument(
    "data", type=dict, help="RData for the DNS Record", required=True
)
record_put_parser.add_argument(
    "comment", type=str, help="Comment for the DNS Record", required=False
)
record_put_parser.add_argument(
    "index",
    type=int,
    help="Index of the record within its name & type pair (Resource Record Set)",
    required=True,
)

record_delete_parser = record_get_parser.copy()
record_delete_parser.replace_argument(
    "type", type=str, help="Type of DNS Record", required=True
)
record_delete_parser.add_argument(
    "data", type=dict, help="RData of the DNS Record", required=True
)
record_delete_parser.add_argument(
    "index",
    type=int,
    help="Index of the record within its name & type pair (Resource Record Set)",
    required=True,
)

dns_fields_model = api.model("DnsRecordFields", {"*": fields.Wildcard(fields.Raw)})
dns_record_model = api.model(
    "DnsRecord",
    {
        "name": fields.String(example="www"),
        "type": fields.String(example="A"),
        "ttl": fields.Integer(example=86400),
        "comment": fields.String(example="A comment describing the record"),
        "data": fields.Nested(dns_fields_model, example={"address": "192.168.1.2"}),
        "index": fields.Integer(example=0),
    },
)


@api.route("/zones/<string:zone_name>/records")
class DnsRecord(Resource):
    @api.expect(record_get_parser)
    @api.marshal_with(dns_record_model, as_list=True)
    def get(self, zone_name: str):
        """
        Gets a list of all records in the zone.
        Optionally, get a record list filtered by the record's 'name' and/or its 'type'.
        By default, SOA records are excluded and are treated as part of the zone data. SOA records can be retrieved explicitly with 'type=SOA'.
        """
        args = record_get_parser.parse_args()
        record_name = args.get("name")
        record_type = args.get("type")
        include_soa = record_type == "SOA"

        records = get_records(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name=record_name,
            record_type=record_type,
            include_soa=include_soa,
        )
        records_response = record_to_response(records=records)

        return records_response

    @api.expect(record_post_parser)
    @api.marshal_with(dns_record_model)
    def post(self, zone_name: str):
        """
        Creates a new DNS record in the specified zone.
        """
        args = record_post_parser.parse_args()
        new_record = create_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name=args["name"],
            record_type=args["type"],
            record_ttl=args["ttl"],
            record_data=args["data"],
            record_comment=args["comment"],
        )
        new_record_response = record_to_response(new_record)[0]
        return new_record_response


@api.route("/zones/<string:zone_name>/records/<string:record_name>")
class SpecificDnsRecord(Resource):
    @api.expect(record_get_parser)
    @api.marshal_with(dns_record_model, as_list=True)
    def get(self, zone_name: str, record_name: str):
        """
        Gets a list of all records in the zone under the specified name.
        Optionally may also be filtered by record type.
        By default, SOA records are excluded and are treated as part of the zone data. SOA records can be retrieved explicitly with 'type=SOA'.
        """
        args = record_get_parser.parse_args()

        record_type = args.get("type")
        include_soa = record_type == "SOA"

        records = get_records(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name=record_name,
            record_type=record_type,
            include_soa=include_soa,
        )
        records_response = record_to_response(records=records)

        if not records:
            raise NotFound
        return records_response

    @api.expect(record_put_parser)
    @api.marshal_with(dns_record_model)
    def put(self, zone_name: str, record_name: str):
        """
        Updates an existing DNS record in the specified zone.
        """
        args = record_put_parser.parse_args()
        record_ttl = args.get("ttl")
        if record_ttl is None:
            record_ttl = current_app.config["DEFAULT_ZONE_TTL"]
        updated_record = update_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name=record_name,
            record_type=args["type"],
            record_ttl=record_ttl,
            record_data=args["data"],
            record_comment=args["comment"],
            record_index=args["index"],
        )
        updated_record_response = record_to_response(updated_record)[0]
        return updated_record_response

    @api.expect(record_delete_parser)
    def delete(self, zone_name, record_name: str):
        """
        Deletes a DNS record in the specified zone.
        """
        args = record_delete_parser.parse_args()
        delete_record(
            zone_name=zone_name,
            zonefile_folder=current_app.config["ZONE_FILE_FOLDER"],
            record_name=record_name,
            record_type=args["type"],
            record_data=args["data"],
            record_index=args["index"],
        )
        return {}
