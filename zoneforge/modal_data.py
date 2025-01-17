ZONE_CREATION = {
    "heading": "Create New Zone",
    "id": "add-zone-modal",
    "api-method": "POST",
    "open-char": "+",
    "close-char": "&times;",
    "form": [
        {
            "heading": None,
            "inputs": [
                {
                    "id": "zone_name",
                    "label": "Zone Name",
                    "tooltip": "The domain to create a zone for. AKA origin.",
                    "placeholder": "example.com",
                    "type": "text",
                    "default": None,
                    "required": True,
                },
               # {
                #    "id": "zone_ttl",
                #    "label": "TTL",
                #    "tooltip": "The default TTL for records in the zone.",
                #    "type": "number",
                #    "default": 86400,
                #    "required": True,
                #},
            ]
        },
        {
            "heading": "SOA",
            "inputs": [
                {
                    "id": "soa_ttl",
                    "label": "TTL",
                    "tooltip": "TTL specific to the SOA record.",
                    "type": "number",
                    "default": 86400,
                    "required": True,
                },
                {
                    "id": "admin_email",
                    "label": "Responsible Party Email",
                    "tooltip": "The email address of the zone administrator.",
                    "placeholder": "admin@example.com",
                    "type": "email",
                    "default": None,
                    "required": True,
                },
                {
                    "id": "refresh",
                    "label": "Refresh",
                    "tooltip": "How often secondary nameservers should check for updates.",
                    "type": "number",
                    "default": 86400,
                    "required": True,
                },
                {
                    "id": "retry",
                    "label": "Retry",
                    "tooltip": "How long secondary nameservers should wait before retrying a failed zone transfer.",
                    "type": "number",
                    "default": 7200,
                    "required": True,
                },
                {
                    "id": "expire",
                    "label": "Expire",
                    "tooltip": "The time after which secondary nameservers discard the zone if no updates are received.",
                    "type": "number",
                    "default": 3600000,
                    "required": True,
                },
                    {
                    "id": "minimum",
                    "label": "Minimum",
                    "tooltip": "Used to calculate negative response caching. Resolvers use the smaller of this value or the SOA TTL",
                    "type": "number",
                    "default": 172800,
                    "required": True,
                },
            ]
        },
        {
            "heading": "Primary Nameserver",
            "inputs": [
                {
                    "id": "primary_ns",
                    "label": "Name",
                    "tooltip": "The name of the primary authoritative nameserver for the zone.",
                    "placeholder": "ns1",
                    "type": "text",
                    "default": None,
                    "required": True,
                },
                {
                    "id": "primary_ns_ttl",
                    "label": "NS Record TTL",
                    "tooltip": "The TTL of the primary authoritative nameserver's NS record for the zone.",
                    "type": "number",
                    "default": 86400,
                    "required": True,
                },
                {
                    "id": "primary_ns_ip",
                    "label": "IP",
                    "tooltip": "The IP address of the primary authoritative nameserver for the zone. Necessary if the NS is within the zone.",
                    "placeholder": "192.168.1.2",
                    "type": "text",
                    "default": None,
                    "required": False,
                },
                {
                    "id": "primary_ns_a_ttl",
                    "label": "A Record TTL",
                    "tooltip": "The TTL of the primary authoritative nameserver's A record for the zone. Necessary if the NS is within the zone.",
                    "type": "number",
                    "default": 86400,
                    "required": False,
                },
            ],
        },
    ]
}
