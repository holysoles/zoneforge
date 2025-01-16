from flask_restx import Resource, reqparse
from dns.zone import Zone
from dns.name import Name
from dns.rdataclass import *
from dns.rdatatype import *
from zoneforge.zf import get_zones, create_zone, delete_zone, get_records, create_record, update_record, delete_record
from werkzeug.exceptions import *

parser = reqparse.RequestParser()
parser.add_argument('record_type', type=str, help='Type of DNS Record', required=False) # TODO make a list of valid values
parser.add_argument('record_data', type=str, help='RData for the DNS Record', required=False) #TODO custom type

class StatusResource(Resource):
    def get(self):
        return {'status': 'OK'}, 200
    
class ZoneResource(Resource):
    def get(self, zone_name=None):
        zones_response = []
        zones = get_zones(zone_name)
        if not zones:
            raise NotFound('')
        else:
            for zone in zones:
                print(f"DEBUG: transforming zone ${zone}")
                zones_response.append(transform_zone(zone))
        
        if zone_name:
            zones_response = zones_response[0] # return single element when zone_name was specified
        return zones_response
    
    def post(self, zone_name):
        new_zone = create_zone(zone_name)
        new_zone_response = transform_zone(new_zone)
        return new_zone_response
    
    def delete(self, zone_name):
        if delete_zone(zone_name):
            return {}
        else:
            raise NotFound('A zone with that name does not exist.')
        


class RecordResource(Resource):
    def get(self, zone_name, record_name=None):
        args = parser.parse_args()
        record_type = args.get('record_type')
        records = get_records(zone_name, record_name, record_type) #TODO unhardcode
        if record_name:
            records = {record_name: records}
        return_records = transform_records(records)

        if record_name and not return_records:
            raise NotFound
        return return_records
    
    def post(self, zone_name, record_name):
        args = parser.parse_args()
        record_type = args.get('record_type')
        record_data = args.get('record_data')
        new_record = create_record(zone_name, record_name, record_type, record_data)
        new_record = {record_name: new_record}
        new_record_response = transform_records(new_record)[0]
        return new_record_response
    
    def put(self, zone_name, record_name):
        args = parser.parse_args()
        record_type = args.get('record_type')
        record_data = args.get('record_data')
        updated_record = update_record(zone_name, record_name, record_type, record_data)
        updated_record = {record_name: updated_record}
        updated_record_response = transform_records(updated_record)[0]
        return updated_record_response
    
    def delete(self, zone_name, record_name):
        args = parser.parse_args()
        record_type = args.get('record_type')
        record_data = args.get('record_data')
        delete_record(zone_name, record_name, record_type)
        return {}

def transform_zone(zone: Zone) -> dict:
    return {
        "origin": str(zone.origin),
        "record_count": len(zone.nodes),
    }
    

def transform_records(names) -> dict:
    transformed_records = []
    for name, node in names.items():
        print(f"DEBUG: transforming records under name {name}")
        for rdataset in node.rdatasets:
            for rdata in rdataset:
                record_type = rdataset.rdtype
                record = {
                            "name": str(name),
                            "type": record_type._name_,
                            "ttl": rdataset.ttl,
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
                    print(f"ERROR: DNS Record Type f{rdataset.rdtype} not supported.")
                        
                transformed_records.append(record)
    return transformed_records