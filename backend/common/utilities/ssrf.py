import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional, Tuple
from django.conf import settings
from common.exceptions import SSRFProtectionError

BLOCKED_NETWORKS = [
    # IPv4 loopback & private
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network('100.64.0.0/10'),    # Carrier-grade NAT
    ipaddress.ip_network('192.0.0.0/24'),
    ipaddress.ip_network('192.0.2.0/24'),     # TEST-NET-1
    ipaddress.ip_network('198.51.100.0/24'),  # TEST-NET-2
    ipaddress.ip_network('203.0.113.0/24'),   # TEST-NET-3
    ipaddress.ip_network('224.0.0.0/4'),      # Multicast
    ipaddress.ip_network('240.0.0.0/4'),      # Reserved
    ipaddress.ip_network('0.0.0.0/8'),
    # IPv6 loopback & private
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fe80::/10'),        # Link-local
    ipaddress.ip_network('fc00::/7'),         # Unique local
    ipaddress.ip_network('::/128'),
]

FORBIDDEN_HOSTNAMES = {
    'localhost',
    'metadata.google.internal',
    '169.254.169.254',
    'instance-data',
}

def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to any blocked private, loopback, or link-local range."""
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        return True
    for net in BLOCKED_NETWORKS:
        if ip in net:
            return True
    return False

def validate_destination_url(url: str, allow_private_for_tests: bool = False) -> Tuple[str, str]:
    """
    Validate that destination_url is safe from SSRF attacks.
    Returns (validated_url, resolved_ip).
    Raises SSRFProtectionError if unsafe.
    """
    if not url:
        raise SSRFProtectionError("Destination URL cannot be empty.")

    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFProtectionError(f"Malformed URL: {exc}")

    if parsed.scheme.lower() not in ('http', 'https'):
        raise SSRFProtectionError(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    # In production mode, require HTTPS
    if not settings.DEBUG and parsed.scheme.lower() != 'https':
        raise SSRFProtectionError("Production webhook endpoints must use the HTTPS scheme.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFProtectionError("Destination URL missing hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in FORBIDDEN_HOSTNAMES or hostname_lower.endswith('.internal') or hostname_lower.endswith('.local'):
        if not (allow_private_for_tests or (settings.DEBUG and hostname_lower == 'localhost')):
            raise SSRFProtectionError(f"Destination hostname '{hostname}' is forbidden.")

    # Resolve IP addresses for hostname
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == 'https' else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        if allow_private_for_tests:
            # In isolated test environments without external DNS resolution
            return url, '203.0.113.1'
        raise SSRFProtectionError(f"DNS resolution failure for host '{hostname}': {exc}")

    if not addr_info:
        raise SSRFProtectionError(f"No IP addresses resolved for host '{hostname}'.")

    resolved_ip = None
    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFProtectionError(f"Invalid resolved IP '{ip_str}'.")

        if is_ip_blocked(ip_obj):
            if not allow_private_for_tests:
                raise SSRFProtectionError(f"Destination IP '{ip_str}' resolved from '{hostname}' is private/restricted.")

        if resolved_ip is None:
            resolved_ip = ip_str

    return url, resolved_ip
