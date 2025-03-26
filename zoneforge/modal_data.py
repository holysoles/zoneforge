ZONE_CREATE_PRIMARY_NS_OPTIONS = [
    {
        "id": "primary_ns",
        "label": "Name",
        "tooltip": "The name of the primary authoritative nameserver for the zone.",
        "placeholder": "ns1",
        "type": "text",
        "required": True,
    },
    {
        "id": "primary_ns_ttl",
        "label": "NS Record TTL",
        "tooltip": "The TTL of the primary authoritative nameserver's NS record for the zone.",
        "type": "number",
        "required": True,
    },
    {
        "id": "primary_ns_ip",
        "label": "IP",
        "tooltip": "The IP address of the primary authoritative nameserver for the zone. Necessary if the NS is within the zone.",
        "placeholder": "192.168.1.2",
        "type": "text",
        "required": False,
    },
    {
        "id": "primary_ns_a_ttl",
        "label": "A Record TTL",
        "tooltip": "The TTL of the primary authoritative nameserver's A record for the zone. Necessary if the NS is within the zone.",
        "type": "number",
        "required": False,
    },
]

ZONE_EDIT_PRIMARY_NS_OPTIONS = [
    {
        "id": "primary_ns",
        "label": "Name",
        "tooltip": "The name of the primary authoritative nameserver for the zone.",
        "placeholder": "ns1",
        "type": "text",
        "required": True,
    },
]

ZONE_CREATE_FORM = [
    {
        "heading": None,
        "inputs": [
            {
                "id": "name",
                "label": "Zone Name",
                "tooltip": "The domain to create a zone for. AKA origin.",
                "placeholder": "example.com",
                "type": "text",
                "required": True,
            },
        ],
    },
    {
        "heading": "SOA",
        "inputs": [
            {
                "id": "soa_ttl",
                "label": "TTL",
                "tooltip": "TTL specific to the SOA record.",
                "type": "number",
                "required": True,
            },
            {
                "id": "admin_email",
                "label": "Responsible Party Email",
                "tooltip": "The email address of the zone administrator.",
                "placeholder": "admin@example.com",
                "type": "email",
                "required": True,
            },
            {
                "id": "refresh",
                "label": "Refresh",
                "tooltip": "How often secondary nameservers should check for updates.",
                "type": "number",
                "required": True,
            },
            {
                "id": "retry",
                "label": "Retry",
                "tooltip": "How long secondary nameservers should wait before retrying a failed zone transfer.",
                "type": "number",
                "required": True,
            },
            {
                "id": "expire",
                "label": "Expire",
                "tooltip": "The time after which secondary nameservers discard the zone if no updates are received.",
                "type": "number",
                "required": True,
            },
            {
                "id": "minimum",
                "label": "Minimum",
                "tooltip": "Used to calculate negative response caching. Resolvers use the smaller of this value or the SOA TTL",
                "type": "number",
                "required": True,
            },
        ],
    },
    {"heading": "Primary Nameserver", "inputs": ZONE_CREATE_PRIMARY_NS_OPTIONS},
]

ZONE_CREATE_XFR_FORM = [
    {
        "heading": None,
        "inputs": [
            {
                "id": "zone_name",
                "label": "Zone Name",
                "tooltip": "The domain to initiate a zone transfer for. AKA origin.",
                "placeholder": "example.com",
                "type": "text",
                "required": True,
            },
            {
                "id": "use_udp",
                "label": "Use UDP?",
                "tooltip": "Whether or not the zone transfer should be attempted over UDP.",
                "placeholder": "example.com",
                "type": "checkbox",
                "required": False,
            },
        ],
    },
    {
        "heading": "Nameserver",
        "inputs": [
            {
                "id": "primary_ns_ip",
                "label": "Nameserver IP",
                "tooltip": "The IP of the nameserver to initiate the transfer from. By default, the primary NS from the zone's SOA record is used.",
                "placeholder": "1.1.1.1",
                "type": "text",
                "required": False,
            },
            {
                "id": "primary_ns_port",
                "label": "Nameserver Port",
                "tooltip": "The nameserver's port to connect to for the zone transfer. Defaults to 53.",
                "placeholder": "53",
                "type": "number",
                "required": False,
            },
        ],
    },
]

ZONE_EDIT_FORM = [
    {
        "heading": None,
        "inputs": [
            {
                "id": "name",
                "label": "Zone Name",
                "tooltip": "The domain that the zone manages. AKA origin.",
                "placeholder": "example.com",
                "type": "text",
                "required": True,
                "readonly": True,
            },
        ],
    },
    {
        "heading": "SOA",
        "inputs": [
            {
                "id": "soa_ttl",
                "label": "TTL",
                "tooltip": "TTL specific to the SOA record.",
                "type": "number",
                "required": True,
            },
            {
                "id": "admin_email",
                "label": "Responsible Party Email",
                "tooltip": "The email address of the zone administrator.",
                "placeholder": "admin@example.com",
                "type": "email",
                "required": True,
            },
            {
                "id": "refresh",
                "label": "Refresh",
                "tooltip": "How often secondary nameservers should check for updates.",
                "type": "number",
                "required": True,
            },
            {
                "id": "retry",
                "label": "Retry",
                "tooltip": "How long secondary nameservers should wait before retrying a failed zone transfer.",
                "type": "number",
                "required": True,
            },
            {
                "id": "expire",
                "label": "Expire",
                "tooltip": "The time after which secondary nameservers discard the zone if no updates are received.",
                "type": "number",
                "required": True,
            },
            {
                "id": "minimum",
                "label": "Minimum",
                "tooltip": "Used to calculate negative response caching. Resolvers use the smaller of this value or the SOA TTL",
                "type": "number",
                "required": True,
            },
        ],
    },
    {"heading": "Primary Nameserver", "inputs": ZONE_EDIT_PRIMARY_NS_OPTIONS},
]

ZONE_CREATION = {
    "heading": "Create New Zone",
    "id": "create-zone-modal",
    "api-method": "POST",
    "api-endpoint": "/api/zones",
    "open-char": "Create New Zone",
    "close-char": "&times;",
    "form": ZONE_CREATE_FORM,
}

ZONE_CREATION_XFR = {
    "heading": "Import via Zone Transfer",
    "id": "zone-from-xfr-modal",
    "api-method": "POST",
    "api-endpoint": "/api/zones/transfer",
    "open-char": "New Zone From Transfer",
    "close-char": "&times;",
    "form": ZONE_CREATE_XFR_FORM,
}

ZONE_EDIT = {
    "heading": "Edit Zone",
    "id": "edit-zone-modal",
    "api-method": "PUT",
    "api-endpoint": "/api/zones",
    "api-id": "name",
    "deleteable": True,
    "delete-redirect": "home",
    "open-char": "Edit",
    "close-char": "&times;",
    "form": ZONE_EDIT_FORM,
}

ZONE_DEFAULTS = {
    "name": None,
    "soa_ttl": 86400,
    "admin_email": None,
    "refresh": 86400,
    "retry": 7200,
    "expire": 3600000,
    "minimum": 172800,
}

ZONE_PRIMARY_NS_DEFAULTS = {
    "primary_ns": None,
    "primary_ns_ttl": 86400,
    "primary_ns_ip": None,
    "primary_ns_a_ttl": 86400,
}
