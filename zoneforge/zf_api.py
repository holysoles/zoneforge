from flask import redirect, url_for, request
from flask_restx import Resource, reqparse
from dns.zone import Zone
from dns.name import Name
from dns.rdataclass import *
from dns.rdatatype import *
from dns.rrset import *
from zoneforge.zf import get_zones, create_zone, delete_zone, get_records, create_record, update_record, delete_record
from werkzeug.exceptions import *

# TODO for parsers: make a list of valid values
zone_parser = reqparse.RequestParser()
zone_parser.add_argument('browser', type=bool, help='Track if requests are coming from the web application', required=False) 
zone_parser.add_argument('zone_name', type=str, help='Type of DNS Record', required=False) 

record_parser = reqparse.RequestParser()
zone_parser.add_argument('browser', type=bool, help='Track if requests are coming from the web application', required=False) 
record_parser.add_argument('record_type', type=str, help='Type of DNS Record', required=False)
record_parser.add_argument('record_data', type=str, help='RData for the DNS Record', required=False)

class StatusResource(Resource):
    def get(self):
        return {'status': 'OK'}, 200
    
class ZoneResource(Resource):
    def get(self, zone_name: str = None):
        zones_response = []
        if zone_name:
            zone_name = dns.name.from_text(zone_name)
        zones = get_zones(zone_name)
        if not zones:
            raise NotFound('A zone with that name does not exist.')
        else:
            for zone in zones:
                print(f"DEBUG: transforming zone ${zone}")
                zones_response.append(transform_zone(zone))
        
        if zone_name:
            zones_response = zones_response[0] # return single element when zone_name was specified
        return zones_response
    
    def post(self, zone_name: str = None):
        zone_parser.add_argument('soa_ttl', type=str, help='SOA TTL', required=True) 
        zone_parser.add_argument('admin_email', type=str, help='Email address of zone admin', required=True) 
        zone_parser.add_argument('refresh', type=str, help='Record refresh frequency for secondary nameservers', required=True)
        zone_parser.add_argument('retry', type=str, help='Retry frequency for failed zone transfers', required=True) 
        zone_parser.add_argument('expire', type=str, help='Period after which the zone is discarded if no updates are received', required=True) 
        zone_parser.add_argument('minimum', type=str, help='Used for calculation of negative response TTL', required=True)
        zone_parser.add_argument('primary_ns', type=str, help='Primary nameserver for the zone', required=True) 
        zone_parser.add_argument('primary_ns_ttl', type=str, help="TTL for the primary nameserver's NS record", required=True)
        zone_parser.add_argument('primary_ns_ip', type=str, help="IP for the primary nameserver's A record", required=False)
        zone_parser.add_argument('primary_ns_a_ttl', type=str, help="TTL for the primary nameserver's A record", required=False) 
        args = zone_parser.parse_args()

        if not zone_name:
            zone_name = args.get("zone_name")
            if not zone_name:
                raise BadRequest("A zone name must be specified with either '/zone/[zone_name]' or with the 'zone_request' parameter")
        zone_name = dns.name.from_text(zone_name)
            
        zones = get_zones(zone_name)
        if len(zones) != 0:        
            raise BadRequest('A zone with that name already exists.')
        
        # prepare required initial zone data
        primary_ns = args['primary_ns']
        admin_email = args['admin_email'].replace('@', '.')
        soa_rrset = create_record(record_name="@", record_type="SOA", record_data=f"{primary_ns} {admin_email} 0 {args['refresh']} {args['retry']} {args['expire']} {args['minimum']}", record_ttl=args['soa_ttl'] , write=False)
        primary_ns_rrset = create_record(record_name='@', record_type='NS', record_data=f"{primary_ns}", record_ttl=args['primary_ns_ttl'], write=False)

        make_primary_ns_a_record = args.get('primary_ns_ip') and args.get('primary_ns_a_ttl')
        primary_ns_a_rrset = create_record(record_name=f"{primary_ns}", record_type='A', record_data=f"{args['primary_ns_ip']}", record_ttl=args['primary_ns_a_ttl'], write=False) if make_primary_ns_a_record else None

        new_zone = create_zone(zone_name, soa_rrset, primary_ns_rrset, primary_ns_a_rrset)
        new_zone_response = transform_zone(new_zone)

        if args.get('browser'):
            return redirect(url_for('home'))
        return new_zone_response
    
    def delete(self, zone_name: str = None):
        args = zone_parser.parse_args()
        if not zone_name:
            zone_name = args.get("zone_name")
            if not zone_name:
                raise BadRequest("A zone name must be specified with either '/zone/[zone_name]' or with the 'zone_request' parameter")
        zone_name = dns.name.from_text(zone_name)

        if delete_zone(zone_name):
            return {}
        else:
            raise NotFound('A zone with that name does not exist.')
        


class RecordResource(Resource):
    def get(self, zone_name, record_name=None):
        args = record_parser.parse_args()
        record_type = args.get('record_type')
        records = get_records(zone_name=zone_name, record_name=record_name, record_type=record_type)
        return_records = transform_records(records)

        if record_name and not return_records:
            raise NotFound
        return return_records
    
    def post(self, zone_name, record_name):
        args = record_parser.parse_args()
        record_type = args.get('record_type')
        record_data = args.get('record_data')
        new_record = create_record(record_name=record_name, record_type=record_type, record_data=record_data, zone_name=zone_name)
        new_record_response = transform_records(new_record)[0]
        return new_record_response
    
    def put(self, zone_name, record_name):
        args = record_parser.parse_args()
        record_type = args.get('record_type')
        record_data = args.get('record_data')
        updated_record = update_record(zone_name, record_name, record_type, record_data)
        updated_record = {record_name: updated_record}
        updated_record_response = transform_records(updated_record)[0]
        return updated_record_response
    
    def delete(self, zone_name, record_name):
        args = record_parser.parse_args()
        record_type = args.get('record_type')
        delete_record(zone_name, record_name, record_type)
        return {}

def transform_zone(zone: Zone) -> dict:
    return {
        "origin": str(zone.origin),
        "record_count": len(zone.nodes),
    }
    

def transform_records(records: RRset) -> dict:
    transformed_records = []
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
            if getattr(rdata, "rdcomment"):
                record["comment"] = rdata.rdcomment
            if record_type == SOA:
                record["data"]["expire"] = rdata.expire
                record["data"]["minimum"] = rdata.minimum
            elif record_type == MX:
                record["data"]["exchange"] = rdata.exchange.to_text()
            elif record_type == NS:
                record["data"]["target"] = rdata.target.to_text()  #TODO need to convert @s to origin name
            elif record_type == CNAME:
                record["data"]["target"] = rdata.target.to_text() #TODO need to convert @s to origin name
            elif record_type == A:
                record["data"]["address"] = rdata.address
            elif record_type == TXT:
                record["data"]["data"] = rdata.to_text()
            else:
                print(f"ERROR: DNS Record Type f{rrset.rdtype} not supported.")
                    
            transformed_records.append(record)
    return transformed_records