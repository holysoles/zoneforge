import dns.zone
from dns.exception import DNSException
from os import listdir
from os.path import join

# TODO get this declared in app.py, support it as a env var and arg
ZONE_FILE_FOLDER = './lib/examples'

def get_zones(zone_name=None) -> list[dns.zone.Zone]:
    zone_files = []
    zones = []
    domain = None
    if zone_name:
        domain = zone_name
        print("Getting zone object for domain", domain)
        zone_files = [f"{domain}zone"]
    else:
        zone_files = listdir(ZONE_FILE_FOLDER)

    for zone_file in zone_files:
        zone_file_path = join(ZONE_FILE_FOLDER, zone_file)
        try:
            zone = dns.zone.from_file(zone_file_path, domain)
            zones.append(zone)
        except DNSException as e:
            print (e.__class__, e)
            # TODO err handle
        except Exception as e:
            print (e)
            # TODO err handle
    return zones

def get_records(zone_name, record_name=None, record_type=None) -> dns.name.Name:
    # TODO support filtering on record_type
    zone = get_zones(zone_name)
    if not zone:
        print("no zone found")
        # TODO what if no zone?
    zone = zone[0]
    if record_name:
        return zone[record_name]
    else:
        return zone.nodes