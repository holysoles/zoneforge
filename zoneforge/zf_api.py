from flask_restful import Resource, reqparse
from dns.zone import Zone
from dns.name import Name
from dns.rdataclass import *
from dns.rdatatype import *
from zoneforge.zf import get_zones, get_records

#parser = reqparse.RequestParser()
#parser.add_argument('record_type', type=int, help='Type of DNS Record')

class StatusResource(Resource):
    def get(self):
        return {'status': 'OK'}, 200
    
class ZoneResource(Resource):
    def get(self, zone_name=None):
        zones_response = []
        try:
            zones = get_zones(zone_name)
            if not zones:
                return 404
            else:
                for zone in zones:
                    print(f"DEBUG: transforming zone ${zone}")
                    zones_response.append(transform_zone(zone))
        except:
            return 500
        
        if zone_name:
            zones_response = zones_response[0] # return single element when zone_name was specified
        return zones_response

class RecordResource(Resource):
    def get(self, zone_name, record_name=None):
        #args = parser.parse_args()
        #record_type = args.get('record_type')
        records = get_records(zone_name, record_name, record_type=None) #TODO unhardcode
        if record_name:
            records = {record_name: records}
        return_records = transform_records(records, zone_name)

        if record_name and not return_records:
            return "record not found", 404
        return return_records
    
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