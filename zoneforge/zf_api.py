from flask_restful import Resource, reqparse
from dns.zone import Zone
from dns.name import Name
from dns.rdataclass import *
from dns.rdatatype import *
from zoneforge.zf import get_zones, create_zone, delete_zone, get_records
from zoneforge.exceptions import *

#parser = reqparse.RequestParser()
#parser.add_argument('record_type', type=int, help='Type of DNS Record')

class ZFErrors():
    dict = {
        'ZoneNotFoundError': {
            'message': "A zone with that name does not exist.",
            'status': 404,
        },
        'ZoneAlreadyExists': {
            'message': "A zone with that name already exists.",
            'status': 403,
        },
        'RecordNotFoundError': {
            'message': "A record with that name does not exist.",
            'status': 404,  
        },
    }

class StatusResource(Resource):
    def get(self):
        return {'status': 'OK'}, 200
    
class ZoneResource(Resource):
    def get(self, zone_name=None):
        zones_response = []
        zones = get_zones(zone_name)
        if not zones:
            raise ZoneNotFoundError
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
            raise ZoneNotFoundError
        


class RecordResource(Resource):
    def get(self, zone_name, record_name=None):
        #args = parser.parse_args()
        #record_type = args.get('record_type')
        records = get_records(zone_name, record_name, record_type=None) #TODO unhardcode
        if record_name:
            records = {record_name: records}
        return_records = transform_records(records, zone_name)

        if record_name and not return_records:
            raise NotFound
        return return_records
    
    def post(self, zone_name):
        print()
    
    def put(self, zone_name):
        print()

    def patch(self, zone_name):
        print()
    
    def delete(self, zone_name):
        if False:
            return {}
        else:
            raise RecordNotFoundError

def transform_zone(zone: Zone) -> dict:
    return {
        "origin": str(zone.origin),
        "record_count": len(zone.nodes),
    }
    

def transform_records(names, zone_name) -> dict:
    transformed_records = []
    for name, node in names.items():
        print(f"DEBUG: transforming records under name {name}")
        for rdataset in node.rdatasets:
            for rdata in rdataset:
                record_type = rdataset.rdtype
                record = {
                            "name": str(name),
                            "type": record_type._name_,
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