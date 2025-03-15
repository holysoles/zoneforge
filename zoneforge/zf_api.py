from flask_restx import Resource, reqparse
from flask import request
from zoneforge.zf import get_zones, create_zone, delete_zone, get_records, create_record, update_record, delete_record, record_to_response, get_record_types_map, friendly_email_to_zone_format
from werkzeug.exceptions import *
import dns.name

zone_parser = reqparse.RequestParser()
zone_parser.add_argument('name', type=str, help='Name of the DNS Zone', required=False) 

record_parser = reqparse.RequestParser()
record_parser.add_argument('name', type=str, help='Name of the DNS record', required=False)
record_parser.add_argument('ttl', type=str, help='TTL of the DNS record', required=False)
record_parser.add_argument('type', type=str, help='Type of DNS Record', required=False)
record_parser.add_argument('data', type=dict, help='RData of the DNS Record', required=False)

class StatusResource(Resource):
    def get(self):
        return {'status': 'OK'}, 200
    
class ZoneResource(Resource):
    def get(self, zone_name: str = None):
        zones_response = []
        if not zone_name:
            args = zone_parser.parse_args()
            zone_name = args.get("name")

        if zone_name:
            dns_name = dns.name.from_text(zone_name)
        else:
            dns_name = None
        zones = get_zones(dns_name)
        if not zones and zone_name:
            raise NotFound('A zone with that name does not exist.')
        else:
            for zone in zones:
                zones_response.append(zone.to_response())
        
        if zone_name:
            zones_response = zones_response[0] # return single element when name was specified
        return zones_response
    
    def post(self, zone_name: str = None):
        parser = zone_parser.copy()
        parser.add_argument('soa_ttl', type=str, help='SOA TTL', required=True) 
        parser.add_argument('admin_email', type=str, help='Email address of zone admin', required=True) 
        parser.add_argument('refresh', type=str, help='Record refresh frequency for secondary nameservers', required=True)
        parser.add_argument('retry', type=str, help='Retry frequency for failed zone transfers', required=True) 
        parser.add_argument('expire', type=str, help='Period after which the zone is discarded if no updates are received', required=True) 
        parser.add_argument('minimum', type=str, help='Used for calculation of negative response TTL', required=True)
        parser.add_argument('primary_ns', type=str, help='Primary nameserver for the zone', required=True) 
        parser.add_argument('primary_ns_ttl', type=str, help="TTL for the primary nameserver's NS record", required=True)
        parser.add_argument('primary_ns_ip', type=str, help="IP for the primary nameserver's A record", required=False)
        parser.add_argument('primary_ns_a_ttl', type=str, help="TTL for the primary nameserver's A record", required=False) 
        args = parser.parse_args()

        if not zone_name:
            zone_name = args.get("name")
            if not zone_name:
                raise BadRequest("A zone name must be specified with either a URL path of '/zone/[zone_name]' or with the 'name' parameter")
        dns_name = dns.name.from_text(zone_name)
            
        zones = get_zones(dns_name)
        if len(zones) != 0:        
            raise BadRequest('A zone with that name already exists.')
        
        # prepare required initial zone data
        primary_ns = args['primary_ns']
        admin_email = friendly_email_to_zone_format(args['admin_email'])
        soa_record_data = {
            "mname": primary_ns,
            "rname": admin_email,
            "serial": 0, # will be handled on zone write to disk
            "refresh": args['refresh'],
            "retry": args['retry'],
            "expire": args['expire'],
            "minimum": args['minimum']
        }
        soa_rrset = create_record(zone_name=zone_name, record_name="@", record_type="SOA", record_data=soa_record_data, record_ttl=args['soa_ttl'] , write=False)
        primary_ns_record_data = {
            "target": primary_ns,
        }
        primary_ns_rrset = create_record(zone_name=zone_name, record_name='@', record_type='NS', record_data=primary_ns_record_data, record_ttl=args['primary_ns_ttl'], write=False)

        make_primary_ns_a_record = args.get('primary_ns_ip') and args.get('primary_ns_a_ttl')
        if make_primary_ns_a_record:
            primary_ns_a_record_data = {
                "address": args['primary_ns_ip']
            }
            primary_ns_a_rrset = create_record(zone_name=zone_name, record_name=f"{primary_ns}", record_type='A', record_data=primary_ns_a_record_data, record_ttl=args['primary_ns_a_ttl'], write=False)
        else:
            primary_ns_a_rrset = None

        new_zone = create_zone(dns_name, soa_rrset, primary_ns_rrset, primary_ns_a_rrset)
        new_zone_response = new_zone.to_response()

        return new_zone_response
    
    def put(self, zone_name: str = None):
        parser = zone_parser.copy()
        parser.add_argument('soa_ttl', type=str, help='SOA TTL', required=True) 
        parser.add_argument('admin_email', type=str, help='Email address of zone admin', required=True) 
        parser.add_argument('refresh', type=str, help='Record refresh frequency for secondary nameservers', required=True)
        parser.add_argument('retry', type=str, help='Retry frequency for failed zone transfers', required=True) 
        parser.add_argument('expire', type=str, help='Period after which the zone is discarded if no updates are received', required=True) 
        parser.add_argument('minimum', type=str, help='Used for calculation of negative response TTL', required=True)
        parser.add_argument('primary_ns', type=str, help='Primary nameserver for the zone', required=True)
        args = parser.parse_args()

        if not zone_name:
            zone_name = args.get("name")
            if not zone_name:
                raise BadRequest("A zone name must be specified with either a URL path of '/zone/[zone_name]' or with the 'name' parameter")
        dns_name = dns.name.from_text(zone_name)

        zones = get_zones(dns_name)
        if len(zones) != 1:        
            raise BadRequest('A zone with that name does not currently exist. Zone names are not currently mutable.')
        
        # update SOA record
        primary_ns = args['primary_ns']
        admin_email = friendly_email_to_zone_format(args['admin_email'])
        soa_record_data = {
            "mname": primary_ns,
            "rname": admin_email,
            "serial": 0, # will be handled on zone write to disk
            "refresh": args['refresh'],
            "retry": args['retry'],
            "expire": args['expire'],
            "minimum": args['minimum']
        }
        _ = update_record(zone_name=zone_name, record_name="@", record_type="SOA", record_data=soa_record_data, record_ttl=args['soa_ttl'])

        update_zone = get_zones(dns_name)
        update_zone_response = update_zone[0].to_response()
        return update_zone_response

    
    def delete(self, zone_name: str = None):
        args = zone_parser.parse_args()
        if not zone_name:
            zone_name = args.get("name")
            if not zone_name:
                raise BadRequest("A zone name must be specified with either a URL path of '/zone/[zone_name]' or with the 'name' parameter")
        dns_name = dns.name.from_text(zone_name)

        if delete_zone(dns_name):
            return {}
        else:
            raise NotFound('A zone with that name does not exist.')

class RecordResource(Resource):
    def get(self, zone_name: str, record_name: str = None, record_type: str = None):
        args = record_parser.parse_args()
        if not record_name:
            record_name = args.get("name")

        if not record_type:
            record_type = args.get('type')
        # Only include SOA if specifically requested. We treat this as part of zone data normally
        include_soa = record_type == 'SOA'
        
        records = get_records(
            zone_name=zone_name, 
            record_name=record_name, 
            record_type=record_type,
            include_soa=include_soa
        )
        records_response = record_to_response(records=records)

        if record_name and not records:
            raise NotFound
        return records_response
    
    def post(self, zone_name: str, record_name: str = None):
        parser = record_parser.copy()
        parser.replace_argument('type', type=str, help='Type of DNS Record', required=True)
        parser.add_argument('data', type=dict, help='RData for the DNS Record', required=True)
        parser.add_argument('comment', type=str, help='Comment for the DNS Record', required=False)
        args = parser.parse_args()
        if not record_name:
            record_name = args.get("name")
            if not record_name:
                raise BadRequest("A record name must be specified with either a URL path of '/zone/[zone_name]/record[record_name]' or with the 'name' parameter")
        record_ttl = args.get('ttl')
        new_record = create_record(zone_name=zone_name, record_name=record_name, record_type=args['type'], record_ttl=record_ttl, record_data=args['data'], record_comment=args['comment'])
        new_record_response = record_to_response(new_record)[0]
        return new_record_response
    
    def put(self, zone_name: str, record_name: str = None):
        parser = record_parser.copy()
        parser.replace_argument('type', type=str, help='Type of DNS Record', required=True)
        parser.add_argument('data', type=dict, help='RData for the DNS Record', required=True)
        parser.add_argument('comment', type=str, help='Comment for the DNS Record', required=False)
        args = parser.parse_args()
        if not record_name:
            record_name = args.get("name")
            if not record_name:
                raise BadRequest("A record name must be specified with either a URL path of '/zone/[zone_name]/record[record_name]' or with the 'name' parameter")
        record_ttl = args.get('ttl')
        updated_record = update_record(zone_name=zone_name, record_name=record_name, record_type=args['type'], record_ttl=record_ttl, record_data=args['data'], record_comment=args['comment'])
        updated_record_response = record_to_response(updated_record)[0]
        return updated_record_response
    
    def delete(self, zone_name, record_name: str = None):
        parser = record_parser.copy()
        parser.replace_argument('type', type=str, help='Type of DNS Record', required=True)
        parser.replace_argument('data', type=dict, help='RData of the DNS Record', required=True)
        parser.replace_argument('ttl', type=str, help='TTL of the DNS Record', required=True)
        args = parser.parse_args()
        if not record_name:
            record_name = args.get("name")
            if not record_name:
                raise BadRequest("A record name must be specified with either a URL path of '/zone/[zone_name]/record[record_name]' or with the 'name' parameter")
        delete_record(zone_name=zone_name, record_name=record_name, record_type=args['type'], record_data=args['data'], record_ttl=args['ttl'])
        return {}

class RecordTypeResource(Resource):
    def get(self, record_type: str = None):
        record_types = get_record_types_map(record_type)
        return record_types
