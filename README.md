# ZoneForge

ZoneForge is a management tool for [RFC1035](https://rfc-annotations.research.icann.org/rfc1035.html)/BIND style DNS zone files. 

![GitHub License](https://img.shields.io/github/license/holysoles/zoneforge)
![Issues](https://img.shields.io/github/issues/holysoles/zoneforge)

> [!WARNING]  
> This is in early development and should be considered unstable until the first official release.

## About

Zone files are a commonly supported standard for serving [authoritative DNS](https://en.wikipedia.org/wiki/Name_server#Authoritative_name_server) zone records, such as in [BIND](https://www.isc.org/bind/), [NSD](https://github.com/NLnetLabs/nsd), and [CoreDNS's file plugin](https://coredns.io/plugins/file/). While those DNS server implementations are highly performant and lightweight, they don't provide a user-friendly way to manage their zone's records.

ZoneForge simplifies the *management* of RFC1035/BIND-style DNS zone files by providing an intuitive web-based interface and REST API, instead of re-inventing an entire DNS server. This project is ideal for administrators who require:
- A centralized, user-friendly tool to manage DNS records.
- Robust REST API.
- Deployment flexibility for various environments.

## Table of Contents
- [About](#About)
- [Features](#Features)
- [Usage](#Usage)
- [Resources](#Resources)
- [Credits](#Credits)

# Features

## Zones

### Create

```shell
curl -X POST 'http://localhost:5000/api/zone/example.com.' \
--header 'Content-Type: application/json' \
--data '{
    "soa_ttl": "3600",
    "admin_email": "admin@example.com",
    "refresh": "7200",
    "retry": "3600",
    "expire": "1209600",
    "minimum": "3600",
    "primary_ns": "ns1.example.com",
    "primary_ns_ttl": "3600",
    "primary_ns_ip": "192.0.2.1",
    "primary_ns_a_ttl": "3600"
}'
```

### Read

#### Get all zones
```shell
curl -X GET 'http://localhost:5000/api/zone'
```

#### Get specific zone
```shell
curl -X GET 'http://localhost:5000/api/zone/example.com.'
```

### Delete

```shell
curl -X DELETE 'http://localhost:5000/api/zone/example.com.'
```

## Records

- Limited support for record types (A, CNAME, SOA, MX, NS, TXT).
- EOL comments are supported in the `comment` parameter in record related requests.

### Create

```shell
curl -X POST 'http://localhost:5000/api/zone/example.com./record/subdomain' \
--header 'Content-Type: application/json' \
--data '{
    "type": "CNAME",
    "data": "ns100.example.com",
    "comment": "Optional comment"
}'
```

### Read

```shell
curl -X GET 'http://localhost:5000/api/zone/example.com./record/subdomain'
```

### Update

```shell
curl -X PUT 'http://localhost:5000/api/zone/example.com./record/subdomain' \
--header 'Content-Type: application/json' \
--data '{
    "type": "CNAME",
    "data": "subdomain2.example.com"
}'
```

### Delete

```shell
curl -X DELETE 'http://localhost:5000/api/zone/example.com./record/subdomain' \
--header 'Content-Type: application/json' \
--data '{
    "type": "CNAME",
    "data": "subdomain2.example.com"
}'
```

## Roadmap

# Feature Roadmap

| **Feature**                             | **Status**         |
|-----------------------------------------|--------------------|
| **Web Interface**                       |                    |
|  Create Zones                          | Complete          |
|  Delete Zones                          | Planned           |
|  Edit Zones                            | Planned           |
|  Edit Records                          | Complete          |
|  Create Records                        | Complete          |
|  Delete Records                        | Complete          |
|  Multi-zone Support                    | Complete          |
|  Client side validation                | Planned           |
| **REST API**                            |                    |
|  CRUD for DNS Zones                    | Complete          |
|  CRUD for DNS Records                  | Complete          |
|  Thread Safety for DNS Record CRUD     | Backlog           |
|  Zone Name Mutability                  | Backlog           |
|  Patch Method for DNS Zones            | Backlog           |
|  Patch Method for DNS Records          | Backlog           |
| **Management**                          |                    |
|  Expanded Record Type Support          | Planned           |
|  Authentication                        | Backlog           |
|  Zone Import/Export                    | Backlog           |
|  Preserve Default Zone TTL             | Backlog           |
| **CI/CD**                               |                    |
|  Dockerfile                            | Planned           |
|  GitHub Actions Build Pipeline         | Planned           |
|  Package for PyPi/pip                  | Backlog           |
|  Test Suite                            | Backlog           |
|  GitHub Actions Test Pipeline          | Backlog           |
|  CoreDNS Kubernetes Integration        | Backlog           |



# Resources

## Zone Files

- [Zone File Validator](https://checkzone.dev/) by @woodjme
- [DYN](https://help.dyn.com/how-to-format-a-zone-file/)
- [Oracle](https://docs.oracle.com/en-us/iaas/Content/DNS/Reference/formattingzonefile.htm)

## Migrating Existing DNS to a Zone File

For each domain that a given DNS server is authorative for:

1. First ensure that the zone is enabled for Zone transfer. For Windows DNS, this can be found by right-clicking the Zone -> Properties -> Zone Transfers.

2. Install `dig` on a unix-like system

3. Find the name servers if necessary: `dig example.com -t ns`

4. Initiate the Zone Transfer: `dig axfr example.com @dns.example.com | grep -E -v '^;' > db.example.com`

5. The file `db.example.com` should now contain a RFC1035-compatible zone file.


# Credits

Special thanks to the following projects for providing essential libraries:
- [dnspython](https://github.com/rthalley/dnspython)
- [Flask](https://github.com/pallets/flask)
