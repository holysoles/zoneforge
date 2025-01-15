# ZoneForge

ZoneForge is a management tool for [RFC1035](https://rfc-annotations.research.icann.org/rfc1035.html)/BIND style DNS zone files. 

![GitHub License](https://img.shields.io/github/license/holysoles/zoneforge)
![Issues](https://img.shields.io/github/issues/holysoles/zoneforge)

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

Read-Only currently.

## Records

Read only currently. Limited support for record types (A, CNAME, SOA, MX, NS, TXT).

- EOL comments are supported in the `comments` key of returned records.

## Roadmap

# Feature Roadmap

| **Feature**                             | **Status**         |
|-----------------------------------------|--------------------|
| **Web Interface**                       |                    |
|  Create Zones                          | Planned           |
|  Edit Records                          | Planned           |
|  Delete Records                        | Planned           |
|  Create Zones                          | Planned           |
|  Delete Zones                          | Planned           |
|  Multi-zone Support                    | Complete          |
| **REST API**                            |                    |
|  CRUD for DNS Zones                    | In Progress       |
|  CRUD for DNS Records                  | In Progress       |
| **Management**                          |                    |
|  Expanded Record Type Support          | Planned           |
|  Authentication                        | Backlog           |
|  Zone Import/Export                    | Backlog           |
| **CI/CD**                               |                    |
|  Dockerfile                            | Planned           |
|  GitHub Actions Build Pipeline         | Planned           |
|  Package for PyPi/pip                  | Backlog           |
|  Test Suite                            | Backlog           |
|  GitHub Actions Test Pipeline          | Backlog           |
|  CoreDNS Kubernetes Integration        | Backlog           |



# Resources

## Zone Files

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