# 11 — Security & SSRF Protection Architecture

## 1. Threat Model & Attack Vectors

Webhook infrastructure platforms are inherently vulnerable to **Server-Side Request Forgery (SSRF)** because users are allowed to configure external target URLs that backend workers will connect to via HTTP.

### Blocked Target Ranges & Protocols:
HookSentry rejects any endpoint URL attempting to target:
- **Loopback Addresses**: `127.0.0.0/8`, `::1`
- **Private RFC 1918 Networks**: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Link-Local & Cloud Metadata Endpoints**: `169.254.0.0/16` (including `169.254.169.254` AWS/GCP/Azure/OpenStack metadata)
- **Carrier-Grade NAT (CGNAT)**: `100.64.0.0/10`
- **Unique Local IPv6**: `fc00::/7`, `fe80::/10`
- **Unsafe Protocols**: `ftp://`, `file://`, `gopher://`, `dict://`
- **Internal Hostname Aliases**: `localhost`, `*.internal`, `*.local`, `metadata.google.internal`

---

## 2. DNS Resolution & Rebinding Defense

Naive regex URL validation does not prevent SSRF because an attacker can register an external domain (e.g. `rebind.evil.com`) whose DNS record dynamically resolves to `169.254.169.254` or `127.0.0.1`.

HookSentry performs socket-level validation:
```python
addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
for entry in addr_info:
    ip_str = entry[4][0]
    ip_obj = ipaddress.ip_address(ip_str)
    if is_ip_blocked(ip_obj):
        raise SSRFProtectionError(f"Destination IP '{ip_str}' is restricted.")
```

### Redirect SSRF Prevention:
Attackers can attempt to bypass initial URL validation by returning an HTTP 301/302 redirect pointing to `http://169.254.169.254`. HookSentry explicitly sets `allow_redirects=False` in requests dispatch, preventing automatic redirect traversal.

---

## 3. Data Protection & Encryption at Rest
- **Fernet Symmetric Encryption**: Endpoint secrets are encrypted at rest using a 256-bit AES key in CBC mode with HMAC-SHA256 authentication.
- **Log Sanitization**: Delivery attempt headers are sanitized prior to saving in PostgreSQL. The cryptographic signature is masked (`sha256=a1b2••••••••`), and authorization tokens are stripped.
- **Constant-Time Verification**: All signature and token comparisons employ `hmac.compare_digest()` or `secrets.compare_digest()` to defeat timing attacks.
